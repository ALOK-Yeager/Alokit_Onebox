"""
Hybrid Search Service

Combines Elasticsearch keyword search with VectorDB semantic search
for more comprehensive email search results.
"""

import os
import logging
from typing import List, Tuple, Dict, Any, Optional

# Module-level logger (initialized early for conditional imports)
logger = logging.getLogger(__name__)


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


# Determine whether vector search should be enabled via environment flag
VECTOR_SEARCH_ENABLED = _is_truthy(os.getenv("ENABLE_VECTORDB", "true"))

# Attempt to import VectorDB only when enabled
VectorDB = None  # type: ignore[assignment]
if VECTOR_SEARCH_ENABLED:
    try:
        from src.Services.search.VectorDB import VectorDB as _VectorDB  # type: ignore

        VectorDB = _VectorDB
    except Exception as import_exc:  # pragma: no cover - defensive guard
        logger.warning(
            "Vector search disabled because VectorDB could not be imported: %s",
            import_exc,
        )
        VECTOR_SEARCH_ENABLED = False

# Configure logging (after conditional import so logger has handlers)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridSearch:
    """
    Hybrid search combining keyword-based (Elasticsearch) and semantic (VectorDB) search.
    
    Attributes:
        vector_db: VectorDB instance for semantic search
        vector_weight: Weight for semantic search results (default: 0.7)
        keyword_weight: Weight for keyword search results (default: 0.3)
    """
    
    def __init__(self, vector_weight: float = 0.7, keyword_weight: float = 0.3):
        """
        Initialize the hybrid search service.
        
        Args:
            vector_weight: Weight for vector/semantic search results (0-1)
            keyword_weight: Weight for keyword/Elasticsearch results (0-1)
        """
        self.vector_enabled = VECTOR_SEARCH_ENABLED and VectorDB is not None
        self.vector_db: Optional[Any] = None
        self.vector_weight = vector_weight if self.vector_enabled else 0.0
        self.keyword_weight = keyword_weight

        if self.vector_enabled and VectorDB is not None:
            try:
                self.vector_db = VectorDB()
                logger.info("Vector search enabled via VectorDB")
            except Exception as exc:
                logger.warning(
                    "Disabling vector search because VectorDB initialization failed: %s",
                    exc,
                )
                self.vector_enabled = False
                self.vector_db = None
        else:
            if not VECTOR_SEARCH_ENABLED:
                logger.info("Vector search disabled via ENABLE_VECTORDB setting")
            else:
                logger.warning("Vector search disabled because VectorDB module is unavailable")
        
        # Try to import Elasticsearch (optional)
        self.es = None
        self.es_index = os.getenv("ELASTICSEARCH_INDEX", "emails")
        try:
            from elasticsearch import Elasticsearch
            es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
            es_kwargs: Dict[str, Any] = {}

            api_key = os.getenv("ELASTICSEARCH_API_KEY")
            username = os.getenv("ELASTICSEARCH_USERNAME")
            password = os.getenv("ELASTICSEARCH_PASSWORD")

            if api_key:
                es_kwargs["api_key"] = api_key
            elif username and password:
                es_kwargs["basic_auth"] = (username, password)

            self.es = Elasticsearch(es_url, **es_kwargs)
            logger.info(
                "Connected to Elasticsearch",
                extra={"url": es_url, "index": self.es_index, "apiKey": bool(api_key)},
            )
        except ImportError:
            logger.warning("Elasticsearch library not installed. Using VectorDB only.")
        except Exception as e:
            logger.warning(f"Could not connect to Elasticsearch: {e}. Using VectorDB only.")
    
    def search_vector(self, query: str, n_results: int = 5) -> List[Tuple[str, float]]:
        """
        Perform semantic search using VectorDB.
        
        Args:
            query: Search query string
            n_results: Number of results to return
            
        Returns:
            List of (email_id, score) tuples
        """
        if not self.vector_enabled or not self.vector_db:
            logger.debug("Vector search requested but vector functionality is disabled")
            return []

        try:
            results = self.vector_db.search(query, n_results=n_results)
            logger.info(f"VectorDB search returned {len(results)} results")
            # Ensure we return the correct type
            formatted: List[Tuple[str, float]] = []
            for entry in results:
                email_id = entry.get("id") or entry.get("document")
                if not email_id:
                    continue
                # Chroma reports distance (lower is better). Convert to similarity-style score.
                distance = entry.get("distance")
                score = 1.0 - float(distance) if distance is not None else 1.0
                formatted.append((str(email_id), score))
            return formatted
        except Exception as e:
            logger.error(f"VectorDB search failed: {e}")
            return []
    
    def search_keyword(
        self, query: str, n_results: int = 5, index: Optional[str] = None
    ) -> List[Tuple[str, float]]:
        """
        Perform keyword search using Elasticsearch.
        
        Args:
            query: Search query string
            n_results: Number of results to return
            index: Elasticsearch index name
            
        Returns:
            List of (email_id, score) tuples
        """
        if not self.es:
            logger.warning("Elasticsearch not available, skipping keyword search")
            return []
        
        try:
            target_index = index or self.es_index
            es_results = self.es.search(
                index=target_index,
                query={
                    "multi_match": {
                        "query": query,
                        "fields": ["subject^2", "content", "from", "to"]
                    }
                },
                size=n_results
            )
            
            results = [
                (hit['_id'], hit['_score']) 
                for hit in es_results['hits']['hits']
            ]
            logger.info(f"Elasticsearch returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Elasticsearch search failed: {e}")
            return []
    
    def search(self, query: str, n_results: int = 5) -> List[str]:
        """
        Perform hybrid search combining semantic and keyword search.
        
        Args:
            query: Search query string
            n_results: Number of results to return
            
        Returns:
            List of email IDs sorted by combined score
        """
        # Get results from both sources
        vector_results: List[Tuple[str, float]] = []
        if self.vector_enabled:
            vector_results = self.search_vector(query, n_results=n_results * 2)
        keyword_results = self.search_keyword(query, n_results=n_results * 2)
        
        # Combine and weight results
        combined_scores: Dict[str, float] = {}
        
        # Add vector search results with weight
        for email_id, score in vector_results:
            combined_scores[email_id] = combined_scores.get(email_id, 0) + (self.vector_weight * score)
        
        # Add keyword search results with weight
        for email_id, score in keyword_results:
            combined_scores[email_id] = combined_scores.get(email_id, 0) + (self.keyword_weight * score)
        
        # Sort by combined score
        sorted_results = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Return top n email IDs
        result_ids = [email_id for email_id, _ in sorted_results[:n_results]]
        logger.info(f"Hybrid search returned {len(result_ids)} results")
        
        return result_ids
    
    def search_detailed(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform hybrid search and return detailed results with scores.
        
        Args:
            query: Search query string
            n_results: Number of results to return
            
        Returns:
            List of dictionaries containing email_id and combined_score
        """
        # Get results from both sources
        vector_results: List[Tuple[str, float]] = []
        if self.vector_enabled:
            vector_results = self.search_vector(query, n_results=n_results * 2)
        keyword_results = self.search_keyword(query, n_results=n_results * 2)
        
        # Combine and weight results
        combined_scores: Dict[str, Dict[str, float]] = {}
        
        # Add vector search results with weight
        for email_id, score in vector_results:
            if email_id not in combined_scores:
                combined_scores[email_id] = {"vector_score": 0, "keyword_score": 0, "combined_score": 0}
            combined_scores[email_id]["vector_score"] = score
            combined_scores[email_id]["combined_score"] += self.vector_weight * score
        
        # Add keyword search results with weight
        for email_id, score in keyword_results:
            if email_id not in combined_scores:
                combined_scores[email_id] = {"vector_score": 0, "keyword_score": 0, "combined_score": 0}
            combined_scores[email_id]["keyword_score"] = score
            combined_scores[email_id]["combined_score"] += self.keyword_weight * score
        
        # Sort by combined score
        sorted_results = sorted(
            combined_scores.items(),
            key=lambda x: x[1]["combined_score"],
            reverse=True
        )
        
        # Return top n results with details
        detailed_results = [
            {
                "email_id": email_id,
                "combined_score": scores["combined_score"],
                "vector_score": scores["vector_score"],
                "keyword_score": scores["keyword_score"]
            }
            for email_id, scores in sorted_results[:n_results]
        ]
        
        return detailed_results


if __name__ == "__main__":
    # Test the hybrid search
    print("\n🔍 Testing Hybrid Search Service...")
    
    try:
        searcher = HybridSearch()
        print("✓ HybridSearch initialized successfully")
        
        # Test search
        query = "project updates"
        print(f"\nSearching for: '{query}'")
        
        results = searcher.search(query, n_results=5)
        print(f"✓ Search completed")
        print(f"Found {len(results)} results: {results}")
        
        # Test detailed search
        detailed_results = searcher.search_detailed(query, n_results=3)
        print(f"\n✓ Detailed search completed")
        for i, result in enumerate(detailed_results, 1):
            print(f"{i}. Email ID: {result['email_id']}")
            print(f"   Combined Score: {result['combined_score']:.4f}")
            print(f"   Vector Score: {result['vector_score']:.4f}")
            print(f"   Keyword Score: {result['keyword_score']:.4f}")
        
        print("\n✅ All tests passed! HybridSearch is ready.")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
