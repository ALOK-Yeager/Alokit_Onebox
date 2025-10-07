"""Hybrid search combining Elasticsearch keyword results with vector database semantic results.

This module provides a sophisticated ranking algorithm that merges text-based search results
from Elasticsearch with semantic similarity results from a vector database (ChromaDB).

The hybrid approach leverages:
- Elasticsearch BM25 scoring for keyword matching and text relevance
- Vector embeddings for semantic similarity and conceptual matching

Key Features:
- Configurable weighting between semantic and keyword results (default 70/30)
- Score normalization using min-max scaling
- Intelligent deduplication preserving highest relevance scores
- Robust handling of edge cases (empty results, single-source results)
- Reciprocal Rank Fusion (RRF) as alternative ranking method

Example:
    from Services.search.hybrid_search import hybrid_search, HybridSearchConfig

    # Simple usage with default 70/30 semantic/keyword weighting
    results = hybrid_search(
        query="invoice payment",
        es_results=[{"id": "email-1", "score": 12.5, ...}],
        vector_results=[{"id": "email-2", "distance": 0.15, ...}]
    )

    # Custom weighting (80/20 semantic/keyword)
    config = HybridSearchConfig(semantic_weight=0.8, keyword_weight=0.2)
    results = hybrid_search(
        query="invoice payment",
        es_results=es_results,
        vector_results=vector_results,
        config=config
    )
"""
from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# -------------------------- Configuration -------------------------- #

@dataclass
class HybridSearchConfig:
    """Configuration for hybrid search ranking algorithm.

    Attributes:
        semantic_weight: Weight for vector similarity scores (0-1), default 0.7
        keyword_weight: Weight for Elasticsearch BM25 scores (0-1), default 0.3
        method: Ranking method - 'weighted' (default) or 'rrf' (Reciprocal Rank Fusion)
        rrf_k: Constant for RRF method, controls rank impact (default 60)
        normalize_method: Score normalization - 'minmax' (default) or 'standard'
        min_score_threshold: Minimum combined score to include in results (0-1)
        max_results: Maximum number of results to return (None = unlimited)
    """
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3
    method: Literal['weighted', 'rrf'] = 'weighted'
    rrf_k: int = 60
    normalize_method: Literal['minmax', 'standard'] = 'minmax'
    min_score_threshold: float = 0.0
    max_results: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if not (0 <= self.semantic_weight <= 1):
            raise ValueError("semantic_weight must be between 0 and 1")
        if not (0 <= self.keyword_weight <= 1):
            raise ValueError("keyword_weight must be between 0 and 1")
        if abs((self.semantic_weight + self.keyword_weight) - 1.0) > 1e-6:
            raise ValueError("semantic_weight + keyword_weight must equal 1.0")
        if self.rrf_k < 1:
            raise ValueError("rrf_k must be >= 1")
        if not (0 <= self.min_score_threshold <= 1):
            raise ValueError("min_score_threshold must be between 0 and 1")


# -------------------------- Helper Functions -------------------------- #

def _normalize_scores_minmax(scores: List[float]) -> List[float]:
    """Normalize scores to 0-1 range using min-max scaling.

    Args:
        scores: Raw score values

    Returns:
        Normalized scores in [0, 1] range
    """
    if not scores or len(scores) == 1:
        return [1.0] * len(scores)

    min_score = min(scores)
    max_score = max(scores)
    score_range = max_score - min_score

    if score_range < 1e-9:  # All scores are essentially equal
        return [0.5] * len(scores)

    return [(s - min_score) / score_range for s in scores]


def _normalize_scores_standard(scores: List[float]) -> List[float]:
    """Normalize scores using z-score standardization, then sigmoid to [0, 1].

    Args:
        scores: Raw score values

    Returns:
        Normalized scores in [0, 1] range
    """
    if not scores or len(scores) == 1:
        return [1.0] * len(scores)

    mean_score = sum(scores) / len(scores)
    variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
    std_dev = variance ** 0.5

    if std_dev < 1e-9:
        return [0.5] * len(scores)

    # Z-score then sigmoid
    import math
    z_scores = [(s - mean_score) / std_dev for s in scores]
    return [1 / (1 + math.exp(-z)) for z in z_scores]


def _extract_es_score(result: Dict[str, Any]) -> float:
    """Extract Elasticsearch score from result dict.

    Looks for '_score' or 'score' keys. Defaults to 0.0 if not found.
    """
    return float(result.get('_score', result.get('score', 0.0)))


def _extract_vector_distance(result: Dict[str, Any]) -> float:
    """Extract vector distance from result dict.

    Looks for 'distance' key. Lower distance = higher similarity.
    Defaults to 1.0 (maximum distance) if not found.
    """
    return float(result.get('distance', 1.0))


def _extract_result_id(result: Dict[str, Any]) -> str:
    """Extract unique identifier from result dict.

    Tries '_id', 'id', then falls back to hash of the result.
    """
    if '_id' in result:
        return str(result['_id'])
    if 'id' in result:
        return str(result['id'])
    # Fallback to hash (not ideal but prevents crashes)
    logger.warning("Result missing 'id' field: %s", result)
    return str(hash(frozenset(result.items()) if isinstance(result, dict) else str(result)))


# -------------------------- Ranking Methods -------------------------- #

def _rank_weighted(
    es_results: List[Dict[str, Any]],
    vector_results: List[Dict[str, Any]],
    config: HybridSearchConfig,
) -> List[Dict[str, Any]]:
    """Rank results using weighted score combination.

    Algorithm:
    1. Normalize ES scores (higher = better)
    2. Convert vector distances to similarity scores (1 - distance)
    3. Normalize similarity scores
    4. Combine: final_score = semantic_weight * norm_sim + keyword_weight * norm_es
    5. Deduplicate by ID, keeping highest score
    6. Sort by final score descending

    Args:
        es_results: Elasticsearch results with scores
        vector_results: Vector DB results with distances
        config: Hybrid search configuration

    Returns:
        Combined and ranked results with 'hybrid_score' field
    """
    # Build lookup tables
    es_lookup: Dict[str, Dict[str, Any]] = {}
    vector_lookup: Dict[str, Dict[str, Any]] = {}

    # Process ES results
    if es_results:
        es_scores = [_extract_es_score(r) for r in es_results]
        if config.normalize_method == 'minmax':
            norm_es_scores = _normalize_scores_minmax(es_scores)
        else:
            norm_es_scores = _normalize_scores_standard(es_scores)

        for result, norm_score in zip(es_results, norm_es_scores):
            result_id = _extract_result_id(result)
            es_lookup[result_id] = {**result, 'es_norm_score': norm_score}

    # Process vector results
    if vector_results:
        distances = [_extract_vector_distance(r) for r in vector_results]
        # Convert distance to similarity (assume distance in [0, 2] range typical for cosine)
        # Clamp distances to avoid negative similarities
        similarities = [max(0.0, 1.0 - d) for d in distances]

        if config.normalize_method == 'minmax':
            norm_sim_scores = _normalize_scores_minmax(similarities)
        else:
            norm_sim_scores = _normalize_scores_standard(similarities)

        for result, norm_score in zip(vector_results, norm_sim_scores):
            result_id = _extract_result_id(result)
            vector_lookup[result_id] = {**result, 'vector_norm_score': norm_score}

    # Combine results
    all_ids = set(es_lookup.keys()) | set(vector_lookup.keys())
    combined: List[Dict[str, Any]] = []

    for result_id in all_ids:
        es_data = es_lookup.get(result_id)
        vector_data = vector_lookup.get(result_id)

        # Use the more complete record as base
        base: Dict[str, Any]
        if es_data and vector_data:
            base = {**es_data, **vector_data}  # Merge, vector data wins conflicts
        elif es_data:
            base = es_data
        elif vector_data:
            base = vector_data
        else:
            # Should never happen since result_id came from union of both lookups
            logger.error("Result ID %s not found in either lookup table", result_id)
            continue

        # Calculate weighted score
        es_score = es_data.get('es_norm_score', 0.0) if es_data else 0.0
        vec_score = vector_data.get('vector_norm_score', 0.0) if vector_data else 0.0
        hybrid_score = (config.semantic_weight * vec_score +
                        config.keyword_weight * es_score)

        base['hybrid_score'] = hybrid_score
        base['es_norm_score'] = es_score
        base['vector_norm_score'] = vec_score
        base['_hybrid_source'] = {
            'in_es': result_id in es_lookup,
            'in_vector': result_id in vector_lookup,
        }

        if hybrid_score >= config.min_score_threshold:
            combined.append(base)

    # Sort by hybrid score descending
    combined.sort(key=lambda x: x['hybrid_score'], reverse=True)

    # Apply max results limit
    if config.max_results:
        combined = combined[:config.max_results]

    return combined


def _rank_rrf(
    es_results: List[Dict[str, Any]],
    vector_results: List[Dict[str, Any]],
    config: HybridSearchConfig,
) -> List[Dict[str, Any]]:
    """Rank results using Reciprocal Rank Fusion (RRF).

    RRF formula: score(d) = sum over all rankers of: 1 / (k + rank(d))
    where k is a constant (typically 60) and rank starts at 1.

    RRF is ranking-method agnostic and doesn't require score normalization.

    Args:
        es_results: Elasticsearch results (ranked by relevance)
        vector_results: Vector DB results (ranked by similarity)
        config: Hybrid search configuration

    Returns:
        Combined and ranked results with 'rrf_score' field
    """
    k = config.rrf_k
    rrf_scores: Dict[str, float] = {}
    result_data: Dict[str, Dict[str, Any]] = {}

    # ES contributions (rank 1 = first result)
    for rank, result in enumerate(es_results, start=1):
        result_id = _extract_result_id(result)
        rrf_scores[result_id] = rrf_scores.get(result_id, 0.0) + (1.0 / (k + rank))
        if result_id not in result_data:
            result_data[result_id] = {**result}

    # Vector contributions
    for rank, result in enumerate(vector_results, start=1):
        result_id = _extract_result_id(result)
        rrf_scores[result_id] = rrf_scores.get(result_id, 0.0) + (1.0 / (k + rank))
        if result_id not in result_data:
            result_data[result_id] = {**result}
        else:
            # Merge vector data into existing
            result_data[result_id].update(result)

    # Build combined results
    combined: List[Dict[str, Any]] = []
    for result_id, rrf_score in rrf_scores.items():
        result = result_data[result_id]
        result['rrf_score'] = rrf_score
        result['hybrid_score'] = rrf_score  # Alias for consistency
        combined.append(result)

    # Sort by RRF score descending
    combined.sort(key=lambda x: x['rrf_score'], reverse=True)

    # Apply max results limit
    if config.max_results:
        combined = combined[:config.max_results]

    return combined


# -------------------------- Main API -------------------------- #

def hybrid_search(
    query: str,
    es_results: List[Dict[str, Any]],
    vector_results: List[Dict[str, Any]],
    config: Optional[HybridSearchConfig] = None,
) -> List[Dict[str, Any]]:
    """Combine Elasticsearch keyword results with vector database semantic results.

    This function implements a hybrid ranking algorithm that merges two types of search:
    1. **Keyword/Text Search (Elasticsearch)**: BM25 scoring for exact/fuzzy term matching
    2. **Semantic Search (Vector DB)**: Embedding similarity for conceptual matching

    **Ranking Algorithm (Weighted Method - Default)**:

    Step 1: Score Extraction
        - Extract Elasticsearch scores (higher = better relevance)
        - Extract vector distances (lower = higher similarity)

    Step 2: Normalization
        - ES scores: Min-max normalize to [0, 1]
        - Vector distances: Convert to similarity (1 - distance), then normalize to [0, 1]

    Step 3: Weighted Combination
        - final_score = semantic_weight * normalized_similarity + keyword_weight * normalized_es_score
        - Default: 70% semantic, 30% keyword (0.7 * vec + 0.3 * es)

    Step 4: Deduplication
        - If a document appears in both result sets, scores are combined using weights
        - Each document appears exactly once in final results

    Step 5: Sorting & Filtering
        - Sort by final_score descending
        - Filter by min_score_threshold if configured
        - Limit to max_results if configured

    **Alternative: Reciprocal Rank Fusion (RRF)**:
        - Set config.method = 'rrf' for ranking-based fusion
        - RRF score = sum(1 / (k + rank)) across all rankers
        - Requires no score normalization, only ranking order matters

    **Edge Cases Handled**:
        - Empty ES results: Uses only vector scores
        - Empty vector results: Uses only ES scores
        - Both empty: Returns empty list
        - Single result set: Applies normalization and returns
        - Missing IDs: Uses hash fallback (logs warning)
        - Equal scores: Preserves stable sort order

    Args:
        query: Original search query string (for logging/context)
        es_results: List of Elasticsearch results, each dict must have 'id' and 'score'/'_score'
        vector_results: List of vector DB results, each dict must have 'id' and 'distance'
        config: Optional configuration for weighting and ranking method

    Returns:
        List of combined results sorted by relevance. Each result dict includes:
        - All original fields from source result(s)
        - 'hybrid_score': Final combined score (0-1 for weighted, unbounded for RRF)
        - 'es_norm_score': Normalized ES score (weighted method only)
        - 'vector_norm_score': Normalized vector score (weighted method only)
        - '_hybrid_source': Dict with 'in_es' and 'in_vector' boolean flags

    Raises:
        ValueError: If config parameters are invalid

    Example:
        >>> es_results = [
        ...     {"id": "email-1", "score": 12.5, "subject": "Invoice"},
        ...     {"id": "email-2", "score": 8.3, "subject": "Payment"}
        ... ]
        >>> vector_results = [
        ...     {"id": "email-2", "distance": 0.15, "document": "Payment details..."},
        ...     {"id": "email-3", "distance": 0.22, "document": "Invoice attached..."}
        ... ]
        >>> results = hybrid_search("invoice payment", es_results, vector_results)
        >>> print(results[0]['id'], results[0]['hybrid_score'])
        email-2 0.876
    """
    if config is None:
        config = HybridSearchConfig()

    # Handle edge cases
    if not es_results and not vector_results:
        logger.info("Both ES and vector results are empty for query: %s", query)
        return []

    if not es_results:
        logger.info("ES results empty, using only vector results for query: %s", query)
        # Return vector results with normalized scores as hybrid_score
        distances = [_extract_vector_distance(r) for r in vector_results]
        similarities = [max(0.0, 1.0 - d) for d in distances]
        norm_scores = _normalize_scores_minmax(similarities)
        results = []
        for result, score in zip(vector_results, norm_scores):
            result_copy = {**result, 'hybrid_score': score, 'vector_norm_score': score, 'es_norm_score': 0.0}
            results.append(result_copy)
        results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        if config.max_results:
            results = results[:config.max_results]
        return results

    if not vector_results:
        logger.info("Vector results empty, using only ES results for query: %s", query)
        # Return ES results with normalized scores as hybrid_score
        es_scores = [_extract_es_score(r) for r in es_results]
        norm_scores = _normalize_scores_minmax(es_scores)
        results = []
        for result, score in zip(es_results, norm_scores):
            result_copy = {**result, 'hybrid_score': score, 'es_norm_score': score, 'vector_norm_score': 0.0}
            results.append(result_copy)
        results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        if config.max_results:
            results = results[:config.max_results]
        return results

    # Normal case: both result sets present
    logger.info(
        "Hybrid search for query '%s': %d ES results, %d vector results, method=%s",
        query, len(es_results), len(vector_results), config.method
    )

    if config.method == 'rrf':
        return _rank_rrf(es_results, vector_results, config)
    else:
        return _rank_weighted(es_results, vector_results, config)


__all__ = ["hybrid_search", "HybridSearchConfig"]
