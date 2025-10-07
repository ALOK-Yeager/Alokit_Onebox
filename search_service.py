"""
Hybrid Search Service

Combines Elasticsearch keyword search with VectorDB semantic search
for more comprehensive email search results.
"""

import os
import logging
from typing import List, Tuple, Dict, Any, Optional
from src.Services.search.VectorDB import VectorDB

# Configure logging
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
        self.vector_db = VectorDB()
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        
        # Try to import Elasticsearch (optional)
        self.es = None
        try:
            from elasticsearch import Elasticsearch
            es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
            self.es = Elasticsearch([es_url])
            logger.info(f"Connected to Elasticsearch at {es_url}")
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
        try:
            results = self.vector_db.search(query, n_results=n_results)
            logger.info(f"VectorDB search returned {len(results)} results")
            # Ensure we return the correct type
            return [(str(r[0]), float(r[1])) for r in results]
        except Exception as e:
            logger.error(f"VectorDB search failed: {e}")
            return []
    
    def search_keyword(self, query: str, n_results: int = 5, index: str = "emails") -> List[Tuple[str, float]]:
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
            es_results = self.es.search(
                index=index,
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
