# Hybrid Search Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          User Search Query                           │
│                      "invoice payment details"                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │  Search Dispatcher  │
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ▼                                 ▼
┌─────────────────────────┐         ┌─────────────────────────┐
│   Elasticsearch (ES)    │         │   Vector Database       │
│   BM25 Keyword Search   │         │   Semantic Similarity   │
└───────────┬─────────────┘         └───────────┬─────────────┘
            │                                   │
            │ Returns:                          │ Returns:
            │ - Document IDs                    │ - Document IDs
            │ - BM25 Scores                     │ - Cosine Distances
            │ - Metadata                        │ - Metadata
            │                                   │
            │                                   │
            └───────────────┬───────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  Hybrid Search Engine │
                │  (hybrid_search.py)   │
                └───────────┬───────────┘
                            │
                ┌───────────┴──────────┐
                │                      │
                │  1. Score Extract    │
                │  2. Normalize [0,1]  │
                │  3. Weight Combine   │
                │  4. Deduplicate      │
                │  5. Sort & Filter    │
                │                      │
                └───────────┬──────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   Ranked Results      │
                │   with Hybrid Scores  │
                └───────────────────────┘
```

## Data Flow Example

```
Query: "budget financial report"

┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Elasticsearch Results (BM25)                            │
├─────────────────────────────────────────────────────────────────┤
│ ID: msg-001  Score: 18.5  Subject: "Q4 Financial Report"       │
│ ID: msg-002  Score: 14.2  Subject: "Budget Review Meeting"     │
│ ID: msg-003  Score: 10.8  Subject: "Expense Approval"          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                    Normalize to [0,1]
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Normalized ES Scores                                            │
├─────────────────────────────────────────────────────────────────┤
│ msg-001: 1.000  (highest ES score)                             │
│ msg-002: 0.442                                                  │
│ msg-003: 0.000  (lowest ES score)                              │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Vector Database Results (Cosine Distance)              │
├─────────────────────────────────────────────────────────────────┤
│ ID: msg-002  Distance: 0.08  Subject: "Budget Review Meeting"  │
│ ID: msg-004  Distance: 0.12  Subject: "Budget Planning"        │
│ ID: msg-001  Distance: 0.18  Subject: "Q4 Financial Report"    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                Convert to Similarity (1 - distance)
                            ↓
                    Normalize to [0,1]
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Normalized Vector Scores                                        │
├─────────────────────────────────────────────────────────────────┤
│ msg-002: 1.000  (most similar)                                 │
│ msg-004: 0.600                                                  │
│ msg-001: 0.000  (least similar)                                │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Weighted Combination (70% semantic, 30% keyword)       │
├─────────────────────────────────────────────────────────────────┤
│ msg-001: 0.7×0.000 + 0.3×1.000 = 0.300  (ES only)            │
│ msg-002: 0.7×1.000 + 0.3×0.442 = 0.833  (both, high semantic) │
│ msg-003: 0.7×0.000 + 0.3×0.000 = 0.000  (ES only, low)       │
│ msg-004: 0.7×0.600 + 0.3×0.000 = 0.420  (vector only)         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                    Sort by hybrid score
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Final Ranked Results                                            │
├─────────────────────────────────────────────────────────────────┤
│ 1. msg-002  Score: 0.833  "Budget Review Meeting"              │
│ 2. msg-004  Score: 0.420  "Budget Planning"                    │
│ 3. msg-001  Score: 0.300  "Q4 Financial Report"                │
│ 4. msg-003  Score: 0.000  "Expense Approval"                   │
└─────────────────────────────────────────────────────────────────┘
```

## Score Calculation Detail

### Example: msg-002 (appears in both sources)

```
┌─────────────────────────────────────────────────────────────┐
│ Elasticsearch Path                                          │
├─────────────────────────────────────────────────────────────┤
│ Raw BM25 Score:           14.2                             │
│ ES Scores Range:          [10.8, 14.2, 18.5]              │
│ Normalized (min-max):     (14.2-10.8)/(18.5-10.8) = 0.442 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Vector Database Path                                        │
├─────────────────────────────────────────────────────────────┤
│ Raw Distance:             0.08                             │
│ Similarity:               1 - 0.08 = 0.92                  │
│ Similarity Range:         [0.82, 0.88, 0.92]              │
│ Normalized (min-max):     (0.92-0.82)/(0.92-0.82) = 1.000 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Hybrid Combination (70/30 weighting)                       │
├─────────────────────────────────────────────────────────────┤
│ Semantic Component:       0.7 × 1.000 = 0.700             │
│ Keyword Component:        0.3 × 0.442 = 0.133             │
│ Final Hybrid Score:       0.700 + 0.133 = 0.833           │
└─────────────────────────────────────────────────────────────┘
```

## Deduplication Logic

```
┌────────────────────────────────────────────────────────────────┐
│ Before Deduplication                                           │
├────────────────────────────────────────────────────────────────┤
│ From ES:                     From Vector DB:                  │
│ - msg-001 (ES score: 1.0)    - msg-002 (Vec score: 1.0)      │
│ - msg-002 (ES score: 0.4)    - msg-001 (Vec score: 0.0)      │
│ - msg-003 (ES score: 0.0)    - msg-004 (Vec score: 0.6)      │
└────────────────────────────────────────────────────────────────┘
                            ↓
              Merge by ID, combine scores
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ After Deduplication                                            │
├────────────────────────────────────────────────────────────────┤
│ msg-001: ES=1.0, Vec=0.0  → Hybrid=0.7×0.0 + 0.3×1.0 = 0.30  │
│ msg-002: ES=0.4, Vec=1.0  → Hybrid=0.7×1.0 + 0.3×0.4 = 0.82  │
│ msg-003: ES=0.0, Vec=0.0  → Hybrid=0.7×0.0 + 0.3×0.0 = 0.00  │
│ msg-004: ES=0.0, Vec=0.6  → Hybrid=0.7×0.6 + 0.3×0.0 = 0.42  │
└────────────────────────────────────────────────────────────────┘
```

## Edge Case: Single Source Only

### Scenario A: Vector DB Results Only

```
┌────────────────────────────────────────────────────────────────┐
│ Input: ES Results = []  (empty)                                │
│        Vector Results = [msg-1, msg-2, msg-3]                  │
├────────────────────────────────────────────────────────────────┤
│ Processing:                                                    │
│ 1. Detect ES is empty                                          │
│ 2. Normalize vector scores to [0, 1]                          │
│ 3. Use normalized vector scores as hybrid_score               │
│ 4. Set es_norm_score = 0.0 for all                           │
├────────────────────────────────────────────────────────────────┤
│ Output:                                                        │
│ - msg-1: hybrid_score=1.0, vector_norm=1.0, es_norm=0.0      │
│ - msg-2: hybrid_score=0.5, vector_norm=0.5, es_norm=0.0      │
│ - msg-3: hybrid_score=0.0, vector_norm=0.0, es_norm=0.0      │
└────────────────────────────────────────────────────────────────┘
```

### Scenario B: Elasticsearch Results Only

```
┌────────────────────────────────────────────────────────────────┐
│ Input: ES Results = [msg-1, msg-2, msg-3]                      │
│        Vector Results = []  (empty)                            │
├────────────────────────────────────────────────────────────────┤
│ Processing:                                                    │
│ 1. Detect Vector DB is empty                                  │
│ 2. Normalize ES scores to [0, 1]                              │
│ 3. Use normalized ES scores as hybrid_score                   │
│ 4. Set vector_norm_score = 0.0 for all                       │
├────────────────────────────────────────────────────────────────┤
│ Output:                                                        │
│ - msg-1: hybrid_score=1.0, es_norm=1.0, vector_norm=0.0      │
│ - msg-2: hybrid_score=0.5, es_norm=0.5, vector_norm=0.0      │
│ - msg-3: hybrid_score=0.0, es_norm=0.0, vector_norm=0.0      │
└────────────────────────────────────────────────────────────────┘
```

## RRF (Reciprocal Rank Fusion) Method

```
Formula: score(doc) = Σ 1/(k + rank)

Example with k=60:

┌────────────────────────────────────────────────────────────────┐
│ Elasticsearch Rankings        Vector DB Rankings              │
├────────────────────────────────────────────────────────────────┤
│ 1. msg-A → 1/(60+1) = 0.0164  1. msg-B → 1/(60+1) = 0.0164   │
│ 2. msg-B → 1/(60+2) = 0.0161  2. msg-A → 1/(60+2) = 0.0161   │
│ 3. msg-C → 1/(60+3) = 0.0159  3. msg-D → 1/(60+3) = 0.0159   │
└────────────────────────────────────────────────────────────────┘
                            ↓
                    Sum scores per doc
                            ↓
┌────────────────────────────────────────────────────────────────┐
│ Final RRF Scores                                               │
├────────────────────────────────────────────────────────────────┤
│ msg-A: 0.0164 + 0.0161 = 0.0325  (in both, ranks 1 & 2)      │
│ msg-B: 0.0161 + 0.0164 = 0.0325  (in both, ranks 2 & 1)      │
│ msg-C: 0.0159 + 0.0000 = 0.0159  (ES only, rank 3)           │
│ msg-D: 0.0000 + 0.0159 = 0.0159  (Vector only, rank 3)       │
└────────────────────────────────────────────────────────────────┘
```

## Configuration Impact

### 70/30 Weighting (Default - Balanced)

```
Semantic: ████████████████████████████████████████████████████ 70%
Keyword:  █████████████████████ 30%

Best for: General purpose search, balanced precision/recall
```

### 90/10 Weighting (Semantic-Heavy)

```
Semantic: ██████████████████████████████████████████████████████████████████████ 90%
Keyword:  ███████ 10%

Best for: Conceptual queries, synonym matching, "emails about X"
```

### 30/70 Weighting (Keyword-Heavy)

```
Semantic: █████████████████████ 30%
Keyword:  ████████████████████████████████████████████████████ 70%

Best for: Exact term matching, IDs, names, technical terms
```

## Performance Flow

```
┌────────────────────────────────────────────────────────────────┐
│ Search Performance Breakdown (typical query)                   │
├────────────────────────────────────────────────────────────────┤
│ Elasticsearch Query:     30-50ms  ████████████████             │
│ Vector DB Query:         5-20ms   ████                         │
│ Hybrid Ranking:          <1ms     █                            │
│ Network/Serialization:   10-20ms  ████                         │
├────────────────────────────────────────────────────────────────┤
│ Total:                   50-100ms                              │
└────────────────────────────────────────────────────────────────┘
```
