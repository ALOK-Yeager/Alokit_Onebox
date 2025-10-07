"""Example usage for the PromptEmailClassifier.

Run:
    python examples/prompt_classifier_example.py
"""
from src.Services.ai.prompt_email_classifier import PromptEmailClassifier

SAMPLE_EMAIL = """Subject: Flight Itinerary Confirmation\n\nYour flight booking is confirmed. Boarding pass will be sent 24 hours prior.\nInvoice total: $423.18 USD.\n\nTo manage your booking visit: https://air.example.com/booking/ABC123\n\n--\nThanks,\nTravel Support Team\n"""

def main():
    clf = PromptEmailClassifier()
    result = clf.classify(SAMPLE_EMAIL)
    print("Category:", result.category)
    print("Confidence:", f"{result.confidence:.4f}")
    print("Top Scores:")
    for s in result.scores:
        print(f"  - {s['category']}: {s['score']:.4f} (raw={s['raw']:.4f})")
    print("Fallback used:", result.fallback_used)
    print("Top margin:", f"{result.top_margin:.4f}")

if __name__ == "__main__":
    main()
