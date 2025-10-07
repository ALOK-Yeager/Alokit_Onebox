"""Example usage and tests for hybrid_search functionality.

This script demonstrates:
1. Basic hybrid search usage
2. Custom weighting configurations
3. Edge case handling
4. RRF ranking method
5. Integration with VectorDB and Elasticsearch results
"""

import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Services.search.hybrid_search import hybrid_search, HybridSearchConfig


def example_basic_usage():
    """Basic hybrid search with default 70/30 weighting."""
    print("=" * 60)
    print("Example 1: Basic Hybrid Search (70/30 semantic/keyword)")
    print("=" * 60)

    # Simulated Elasticsearch results (BM25 scores)
    es_results = [
        {"id": "email-1", "score": 15.2, "subject": "Invoice #12345", "from": "billing@acme.com"},
        {"id": "email-2", "score": 12.8, "subject": "Payment confirmation", "from": "finance@acme.com"},
        {"id": "email-3", "score": 8.5, "subject": "Receipt for your order", "from": "orders@shop.com"},
    ]

    # Simulated Vector DB results (cosine distances)
    vector_results = [
        {"id": "email-2", "distance": 0.12, "document": "Your payment has been processed successfully..."},
        {"id": "email-4", "distance": 0.18, "document": "Invoice attached for services rendered..."},
        {"id": "email-5", "distance": 0.25, "document": "Thank you for your payment..."},
    ]

    results = hybrid_search(
        query="invoice payment",
        es_results=es_results,
        vector_results=vector_results
    )

    print(f"\nTotal combined results: {len(results)}")
    print("\nTop 3 ranked results:")
    for i, result in enumerate(results[:3], 1):
        print(f"\n{i}. ID: {result['id']}")
        print(f"   Hybrid Score: {result['hybrid_score']:.4f}")
        print(f"   ES Score (norm): {result.get('es_norm_score', 0):.4f}")
        print(f"   Vector Score (norm): {result.get('vector_norm_score', 0):.4f}")
        print(f"   Subject: {result.get('subject', 'N/A')}")
        print(f"   In ES: {result['_hybrid_source']['in_es']}, In Vector: {result['_hybrid_source']['in_vector']}")


def example_custom_weighting():
    """Custom weighting: 80/20 semantic/keyword."""
    print("\n" + "=" * 60)
    print("Example 2: Custom Weighting (80/20 semantic/keyword)")
    print("=" * 60)

    es_results = [
        {"id": "email-1", "score": 20.0, "subject": "Meeting schedule"},
        {"id": "email-2", "score": 15.0, "subject": "Project sync"},
    ]

    vector_results = [
        {"id": "email-2", "distance": 0.08, "document": "Let's sync on the project..."},
        {"id": "email-3", "distance": 0.15, "document": "Meeting agenda for next week..."},
    ]

    config = HybridSearchConfig(
        semantic_weight=0.8,
        keyword_weight=0.2,
        max_results=5
    )

    results = hybrid_search(
        query="project meeting",
        es_results=es_results,
        vector_results=vector_results,
        config=config
    )

    print(f"\nResults with 80% semantic weight:")
    for result in results:
        print(f"  {result['id']}: hybrid={result['hybrid_score']:.4f}")


def example_edge_cases():
    """Test edge case handling."""
    print("\n" + "=" * 60)
    print("Example 3: Edge Cases")
    print("=" * 60)

    # Case 1: Empty ES results
    print("\n1. Empty Elasticsearch results:")
    vector_results = [
        {"id": "email-1", "distance": 0.1, "document": "Content..."},
        {"id": "email-2", "distance": 0.2, "document": "More content..."},
    ]
    results = hybrid_search("test query", [], vector_results)
    print(f"   Results: {len(results)} (using vector scores only)")
    if results:
        print(f"   Top result: {results[0]['id']} score={results[0]['hybrid_score']:.4f}")

    # Case 2: Empty vector results
    print("\n2. Empty vector results:")
    es_results = [
        {"id": "email-3", "score": 10.0, "subject": "Test"},
        {"id": "email-4", "score": 8.0, "subject": "Another test"},
    ]
    results = hybrid_search("test query", es_results, [])
    print(f"   Results: {len(results)} (using ES scores only)")
    if results:
        print(f"   Top result: {results[0]['id']} score={results[0]['hybrid_score']:.4f}")

    # Case 3: Both empty
    print("\n3. Both empty:")
    results = hybrid_search("test query", [], [])
    print(f"   Results: {len(results)} (should be 0)")

    # Case 4: Single overlapping result
    print("\n4. Single overlapping result:")
    results = hybrid_search(
        "test",
        [{"id": "email-1", "score": 10.0}],
        [{"id": "email-1", "distance": 0.1}]
    )
    print(f"   Results: {len(results)}")
    if results:
        print(f"   Combined score: {results[0]['hybrid_score']:.4f}")


def example_rrf_method():
    """Reciprocal Rank Fusion ranking."""
    print("\n" + "=" * 60)
    print("Example 4: Reciprocal Rank Fusion (RRF)")
    print("=" * 60)

    es_results = [
        {"id": "email-1", "score": 50.0, "subject": "Important"},
        {"id": "email-2", "score": 30.0, "subject": "Relevant"},
        {"id": "email-3", "score": 10.0, "subject": "Somewhat"},
    ]

    vector_results = [
        {"id": "email-3", "distance": 0.05, "document": "Very similar..."},
        {"id": "email-2", "distance": 0.10, "document": "Similar..."},
        {"id": "email-1", "distance": 0.20, "document": "Less similar..."},
    ]

    config = HybridSearchConfig(method='rrf', rrf_k=60)

    results = hybrid_search(
        query="test query",
        es_results=es_results,
        vector_results=vector_results,
        config=config
    )

    print("\nRRF ranking (k=60):")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['id']}: RRF score={result['rrf_score']:.4f}")


def example_score_threshold():
    """Filter results by minimum score threshold."""
    print("\n" + "=" * 60)
    print("Example 5: Minimum Score Threshold")
    print("=" * 60)

    es_results = [
        {"id": f"email-{i}", "score": 20.0 - i * 2} for i in range(1, 6)
    ]

    vector_results = [
        {"id": f"email-{i}", "distance": 0.1 * i} for i in range(1, 6)
    ]

    config = HybridSearchConfig(min_score_threshold=0.5, max_results=10)

    results = hybrid_search(
        query="test",
        es_results=es_results,
        vector_results=vector_results,
        config=config
    )

    print(f"\nResults with min_score_threshold=0.5:")
    for result in results:
        print(f"  {result['id']}: score={result['hybrid_score']:.4f}")


def example_integration_scenario():
    """Realistic integration scenario with metadata."""
    print("\n" + "=" * 60)
    print("Example 6: Realistic Integration Scenario")
    print("=" * 60)

    # Elasticsearch results with full metadata
    es_results = [
        {
            "id": "msg-001",
            "score": 18.5,
            "subject": "Q4 Financial Report",
            "from": "cfo@company.com",
            "date": "2025-10-01T10:00:00Z",
            "body": "Please find attached the Q4 financial report...",
            "aiCategory": "finance",
        },
        {
            "id": "msg-002",
            "score": 14.2,
            "subject": "Budget Review Meeting",
            "from": "manager@company.com",
            "date": "2025-10-02T14:30:00Z",
            "body": "Let's review the budget for next quarter...",
            "aiCategory": "meeting",
        },
        {
            "id": "msg-003",
            "score": 10.8,
            "subject": "Expense Approval Needed",
            "from": "hr@company.com",
            "date": "2025-10-03T09:15:00Z",
            "body": "Your expense report requires approval...",
            "aiCategory": "finance",
        },
    ]

    # Vector DB results with semantic matches
    vector_results = [
        {
            "id": "msg-002",
            "distance": 0.08,
            "document": "Let's review the budget for next quarter...",
            "metadata": {"subject": "Budget Review Meeting"},
        },
        {
            "id": "msg-004",
            "distance": 0.12,
            "document": "Annual budget planning session scheduled...",
            "metadata": {"subject": "Budget Planning"},
        },
        {
            "id": "msg-001",
            "distance": 0.18,
            "document": "Please find attached the Q4 financial report...",
            "metadata": {"subject": "Q4 Financial Report"},
        },
    ]

    config = HybridSearchConfig(
        semantic_weight=0.7,
        keyword_weight=0.3,
        max_results=3
    )

    results = hybrid_search(
        query="budget financial report",
        es_results=es_results,
        vector_results=vector_results,
        config=config
    )

    print("\nTop 3 results for 'budget financial report':")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.get('subject', 'N/A')}")
        print(f"   ID: {result['id']}")
        print(f"   From: {result.get('from', 'N/A')}")
        print(f"   Category: {result.get('aiCategory', 'N/A')}")
        print(f"   Hybrid Score: {result['hybrid_score']:.4f}")
        print(f"   ES: {result['es_norm_score']:.3f} | Vector: {result['vector_norm_score']:.3f}")
        print(f"   Found in: ES={result['_hybrid_source']['in_es']}, Vector={result['_hybrid_source']['in_vector']}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("HYBRID SEARCH EXAMPLES AND TESTS")
    print("=" * 60)

    example_basic_usage()
    example_custom_weighting()
    example_edge_cases()
    example_rrf_method()
    example_score_threshold()
    example_integration_scenario()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60 + "\n")
