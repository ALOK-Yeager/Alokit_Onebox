# Hybrid Search Implementation Guide

## Overview

The hybrid search system combines two complementary search approaches:

1. **Elasticsearch (Keyword/Text Search)**: Uses BM25 algorithm for exact term matching and text relevance
2. **Vector Database (Semantic Search)**: Uses sentence embeddings for conceptual similarity

This provides the best of both worlds - precise keyword matching AND semantic understanding.

## Architecture

```
Query → [Elasticsearch Search] → ES Results (BM25 scores)
     ↘                                    ↓
       [Vector DB Search] → Vector Results (cosine distances)
                                          ↓
                          [Hybrid Ranking Algorithm]
                                          ↓
                              Combined & Ranked Results
```

## Implementation Files

- **`src/Services/search/VectorDB.py`**: ChromaDB vector store with persistent storage
- **`src/Services/search/hybrid_search.py`**: Hybrid ranking algorithm with weighted scoring
- **`src/Services/search/ElasticsearchService.ts`**: Existing Elasticsearch implementation
- **`examples/hybrid_search_examples.py`**: Usage examples and test cases

## Ranking Algorithm

### Weighted Method (Default - 70/30 Semantic/Keyword)

**Step 1: Score Extraction**
- Extract Elasticsearch BM25 scores (higher = more relevant)
- Extract vector cosine distances (lower = more similar)

**Step 2: Normalization**
- Normalize ES scores to [0, 1] using min-max scaling
- Convert vector distances to similarities: `similarity = 1 - distance`
- Normalize similarities to [0, 1]

**Step 3: Weighted Combination**
```python
final_score = semantic_weight * normalized_similarity + keyword_weight * normalized_es_score
# Default: 0.7 * vector + 0.3 * es
```

**Step 4: Deduplication**
- Documents appearing in both result sets have their scores combined
- Each document appears exactly once in final results

**Step 5: Sorting & Filtering**
- Sort by final_score descending
- Apply optional minimum score threshold
- Limit to max_results if configured

### Alternative: Reciprocal Rank Fusion (RRF)

RRF uses ranking positions instead of raw scores:
```python
rrf_score(doc) = sum(1 / (k + rank)) for all rankers
# where k=60 (typical constant) and rank starts at 1
```

Benefits:
- Score-agnostic (only order matters)
- No normalization needed
- Robust to score scale differences

## Usage Examples

### Basic Usage

```python
from src.Services.search.hybrid_search import hybrid_search, HybridSearchConfig
from src.Services.search.VectorDB import VectorDB
# Assume ElasticsearchService is available via TypeScript/API

# Get Elasticsearch results
es_results = [
    {"id": "email-1", "score": 15.2, "subject": "Invoice #12345"},
    {"id": "email-2", "score": 12.8, "subject": "Payment confirmation"},
]

# Get Vector DB results
vectordb = VectorDB()
vector_results = vectordb.search("invoice payment", n_results=10)

# Combine with default 70/30 weighting
results = hybrid_search(
    query="invoice payment",
    es_results=es_results,
    vector_results=vector_results
)

for result in results[:5]:
    print(f"{result['id']}: score={result['hybrid_score']:.3f}")
```

### Custom Weighting

```python
# 80/20 semantic/keyword - prefer semantic matches
config = HybridSearchConfig(
    semantic_weight=0.8,
    keyword_weight=0.2,
    max_results=10
)

results = hybrid_search(
    query="budget report",
    es_results=es_results,
    vector_results=vector_results,
    config=config
)
```

### Using RRF Method

```python
# Reciprocal Rank Fusion
config = HybridSearchConfig(
    method='rrf',
    rrf_k=60,
    max_results=10
)

results = hybrid_search(
    query="meeting schedule",
    es_results=es_results,
    vector_results=vector_results,
    config=config
)
```

### Score Threshold Filtering

```python
# Only return results with hybrid_score >= 0.5
config = HybridSearchConfig(
    min_score_threshold=0.5,
    max_results=20
)

results = hybrid_search(
    query="important emails",
    es_results=es_results,
    vector_results=vector_results,
    config=config
)
```

## Integration with Existing Services

### Full Search Pipeline

```python
from src.Services.search.VectorDB import VectorDB
from src.Services.search.hybrid_search import hybrid_search, HybridSearchConfig

class SearchService:
    def __init__(self):
        self.vectordb = VectorDB(persist_directory="./vector_store")
        # self.es_service = ElasticsearchService() # TypeScript service

    def search_emails(self, query: str, account_id: str = None, max_results: int = 20):
        """Perform hybrid search across indexed emails."""
        
        # 1. Get Elasticsearch results (via API call to TypeScript service)
        es_results = self.es_service.search(
            query=query,
            accountId=account_id,
            size=50  # Get more candidates for better hybrid ranking
        )['emails']
        
        # 2. Get vector similarity results
        vector_results = self.vectordb.search(
            query=query,
            n_results=50,
            where={"accountId": account_id} if account_id else None
        )
        
        # 3. Combine with hybrid ranking
        config = HybridSearchConfig(
            semantic_weight=0.7,
            keyword_weight=0.3,
            max_results=max_results,
            min_score_threshold=0.1  # Filter very low scores
        )
        
        results = hybrid_search(
            query=query,
            es_results=es_results,
            vector_results=vector_results,
            config=config
        )
        
        return results
```

### Indexing Emails to Both Systems

```python
def index_email(email: Email):
    """Index an email to both Elasticsearch and VectorDB."""
    
    # 1. Index to Elasticsearch (TypeScript service)
    await elasticsearchService.indexEmail(email)
    
    # 2. Index to VectorDB
    vectordb = VectorDB()
    
    # Combine subject and body for embedding
    content = f"Subject: {email.subject}\n\n{email.body}"
    
    metadata = {
        "accountId": email.accountId,
        "folder": email.folder,
        "from": email.from_address,
        "subject": email.subject,
        "date": email.date.isoformat(),
        "aiCategory": email.aiCategory,
    }
    
    vectordb.add_email(
        email_id=email.id,
        content=content,
        metadata=metadata
    )
```

### Batch Indexing

```python
def batch_index_emails(emails: List[Email]):
    """Efficiently index multiple emails."""
    
    # Index to Elasticsearch
    for email in emails:
        await elasticsearchService.indexEmail(email)
    
    # Batch index to VectorDB
    vectordb = VectorDB()
    
    email_tuples = [
        (email.id, f"Subject: {email.subject}\n\n{email.body}")
        for email in emails
    ]
    
    metadatas = [
        {
            "accountId": email.accountId,
            "folder": email.folder,
            "from": email.from_address,
            "subject": email.subject,
            "date": email.date.isoformat(),
        }
        for email in emails
    ]
    
    vectordb.add_emails(email_tuples, metadatas=metadatas)
```

## Edge Cases Handled

1. **Empty Elasticsearch results**: Uses only vector scores (normalized)
2. **Empty vector results**: Uses only ES scores (normalized)
3. **Both empty**: Returns empty list
4. **Single source per document**: Applies weighting with 0.0 for missing source
5. **Overlapping documents**: Combines scores using configured weights
6. **Missing IDs**: Falls back to hash (logs warning)
7. **Equal scores**: Preserves stable sort order

## Configuration Guidelines

### When to use 70/30 (default)
- General purpose email search
- Balanced between precision and recall
- Users enter natural language queries

### When to use 80/20 or 90/10 (semantic-heavy)
- Conceptual searches ("emails about project delays")
- Users describe what they're looking for rather than keywords
- Important to catch synonyms and paraphrases

### When to use 30/70 or 20/80 (keyword-heavy)
- Exact term matching important (invoice numbers, names)
- Technical content with specific terminology
- Users know exact keywords to search for

### When to use RRF
- Score scales very different between systems
- Want ranking-only approach (no score interpretation)
- Experimentation shows better results than weighted

## Performance Considerations

1. **Candidate Set Size**: Retrieve 50-100 candidates from each system before hybrid ranking
2. **Batch Indexing**: Use `add_emails()` for multiple documents (much faster)
3. **Vector Store**: ChromaDB persists to disk - no re-indexing needed on restart
4. **Normalization**: Min-max is faster than standard (z-score + sigmoid)
5. **RRF**: Slightly faster than weighted (no normalization step)

## Testing

Run the comprehensive test suite:

```bash
python examples/hybrid_search_examples.py
```

This tests:
- Basic usage with default weighting
- Custom weighting configurations
- All edge cases
- RRF method
- Score threshold filtering
- Realistic integration scenario

## API Response Format

Each result includes:

```python
{
    "id": "email-123",              # Document ID
    "hybrid_score": 0.876,          # Combined relevance score (0-1 for weighted)
    "es_norm_score": 0.65,          # Normalized ES score
    "vector_norm_score": 0.95,      # Normalized vector score
    "_hybrid_source": {
        "in_es": True,               # Found in Elasticsearch
        "in_vector": True            # Found in Vector DB
    },
    # ... all other fields from original results
    "subject": "Project Update",
    "from": "manager@company.com",
    "body": "...",
    # etc.
}
```

## Troubleshooting

### Scores all similar/flat
- Check that both result sets have varied scores
- Try increasing candidate set size
- Consider switching to RRF method

### Semantic results dominating too much
- Reduce semantic_weight (try 0.5 or 0.4)
- Check vector model quality
- Verify ES queries are returning good matches

### Keyword results dominating too much
- Increase semantic_weight (try 0.8 or 0.9)
- Check vector index has sufficient documents
- Verify embeddings are being generated correctly

### Missing expected results
- Increase candidate set size in both systems
- Lower min_score_threshold
- Check both indexes contain the document

## Future Enhancements

- [ ] Add learned-to-rank (LTR) weighting based on user feedback
- [ ] Support for temporal boosting (newer emails ranked higher)
- [ ] Category-specific weighting (different weights for different email types)
- [ ] Query expansion using embeddings
- [ ] A/B testing framework for comparing configurations
- [ ] Real-time weight adjustment based on click-through rates

## References

- [Elasticsearch BM25 Algorithm](https://www.elastic.co/guide/en/elasticsearch/reference/current/index-modules-similarity.html)
- [Sentence Transformers Documentation](https://www.sbert.net/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Reciprocal Rank Fusion Paper](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
