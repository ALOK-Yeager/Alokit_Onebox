"""Prompt-engineered EmailClassifier using sentiment backbone.

This classifier repurposes a sentiment analysis model (distilbert-base-uncased-finetuned-sst-2-english)
through light-weight prompt engineering and heuristic post-processing to categorize emails into
multi-domain classes such as Work, Personal, Promotional, Social, Notifications, Finance, Shopping,
Travel, and more.

Design Rationale
-----------------
A pure sentiment model outputs POSITIVE / NEGATIVE confidence. We transform this limited signal
into a multi-class categorization by:
1. Robust Email Preprocessing: Strip signatures, quoted replies, HTML artifacts, trackers.
2. Category-aware Prompt Framing: For each candidate category we build a natural-language hypothesis
   style prompt of the form:
       "This email is about <Category>. <Cleaned Content>"
   The intuition: A sentiment model fine-tuned on natural sentence classification can still produce
   relatively higher positive activation when the concatenated statement is semantically coherent.
3. Scoring Mechanism: For each category prompt we run the sentiment pipeline; we map the 'POSITIVE'
   probability to a pseudo-likelihood that the email matches the category. The original 'NEGATIVE'
   probability is treated as inverse support.
4. Normalization: Convert the positive scores across categories to a probability distribution via
   softmax (temperature adjustable) to encourage separation.
5. Fallback Logic: If top confidence < threshold (e.g., 0.40) or score margin between top-2 < delta
   (e.g., 0.05), emit "Uncertain" with secondary candidates for downstream refinement.
6. Email-specific Heuristics: Lightweight regex detectors influence priors (e.g., presence of
   currency amounts bumps Finance; unsubscribe links bump Promotional; flight references bump Travel).

Limitations
-----------
This is a heuristic adaptation; for production-grade multi-class accuracy a model fine-tuned on
multi-label email corpora is preferable. However this approach provides a zero-training bootstrap.

Usage Example
-------------
    from src.Services.ai.prompt_email_classifier import PromptEmailClassifier

    clf = PromptEmailClassifier()
    result = clf.classify("Subject: Your receipt\nThank you for your payment of $120.00 via Visa.")
    print(result)

Result Format:
    {
        'category': 'Finance',
        'confidence': 0.72,
        'scores': [ {'category': 'Finance', 'score': 0.72}, ... top-k ...],
        'fallback_used': False
    }
"""
from __future__ import annotations

import re
import html
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field

from transformers import pipeline
import math

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s'))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# -------------------------------- Data Structures -------------------------------- #

@dataclass
class ClassificationResult:
    category: str
    confidence: float
    scores: List[Dict[str, Any]]
    fallback_used: bool
    raw_top_category_score: float
    top_margin: float

# ------------------------------- Classifier Implementation ------------------------ #

class PromptEmailClassifier:
    """Prompt-engineered email classifier leveraging a sentiment model.

    Parameters:
        categories: Ordered list of target categories.
        model_name: Sentiment backbone model identifier.
        max_chars: Truncate cleaned email to this length for efficiency.
        temperature: Softmax temperature to control score sharpness.
        fallback_conf_threshold: Minimum confidence to accept top category.
        fallback_margin_threshold: Minimum (top - second) margin to avoid fallback.
        heuristic_prior_weight: Weight applied to heuristic prior adjustments.
    """

    DEFAULT_CATEGORIES: List[str] = [
        "Work", "Personal", "Promotional", "Social", "Notifications",
        "Finance", "Shopping", "Travel", "Support", "Security"
    ]

    SIGNATURE_MARKERS = [
        r"^-- ?$", r"^__+$", r"^Best regards", r"^Kind regards", r"^Sent from my",
        r"^Thanks,", r"^Cheers", r"^Sincerely"  # start-of-line signature cues
    ]

    QUOTE_HEADERS = [
        r"^On .* wrote:$", r"^From: .*", r"^Sent: .*", r"^>+"  # typical reply / forward patterns
    ]

    HTML_REMOVE = [
        (re.compile(r"<style[\s\S]*?</style>", re.IGNORECASE), " "),
        (re.compile(r"<script[\s\S]*?</script>", re.IGNORECASE), " "),
        (re.compile(r"<head[\s\S]*?</head>", re.IGNORECASE), " "),
        (re.compile(r"<[^>]+>"), " "),  # all tags
    ]

    URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
    MULTI_SPACE = re.compile(r"\s{2,}")

    # Heuristic regex features -> category influence mapping
    HEURISTIC_FEATURES: List[Tuple[re.Pattern, str, float]] = [
        (re.compile(r"\b(unsubscribe|opt out|newsletter)\b", re.I), "Promotional", 0.15),
        (re.compile(r"\b(invoice|payment|receipt|usd|eur|\$\d+|\d+\.\d{2})\b", re.I), "Finance", 0.18),
        (re.compile(r"\b(order|shipped|tracking number|delivery|cart)\b", re.I), "Shopping", 0.15),
        (re.compile(r"\b(flight|boarding pass|itinerary|airlines|hotel|booking)\b", re.I), "Travel", 0.17),
        (re.compile(r"\b(password|security alert|verify your account|suspicious)\b", re.I), "Security", 0.17),
        (re.compile(r"\b(meeting|deadline|project|quarterly|update)\b", re.I), "Work", 0.12),
        (re.compile(r"\b(friend request|liked your post|mentioned you)\b", re.I), "Social", 0.16),
        (re.compile(r"\b(notification|alert|reminder)\b", re.I), "Notifications", 0.14),
        (re.compile(r"\b(help desk|support ticket|issue id|troubleshoot)\b", re.I), "Support", 0.16),
    ]

    def __init__(
        self,
        categories: Optional[List[str]] = None,
        model_name: str = "distilbert-base-uncased-finetuned-sst-2-english",
        max_chars: int = 1200,
        temperature: float = 0.9,
        fallback_conf_threshold: float = 0.40,
        fallback_margin_threshold: float = 0.05,
        heuristic_prior_weight: float = 0.6,
        device: Optional[int] = None,
    ) -> None:
        self.categories = categories or self.DEFAULT_CATEGORIES
        self.model_name = model_name
        self.max_chars = max_chars
        self.temperature = max(0.05, temperature)
        self.fallback_conf_threshold = fallback_conf_threshold
        self.fallback_margin_threshold = fallback_margin_threshold
        self.heuristic_prior_weight = heuristic_prior_weight

        # Initialize sentiment pipeline once
        self.sentiment_pipe = pipeline("sentiment-analysis", model=model_name, device=device)

    # --------------------------- Preprocessing --------------------------- #

    def _strip_html(self, text: str) -> str:
        if "<" not in text or ">" not in text:
            return text
        cleaned = text
        for pattern, repl in self.HTML_REMOVE:
            cleaned = pattern.sub(repl, cleaned)
        cleaned = html.unescape(cleaned)
        return cleaned

    def _remove_signatures_and_quotes(self, text: str) -> str:
        lines = text.splitlines()
        pruned: List[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            # Skip signature markers
            if any(re.match(sig, stripped, re.IGNORECASE) for sig in self.SIGNATURE_MARKERS):
                break  # assume signature starts; truncate remainder
            # Skip quote headers and quoted lines
            if any(re.match(qh, stripped) for qh in self.QUOTE_HEADERS):
                continue
            if stripped.startswith(">"):
                continue
            pruned.append(stripped)
        return " ".join(pruned)

    def _clean(self, raw: str) -> str:
        text = self._strip_html(raw)
        text = self.URL_PATTERN.sub(" ", text)
        text = self._remove_signatures_and_quotes(text)
        text = self.MULTI_SPACE.sub(" ", text)
        return text.strip()[: self.max_chars]

    # --------------------------- Heuristic Priors ------------------------ #

    def _compute_priors(self, text: str) -> Dict[str, float]:
        priors = {c: 0.0 for c in self.categories}
        lowered = text.lower()
        for pattern, cat, weight in self.HEURISTIC_FEATURES:
            if pattern.search(lowered) and cat in priors:
                priors[cat] += weight
        return priors

    # --------------------------- Prompt Construction --------------------- #

    def _build_prompt(self, category: str, content: str) -> str:
        # Core prompt engineering idea: create a declarative hypothesis the model will implicitly
        # validate via relative POSITIVE activation if coherent.
        return f"This email is about {category}. {content}"[: self.max_chars + 64]

    # --------------------------- Scoring Logic --------------------------- #

    def _sentiment_positive_prob(self, text: str) -> float:
        try:
            result = self.sentiment_pipe(text, truncation=True)[0]
            label = result.get("label", "")
            score = float(result.get("score", 0.0))
            if label.upper().startswith("NEG"):
                # Interpret negative as low support.
                return 1.0 - score
            return score
        except Exception as e:
            logger.error("Sentiment pipeline failure: %s", e)
            return 0.0

    def _softmax(self, values: List[float]) -> List[float]:
        if not values:
            return []
        scaled = [v / self.temperature for v in values]
        m = max(scaled)
        exps = [math.exp(v - m) for v in scaled]
        denom = sum(exps) or 1.0
        return [e / denom for e in exps]

    # --------------------------- Public API ------------------------------ #

    def classify(self, raw_email_text: str, top_k: int = 5) -> ClassificationResult:
        if not raw_email_text or not raw_email_text.strip():
            return ClassificationResult(
                category="Unclassified",
                confidence=0.0,
                scores=[],
                fallback_used=True,
                raw_top_category_score=0.0,
                top_margin=0.0,
            )

        cleaned = self._clean(raw_email_text)
        if not cleaned:
            return ClassificationResult(
                category="Unclassified",
                confidence=0.0,
                scores=[],
                fallback_used=True,
                raw_top_category_score=0.0,
                top_margin=0.0,
            )

        priors = self._compute_priors(cleaned)

        raw_scores: List[float] = []
        for cat in self.categories:
            prompt = self._build_prompt(cat, cleaned)
            prob = self._sentiment_positive_prob(prompt)
            # Blend with heuristic prior: final pre-normalization score
            blended = prob * (1 - self.heuristic_prior_weight) + priors.get(cat, 0.0) * self.heuristic_prior_weight
            raw_scores.append(blended)

        norm_scores = self._softmax(raw_scores)
        cat_scores = list(zip(self.categories, norm_scores, raw_scores))
        # Sort by normalized probability descending
        cat_scores.sort(key=lambda x: x[1], reverse=True)

        top_category, top_conf, top_raw = cat_scores[0]
        second_conf = cat_scores[1][1] if len(cat_scores) > 1 else 0.0
        margin = top_conf - second_conf

        fallback_used = False
        final_category = top_category
        final_conf = top_conf

        if (top_conf < self.fallback_conf_threshold) or (margin < self.fallback_margin_threshold):
            fallback_used = True
            final_category = "Uncertain"
            # Optionally surface top 2 categories as context

        result_scores = [
            {"category": c, "score": float(conf), "raw": float(rw)}
            for c, conf, rw in cat_scores[: top_k if top_k > 0 else len(cat_scores)]
        ]

        return ClassificationResult(
            category=final_category if fallback_used else top_category,
            confidence=float(final_conf),
            scores=result_scores,
            fallback_used=fallback_used,
            raw_top_category_score=float(top_raw),
            top_margin=float(margin),
        )

# --------------------------- Convenience Function ------------------------------ #

def classify_email(text: str) -> Dict[str, Any]:
    """Functional helper returning plain dict (for simple integrations)."""
    classifier = PromptEmailClassifier()
    res = classifier.classify(text)
    return {
        "category": res.category,
        "confidence": res.confidence,
        "scores": res.scores,
        "fallback_used": res.fallback_used,
        "top_margin": res.top_margin,
    }

__all__ = ["PromptEmailClassifier", "classify_email", "ClassificationResult"]
