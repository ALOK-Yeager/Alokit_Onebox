# Hybrid Search - Quick Reference

## One-Liner
**Combines Elasticsearch keyword matching with vector semantic similarity using configurable weighted ranking.**

## Import
```python
from src.Services.search.VectorDB import VectorDB
from src.Services.search.hybrid_search import hybrid_search, HybridSearchConfig
```

## Basic Usage (3 lines)
```python
vectordb = VectorDB()
vector_results = vectordb.search("invoice payment", n_results=10)
results = hybrid_search("invoice payment", es_results, vector_results)
```

## Configuration Presets

| Use Case | Config | When to Use |
|----------|--------|-------------|
| **General Purpose** | `semantic_weight=0.7, keyword_weight=0.3` | Default, balanced |
| **Conceptual Search** | `semantic_weight=0.9, keyword_weight=0.1` | "emails about delays" |
| **Exact Matching** | `semantic_weight=0.3, keyword_weight=0.7` | Invoice numbers, names |
| **Rank-Based** | `method='rrf', rrf_k=60` | Score scales differ |

## Common Patterns

### Pattern 1: Standard Search
```python
results = hybrid_search(
    query="budget report",
    es_results=es_service.search(query),
    vector_results=vectordb.search(query, n_results=50),
)
```

### Pattern 2: Custom Weighting
```python
config = HybridSearchConfig(semantic_weight=0.8, keyword_weight=0.2)
results = hybrid_search(query, es_results, vector_results, config)
```

### Pattern 3: Filtered Search
```python
config = HybridSearchConfig(
    min_score_threshold=0.5,  # Only high-quality matches
    max_results=10            # Top 10 only
)
results = hybrid_search(query, es_results, vector_results, config)
```

### Pattern 4: RRF Method
```python
config = HybridSearchConfig(method='rrf', rrf_k=60)
results = hybrid_search(query, es_results, vector_results, config)
```

## Result Format
```python
{
    "id": "email-123",
    "hybrid_score": 0.876,      # Final score (0-1)
    "es_norm_score": 0.65,      # Normalized ES score
    "vector_norm_score": 0.95,  # Normalized vector score
    "_hybrid_source": {
        "in_es": True,          # Found in Elasticsearch
        "in_vector": True       # Found in Vector DB
    },
    # ... all original fields (subject, body, from, etc.)
}
```

## VectorDB Quick Reference

### Initialize
```python
vectordb = VectorDB(persist_directory="./vector_store")
```

### Add Single Email
```python
vectordb.add_email(
    email_id="msg-1",
    content="Subject: Meeting\n\nLet's sync tomorrow.",
    metadata={"from": "alice@example.com", "subject": "Meeting"}
)
```

### Batch Add Emails
```python
emails = [("msg-1", "content1"), ("msg-2", "content2")]
metadatas = [{"from": "alice"}, {"from": "bob"}]
vectordb.add_emails(emails, metadatas=metadatas)
```

### Search
```python
results = vectordb.search(
    query="project update",
    n_results=10,
    where={"folder": "INBOX"}  # Optional metadata filter
)
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **Scores all similar** | Increase candidate set size, try RRF method |
| **Semantic too strong** | Reduce `semantic_weight` to 0.5 or 0.4 |
| **Keyword too strong** | Increase `semantic_weight` to 0.8 or 0.9 |
| **Missing expected results** | Lower `min_score_threshold`, increase candidates |
| **Too many irrelevant results** | Raise `min_score_threshold`, reduce `max_results` |

## Performance Tips

1. **Retrieve 50-100 candidates** from each system before hybrid ranking
2. **Use batch operations** for indexing (`add_emails()` not `add_email()`)
3. **ChromaDB persists automatically** - no need to save/load
4. **Min-max normalization** is faster than standard (z-score)
5. **RRF is slightly faster** than weighted (no normalization)

## Weighting Decision Tree

```
Does query have specific keywords (invoice #, name, ID)?
├─ YES → Use 30/70 or 20/80 (keyword-heavy)
└─ NO → Does query describe a concept?
    ├─ YES → Use 80/20 or 90/10 (semantic-heavy)
    └─ NO → Use 70/30 (default balanced)
```

## Common Mistakes

❌ **Don't**: Retrieve only 5-10 candidates before hybrid ranking
✅ **Do**: Retrieve 50-100 candidates, let hybrid ranking pick top N

❌ **Don't**: Use raw scores without normalization
✅ **Do**: Let `hybrid_search()` handle normalization automatically

❌ **Don't**: Set weights that don't sum to 1.0
✅ **Do**: Ensure `semantic_weight + keyword_weight = 1.0`

❌ **Don't**: Index plain email IDs as content
✅ **Do**: Index "Subject: {subject}\n\n{body}" for best results

## Files Reference

| File | Purpose |
|------|---------|
| `src/Services/search/VectorDB.py` | ChromaDB wrapper |
| `src/Services/search/hybrid_search.py` | Ranking algorithm |
| `examples/hybrid_search_examples.py` | Test suite |
| `examples/api_integration_example.py` | FastAPI example |
| `docs/HYBRID_SEARCH_GUIDE.md` | Full documentation |
| `docs/HYBRID_SEARCH_DIAGRAMS.md` | Visual diagrams |

## Testing

### Run All Tests
```bash
python examples/hybrid_search_examples.py
```

### Expected Output
```
✅ Example 1: Basic Hybrid Search (70/30 semantic/keyword)
✅ Example 2: Custom Weighting (80/20 semantic/keyword)
✅ Example 3: Edge Cases
✅ Example 4: Reciprocal Rank Fusion (RRF)
✅ Example 5: Minimum Score Threshold
✅ Example 6: Realistic Integration Scenario
```

## API Endpoints (if using FastAPI example)

```
POST /api/search              # Hybrid search
POST /api/index               # Index single email
POST /api/index/batch         # Batch index emails
GET  /api/stats               # Index statistics
GET  /health                  # Health check
```

## Environment Variables

```bash
# No required environment variables
# Optional: Set log level
export PYTHONPATH=/path/to/onebox_aggregator
export LOG_LEVEL=INFO
```

## Dependencies

```
chromadb==0.3.26
sentence-transformers==2.2.2
fastapi==0.103.1         # For API example only
uvicorn==0.23.2          # For API example only
```

## Score Interpretation

| Hybrid Score | Interpretation |
|--------------|----------------|
| **0.9 - 1.0** | Excellent match (both semantic + keyword) |
| **0.7 - 0.9** | Strong match (one source very relevant) |
| **0.5 - 0.7** | Good match (moderate relevance) |
| **0.3 - 0.5** | Weak match (marginal relevance) |
| **0.0 - 0.3** | Poor match (consider filtering out) |

## Support Checklist

Before asking for help:
- [ ] Ran `examples/hybrid_search_examples.py` successfully
- [ ] Checked `docs/HYBRID_SEARCH_GUIDE.md` for detailed docs
- [ ] Verified both ES and Vector DB have indexed documents
- [ ] Confirmed weights sum to 1.0
- [ ] Tried adjusting `min_score_threshold` and `max_results`

## License

Same as parent project.
