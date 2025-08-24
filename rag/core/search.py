"""Search engine for RAG system supporting vector, keyword, and hybrid search."""

import logging
import re
from typing import Dict, List, Any, Optional, Union
import numpy as np

from .database import DatabaseManager
from .vectorizer import Vectorizer

logger = logging.getLogger(__name__)


class SearchEngine:
    """Handles different types of search operations for the RAG system."""
    
    def __init__(self, database: DatabaseManager, vectorizer: Vectorizer):
        """Initialize search engine with database and vectorizer.
        
        Args:
            database: Database manager instance
            vectorizer: Vectorizer instance for text embedding
        """
        self.database = database
        self.vectorizer = vectorizer
        
        logger.info("SearchEngine initialized")
    
    def vector_search(
        self,
        query: str,
        top_k: int = 5,
        project_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform vector-based semantic search.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            project_id: Optional project ID filter
            filters: Optional metadata filters
            
        Returns:
            Dictionary with search results
            
        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        try:
            # Combine filters
            combined_filters = filters or {}
            if project_id:
                combined_filters["project_id"] = project_id
            
            # Use database's search method which handles vectorization internally
            chroma_results = self.database.search(
                query=query,
                n_results=top_k,
                filters=combined_filters if combined_filters else None
            )
            
            # Format results
            formatted_results = self.format_results(chroma_results, "vector")
            formatted_results["query"] = query
            
            logger.debug(f"Vector search completed: {len(formatted_results['results'])} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Vector search failed for query '{query}': {e}")
            raise
    
    def keyword_search(
        self,
        query: str,
        top_k: int = 5,
        project_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform keyword-based search.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            project_id: Optional project ID filter
            filters: Optional metadata filters
            
        Returns:
            Dictionary with search results
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        try:
            # For keyword search, we'll use a different approach
            # Get all documents and filter based on keyword matching
            combined_filters = filters or {}
            if project_id:
                combined_filters["project_id"] = project_id
            
            # Use database search but with keyword-optimized query
            # This is a simplified approach - in a real system you might use
            # a dedicated text search engine like Elasticsearch
            chroma_results = self.database.search(
                query=query,
                n_results=top_k * 2,  # Get more results for keyword filtering
                filters=combined_filters if combined_filters else None
            )
            
            # Filter results based on keyword matching
            filtered_results = self._filter_by_keywords(chroma_results, query)
            
            # Format results
            formatted_results = self.format_results(filtered_results, "keyword")
            formatted_results["query"] = query
            
            # Limit to top_k
            formatted_results["results"] = formatted_results["results"][:top_k]
            formatted_results["total_found"] = len(formatted_results["results"])
            
            logger.debug(f"Keyword search completed: {len(formatted_results['results'])} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Keyword search failed for query '{query}': {e}")
            raise
    
    def hybrid_search(
        self,
        query: str,
        alpha: float = 0.5,
        top_k: int = 5,
        project_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform hybrid search combining vector and keyword search.
        
        Args:
            query: Search query text
            alpha: Weight for keyword search (0.0 = pure vector, 1.0 = pure keyword)
            top_k: Number of results to return
            project_id: Optional project ID filter
            filters: Optional metadata filters
            
        Returns:
            Dictionary with search results
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        try:
            # Get more results from each search for better hybrid ranking
            search_k = min(top_k * 2, 10)
            
            # Perform both searches
            vector_results = self.vector_search(
                query, top_k=search_k, project_id=project_id, filters=filters
            )
            keyword_results = self.keyword_search(
                query, top_k=search_k, project_id=project_id, filters=filters
            )
            
            # Combine and re-rank results
            combined_results = self._combine_search_results(
                vector_results["results"],
                keyword_results["results"],
                alpha
            )
            
            # Sort by hybrid score and limit to top_k
            combined_results.sort(key=lambda x: x["score"], reverse=True)
            final_results = combined_results[:top_k]
            
            return {
                "results": final_results,
                "total_found": len(final_results),
                "search_type": "hybrid",
                "query": query,
                "alpha": alpha
            }
            
        except Exception as e:
            logger.error(f"Hybrid search failed for query '{query}': {e}")
            raise
    
    def format_results(
        self, 
        chroma_results: Dict[str, List], 
        search_type: str
    ) -> Dict[str, Any]:
        """Format ChromaDB results into standardized format.
        
        Args:
            chroma_results: Results from ChromaDB
            search_type: Type of search performed
            
        Returns:
            Formatted results dictionary
        """
        if not chroma_results["documents"][0]:
            return {
                "results": [],
                "total_found": 0,
                "search_type": search_type
            }
        
        results = []
        documents = chroma_results["documents"][0]
        metadatas = chroma_results["metadatas"][0]
        distances = chroma_results["distances"][0]
        ids = chroma_results["ids"][0]
        
        for i, (doc, metadata, distance, doc_id) in enumerate(
            zip(documents, metadatas, distances, ids)
        ):
            # Convert distance to similarity score (0-1, higher is better)
            score = max(0.0, 1.0 - distance)
            
            result = {
                "text": doc,
                "score": score,
                "metadata": metadata or {},
                "id": doc_id,
                "rank": i + 1
            }
            results.append(result)
        
        return {
            "results": results,
            "total_found": len(results),
            "search_type": search_type
        }
    
    def _filter_by_keywords(
        self, 
        chroma_results: Dict[str, List], 
        query: str
    ) -> Dict[str, List]:
        """Filter ChromaDB results by keyword matching.
        
        Args:
            chroma_results: Raw ChromaDB results
            query: Search query for keyword matching
            
        Returns:
            Filtered ChromaDB results
        """
        if not chroma_results["documents"][0]:
            return chroma_results
        
        # Extract keywords from query
        keywords = self._extract_keywords(query)
        if not keywords:
            return chroma_results
        
        # Filter documents that contain keywords
        filtered_docs = []
        filtered_metadatas = []
        filtered_distances = []
        filtered_ids = []
        
        documents = chroma_results["documents"][0]
        metadatas = chroma_results["metadatas"][0]
        distances = chroma_results["distances"][0]
        ids = chroma_results["ids"][0]
        
        for doc, metadata, distance, doc_id in zip(documents, metadatas, distances, ids):
            if self._contains_keywords(doc, keywords):
                filtered_docs.append(doc)
                filtered_metadatas.append(metadata)
                # For keyword search, assign distance based on keyword relevance
                keyword_score = self._calculate_keyword_score(doc, keywords)
                filtered_distances.append(1.0 - keyword_score)  # Convert to distance
                filtered_ids.append(doc_id)
        
        return {
            "documents": [filtered_docs],
            "metadatas": [filtered_metadatas],
            "distances": [filtered_distances],
            "ids": [filtered_ids]
        }
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from search query.
        
        Args:
            query: Search query string
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction - split by whitespace and remove short words
        words = query.strip().split()
        keywords = [word for word in words if len(word) > 1]
        return keywords
    
    def _contains_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the keywords.
        
        Args:
            text: Text to search in
            keywords: List of keywords to search for
            
        Returns:
            True if text contains at least one keyword
        """
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def _calculate_keyword_score(self, text: str, keywords: List[str]) -> float:
        """Calculate keyword relevance score for text.
        
        Args:
            text: Text to score
            keywords: List of keywords
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not keywords:
            return 0.0
        
        text_lower = text.lower()
        matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
        
        # Calculate score based on keyword match ratio
        score = matches / len(keywords)
        
        # Boost score for exact phrase matches
        full_query = " ".join(keywords).lower()
        if full_query in text_lower:
            score = min(1.0, score + 0.3)
        
        return score
    
    def _combine_search_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        alpha: float
    ) -> List[Dict[str, Any]]:
        """Combine vector and keyword search results.
        
        Args:
            vector_results: Results from vector search
            keyword_results: Results from keyword search
            alpha: Weight for keyword search (0.0-1.0)
            
        Returns:
            Combined results with hybrid scores
        """
        # Create dictionaries for quick lookup
        vector_dict = {result["id"]: result for result in vector_results}
        keyword_dict = {result["id"]: result for result in keyword_results}
        
        # Get all unique document IDs
        all_ids = set(vector_dict.keys()) | set(keyword_dict.keys())
        
        combined = []
        for doc_id in all_ids:
            vector_result = vector_dict.get(doc_id)
            keyword_result = keyword_dict.get(doc_id)
            
            # Calculate hybrid score
            vector_score = vector_result["score"] if vector_result else 0.0
            keyword_score = keyword_result["score"] if keyword_result else 0.0
            
            hybrid_score = self._calculate_hybrid_score(vector_score, keyword_score, alpha)
            
            # Use the result with better information (prefer vector for metadata)
            base_result = vector_result or keyword_result
            
            # Create combined result
            combined_result = {
                **base_result,
                "score": hybrid_score,
                "vector_score": vector_score,
                "keyword_score": keyword_score
            }
            
            combined.append(combined_result)
        
        return combined
    
    def _calculate_hybrid_score(
        self,
        vector_score: float,
        keyword_score: float,
        alpha: float
    ) -> float:
        """Calculate hybrid score from vector and keyword scores.
        
        Args:
            vector_score: Score from vector search (0.0-1.0)
            keyword_score: Score from keyword search (0.0-1.0)
            alpha: Weight for keyword search (0.0-1.0)
            
        Returns:
            Hybrid score (0.0-1.0)
        """
        return alpha * keyword_score + (1.0 - alpha) * vector_score
    
    def suggest_similar_queries(self, query: str, limit: int = 5) -> List[str]:
        """Suggest similar queries based on existing documents.
        
        Args:
            query: Original search query
            limit: Number of suggestions to return
            
        Returns:
            List of suggested queries
        """
        try:
            # Get some search results to analyze
            results = self.vector_search(query, top_k=limit * 2)
            
            suggestions = []
            for result in results["results"][:limit]:
                # Extract potential query terms from document text
                text = result["text"]
                words = text.split()
                
                # Find meaningful phrases (2-3 words)
                for i in range(len(words) - 1):
                    phrase = " ".join(words[i:i+2])
                    if len(phrase) > 5 and phrase.lower() != query.lower():
                        suggestions.append(phrase)
                        if len(suggestions) >= limit:
                            break
                
                if len(suggestions) >= limit:
                    break
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Failed to generate query suggestions: {e}")
            return []
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """Get search engine statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            # Get database info
            db_info = self.database.get_collection_info()
            
            # Get vectorizer info
            vectorizer_info = self.vectorizer.get_model_info()
            
            return {
                "database": {
                    "collection_name": db_info.get("name"),
                    "document_count": db_info.get("count", 0),
                    "collection_metadata": db_info.get("metadata", {})
                },
                "vectorizer": {
                    "model_name": vectorizer_info.get("model_name"),
                    "embedding_dimension": vectorizer_info.get("embedding_dimension"),
                    "device": vectorizer_info.get("device")
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get search statistics: {e}")
            return {"error": str(e)}