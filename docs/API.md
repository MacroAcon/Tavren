# Tavren API Documentation

## Advanced Search Endpoints

### Hybrid Search

**Endpoint:** `POST /api/embeddings/hybrid-search`

**Description:** Performs a combined search that balances semantic understanding with keyword precision for better results.

**Request Parameters:**
```json
{
  "query_text": "User health data showing abnormal heart rate",
  "semantic_weight": 0.7,
  "keyword_weight": 0.3,
  "embedding_type": "content",
  "top_k": 5,
  "use_nvidia_api": true,
  "filter_metadata": {"data_type": "health"}
}
```

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| query_text | string | The text query to search for | Yes |
| semantic_weight | float | Weight for semantic search results (0-1) | No (default: 0.7) |
| keyword_weight | float | Weight for keyword search results (0-1) | No (default: 0.3) |
| embedding_type | string | Type of embedding to search in | No |
| top_k | integer | Number of results to return | No (default: from settings) |
| use_nvidia_api | boolean | Whether to use Nvidia API for encoding | No (default: true) |
| filter_metadata | object | Metadata filters to apply to the search | No |

**Response:**
```json
{
  "query": "User health data showing abnormal heart rate",
  "results": [
    {
      "id": 123,
      "package_id": "pkg_abc123",
      "embedding_type": "content_chunk_0",
      "text_content": "Heart rate readings show several periods of abnormal rhythm...",
      "metadata": {
        "chunk_index": 0,
        "data_type": "health"
      },
      "semantic_score": 0.85,
      "keyword_score": 0.92,
      "combined_score": 0.87
    },
    // More results...
  ],
  "count": 5,
  "semantic_weight": 0.7,
  "keyword_weight": 0.3,
  "search_type": "hybrid"
}
```

### Cross-Package Context Assembly

**Endpoint:** `POST /api/embeddings/cross-package-context`

**Description:** Provides richer context by retrieving information from different data packages and combining them based on relevance.

**Request Parameters:**
```json
{
  "query_text": "How does the user's exercise impact their sleep patterns?",
  "max_packages": 3,
  "max_items_per_package": 3,
  "max_tokens": 2000,
  "use_hybrid_search": true,
  "semantic_weight": 0.7,
  "keyword_weight": 0.3
}
```

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| query_text | string | The text query to search for | Yes |
| max_packages | integer | Maximum number of packages to include | No (default: 5) |
| max_items_per_package | integer | Maximum items to include per package | No (default: 3) |
| max_tokens | integer | Maximum tokens for the final context | No (default: 2000) |
| use_hybrid_search | boolean | Whether to use hybrid search or vector search | No (default: true) |
| semantic_weight | float | Weight for semantic results in hybrid search | No (default: 0.7) |
| keyword_weight | float | Weight for keyword results in hybrid search | No (default: 0.3) |

**Response:**
```json
{
  "query": "How does the user's exercise impact their sleep patterns?",
  "context": "=== Package: Health Data (ID: pkg_health123) ===\nType: health\n\n--- Item 1 (Relevance: 0.8761) ---\nSleep tracking data shows the user averaging 7.2 hours per night...\n\n=== Package: Fitness Data (ID: pkg_fitness456) ===\nType: fitness\n\n--- Item 1 (Relevance: 0.8523) ---\nUser exercise records show consistent running activity...",
  "package_count": 2,
  "item_count": 5,
  "token_count": 542,
  "latency_ms": 328.45,
  "packages": [
    {
      "id": "pkg_health123",
      "name": "Health Data",
      "item_count": 3
    },
    {
      "id": "pkg_fitness456",
      "name": "Fitness Data",
      "item_count": 2
    }
  ],
  "search_type": "hybrid",
  "timestamp": "2023-07-15T14:32:24.123Z"
}
```

### Query Expansion Search

**Endpoint:** `POST /api/embeddings/query-expansion`

**Description:** Improves recall for queries by generating alternative phrasings and combining the results.

**Request Parameters:**
```json
{
  "query_text": "How much did the user exercise last month?",
  "top_k": 5,
  "use_hybrid_search": true,
  "max_expansions": 3,
  "expansion_model": "gpt-3.5-turbo"
}
```

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| query_text | string | The original text query | Yes |
| top_k | integer | Number of results to return | No (default: from settings) |
| use_hybrid_search | boolean | Whether to use hybrid search or vector search | No (default: true) |
| max_expansions | integer | Maximum number of expanded queries to generate | No (default: 3) |
| expansion_model | string | Model to use for query expansion | No (default: "gpt-3.5-turbo") |

**Response:**
```json
{
  "original_query": "How much did the user exercise last month?",
  "expanded_queries": [
    "How much did the user exercise last month?",
    "What was the user's exercise routine in the previous month?",
    "Frequency and duration of user's physical activity last month",
    "User's workout statistics from the past 30 days"
  ],
  "results": [
    {
      "id": 234,
      "package_id": "pkg_fitness456",
      "embedding_type": "content_chunk_2",
      "text_content": "Monthly exercise summary: user completed 18 workouts totaling 842 minutes...",
      "metadata": {
        "chunk_index": 2,
        "data_type": "fitness"
      },
      "original_score": 0.79,
      "boosted_score": 0.87,
      "query_count": 3
    },
    // More results...
  ],
  "result_count": 5,
  "latency_ms": 487.12,
  "search_type": "query_expansion",
  "timestamp": "2023-07-15T14:35:18.456Z"
}
```

### Faceted Search

**Endpoint:** `POST /api/embeddings/faceted-search`

**Description:** Allows structured information retrieval by filtering and grouping results based on metadata facets while maintaining semantic relevance.

**Request Parameters:**
```json
{
  "query_text": "User fitness activity data",
  "facets": {
    "data_type": ["fitness", "health"],
    "activity_type": ["running", "cycling"]
  },
  "facet_weights": {
    "data_type": 0.6,
    "activity_type": 0.4
  },
  "use_hybrid_search": true,
  "top_k": 10
}
```

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| query_text | string | The text query to search for | Yes |
| facets | object | Dict of facet names to list of values to include | Yes |
| facet_weights | object | Weights for each facet (higher = more important) | No |
| use_hybrid_search | boolean | Whether to use hybrid search or vector search | No (default: true) |
| top_k | integer | Number of results to return | No (default: from settings) |

**Response:**
```json
{
  "query": "User fitness activity data",
  "facets": {
    "data_type": ["fitness", "health"],
    "activity_type": ["running", "cycling"]
  },
  "facet_weights": {
    "data_type": 0.6,
    "activity_type": 0.4
  },
  "results": [
    {
      "id": 345,
      "package_id": "pkg_fitness789",
      "embedding_type": "content_chunk_1",
      "text_content": "Running activity recorded on Tuesday: 5.2 miles, 42 minutes, average heart rate 142 bpm...",
      "metadata": {
        "data_type": "fitness",
        "activity_type": "running"
      },
      "facet_match_score": 1.0,
      "matched_facets": 2,
      "original_score": 0.83,
      "faceted_score": 0.88
    },
    // More results...
  ],
  "facet_groups": {
    "data_type": {
      "fitness": [
        // Results with data_type=fitness
      ],
      "health": [
        // Results with data_type=health
      ]
    },
    "activity_type": {
      "running": [
        // Results with activity_type=running
      ],
      "cycling": [
        // Results with activity_type=cycling
      ]
    }
  },
  "result_count": 10,
  "latency_ms": 356.78,
  "search_type": "faceted",
  "use_hybrid_search": true,
  "timestamp": "2023-07-15T14:40:52.789Z"
}
``` 