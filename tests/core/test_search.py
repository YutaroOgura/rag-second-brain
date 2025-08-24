"""Tests for SearchEngine class."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from rag.core.search import SearchEngine


class TestSearchEngine:
    """Test cases for SearchEngine."""
    
    @pytest.fixture
    def mock_database(self):
        """Create mock database manager."""
        mock_db = Mock()
        mock_db.search.return_value = {
            "documents": [["認証システムについて説明します", "データベース設計について"]],
            "metadatas": [[{"project_id": "test", "category": "設計書"}, {"project_id": "test", "category": "実装"}]],
            "distances": [[0.2, 0.4]],
            "ids": [["doc1", "doc2"]]
        }
        return mock_db
    
    @pytest.fixture
    def mock_vectorizer(self):
        """Create mock vectorizer."""
        mock_vec = Mock()
        mock_vec.vectorize.return_value = np.array([0.1, 0.2, 0.3])
        return mock_vec
    
    @pytest.fixture
    def search_engine(self, mock_database, mock_vectorizer):
        """Create SearchEngine instance with mocks."""
        return SearchEngine(mock_database, mock_vectorizer)
    
    def test_init(self, mock_database, mock_vectorizer):
        """Test SearchEngine initialization."""
        engine = SearchEngine(mock_database, mock_vectorizer)
        
        assert engine.database == mock_database
        assert engine.vectorizer == mock_vectorizer
    
    def test_vector_search_success(self, search_engine, mock_database):
        """Test successful vector search."""
        query = "認証システム"
        top_k = 3
        
        results = search_engine.vector_search(query, top_k=top_k)
        
        # Verify database search was called correctly
        mock_database.search.assert_called_once_with(query, n_results=top_k, filters=None)
        
        # Check result format
        assert "results" in results
        assert len(results["results"]) == 2
        assert results["search_type"] == "vector"
        assert results["query"] == query
    
    def test_vector_search_with_filters(self, search_engine, mock_database):
        """Test vector search with metadata filters."""
        query = "設計書"
        filters = {"category": "設計書", "project_id": "test_project"}
        
        search_engine.vector_search(query, filters=filters)
        
        mock_database.search.assert_called_once_with(query, n_results=5, filters=filters)
    
    def test_vector_search_empty_query_raises_error(self, search_engine):
        """Test that empty query raises error."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            search_engine.vector_search("")
    
    def test_keyword_search_success(self, search_engine, mock_database):
        """Test successful keyword search."""
        query = "認証"
        
        # Mock database to return keyword search results
        mock_database.search.return_value = {
            "documents": [["認証システムの実装", "ユーザー認証について"]],
            "metadatas": [[{"project_id": "test"}, {"project_id": "test"}]],
            "distances": [[0.0, 0.0]],  # Exact matches have distance 0
            "ids": [["doc1", "doc2"]]
        }
        
        results = search_engine.keyword_search(query, top_k=3)
        
        assert "results" in results
        assert results["search_type"] == "keyword"
        assert results["query"] == query
    
    def test_hybrid_search_success(self, search_engine):
        """Test successful hybrid search."""
        query = "認証システム設計"
        
        with patch.object(search_engine, 'vector_search') as mock_vector_search, \
             patch.object(search_engine, 'keyword_search') as mock_keyword_search:
            
            # Mock vector search results
            mock_vector_search.return_value = {
                "results": [
                    {"text": "ベクトル検索結果1", "score": 0.9, "id": "vec1"},
                    {"text": "ベクトル検索結果2", "score": 0.8, "id": "vec2"}
                ]
            }
            
            # Mock keyword search results
            mock_keyword_search.return_value = {
                "results": [
                    {"text": "キーワード検索結果1", "score": 1.0, "id": "key1"},
                    {"text": "キーワード検索結果2", "score": 0.7, "id": "key2"}
                ]
            }
            
            results = search_engine.hybrid_search(query, alpha=0.5, top_k=3)
            
            # Verify both searches were called
            mock_vector_search.assert_called_once_with(query, top_k=10, filters=None)
            mock_keyword_search.assert_called_once_with(query, top_k=10, filters=None)
            
            # Check hybrid results
            assert "results" in results
            assert results["search_type"] == "hybrid"
            assert len(results["results"]) <= 3  # Should be limited to top_k
    
    def test_hybrid_search_alpha_weighting(self, search_engine):
        """Test hybrid search alpha weighting."""
        query = "テスト"
        
        with patch.object(search_engine, 'vector_search') as mock_vector_search, \
             patch.object(search_engine, 'keyword_search') as mock_keyword_search:
            
            mock_vector_search.return_value = {"results": [{"score": 0.8, "id": "v1"}]}
            mock_keyword_search.return_value = {"results": [{"score": 0.6, "id": "k1"}]}
            
            # Test with alpha=0.3 (30% keyword, 70% vector)
            search_engine.hybrid_search(query, alpha=0.3, top_k=5)
            
            # Verify calls
            mock_vector_search.assert_called_once()
            mock_keyword_search.assert_called_once()
    
    def test_format_results_success(self, search_engine):
        """Test result formatting."""
        chroma_results = {
            "documents": [["テストドキュメント1", "テストドキュメント2"]],
            "metadatas": [[{"project_id": "test", "file_path": "/test1.md"}, {"project_id": "test", "file_path": "/test2.md"}]],
            "distances": [[0.2, 0.4]],
            "ids": [["doc1", "doc2"]]
        }
        
        formatted = search_engine.format_results(chroma_results, "vector")
        
        assert "results" in formatted
        assert len(formatted["results"]) == 2
        
        # Check first result
        result1 = formatted["results"][0]
        assert result1["text"] == "テストドキュメント1"
        assert result1["score"] == 0.8  # 1 - 0.2 (distance to similarity)
        assert result1["metadata"]["project_id"] == "test"
        assert result1["id"] == "doc1"
    
    def test_format_results_empty(self, search_engine):
        """Test formatting empty results."""
        empty_results = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "ids": [[]]
        }
        
        formatted = search_engine.format_results(empty_results, "vector")
        
        assert formatted["results"] == []
        assert formatted["total_found"] == 0
    
    def test_calculate_hybrid_score(self, search_engine):
        """Test hybrid score calculation."""
        vector_score = 0.8
        keyword_score = 0.6
        alpha = 0.3  # 30% keyword, 70% vector
        
        hybrid_score = search_engine._calculate_hybrid_score(vector_score, keyword_score, alpha)
        
        expected = 0.3 * keyword_score + 0.7 * vector_score
        assert abs(hybrid_score - expected) < 0.001
    
    def test_search_with_project_filter(self, search_engine, mock_database):
        """Test search with project filter."""
        query = "テスト"
        project_id = "specific_project"
        
        search_engine.vector_search(query, project_id=project_id)
        
        # Should call database with project filter
        expected_filters = {"project_id": project_id}
        mock_database.search.assert_called_once_with(query, n_results=5, filters=expected_filters)
    
    def test_search_result_ranking(self, search_engine):
        """Test that search results are properly ranked by score."""
        chroma_results = {
            "documents": [["doc1", "doc2", "doc3"]],
            "metadatas": [[{}, {}, {}]],
            "distances": [[0.1, 0.3, 0.2]],  # Distances: low=good, high=bad
            "ids": [["id1", "id2", "id3"]]
        }
        
        formatted = search_engine.format_results(chroma_results, "vector")
        results = formatted["results"]
        
        # Should be ranked by score (high to low)
        assert results[0]["score"] > results[1]["score"] > results[2]["score"]
        assert results[0]["id"] == "id1"  # Best score (lowest distance)
        assert results[1]["id"] == "id3"  # Middle score
        assert results[2]["id"] == "id2"  # Worst score (highest distance)


class TestSearchEngineIntegration:
    """Integration tests for SearchEngine."""
    
    def test_with_real_components(self, test_database, test_vectorizer, sample_documents):
        """Test SearchEngine with real database and vectorizer."""
        # Add sample documents to database
        test_database.create_collection("test_docs")
        for doc in sample_documents:
            test_database.add_document(doc["text"], doc["metadata"], doc["id"])
        
        # Create search engine with real components
        search_engine = SearchEngine(test_database, test_vectorizer)
        
        # Test search
        results = search_engine.vector_search("認証システム", top_k=2)
        
        assert "results" in results
        assert len(results["results"]) > 0
        assert all("text" in result for result in results["results"])
        assert all("score" in result for result in results["results"])
    
    def test_end_to_end_search_pipeline(self, test_database, test_vectorizer):
        """Test complete search pipeline."""
        # Setup
        test_database.create_collection("pipeline_test")
        search_engine = SearchEngine(test_database, test_vectorizer)
        
        # Add documents
        docs = [
            {"text": "JWT認証システムの実装について", "metadata": {"type": "auth"}},
            {"text": "データベース設計の基本原則", "metadata": {"type": "db"}},
            {"text": "REST APIの設計方法", "metadata": {"type": "api"}}
        ]
        
        for i, doc in enumerate(docs):
            test_database.add_document(doc["text"], doc["metadata"], f"test_doc_{i}")
        
        # Test different search types
        vector_results = search_engine.vector_search("認証")
        keyword_results = search_engine.keyword_search("設計")
        hybrid_results = search_engine.hybrid_search("API実装")
        
        # All should return results
        assert len(vector_results["results"]) > 0
        assert len(keyword_results["results"]) > 0
        assert len(hybrid_results["results"]) > 0


@pytest.mark.slow
class TestSearchEnginePerformance:
    """Performance tests for SearchEngine."""
    
    def test_search_performance_with_many_documents(self, test_database, test_vectorizer):
        """Test search performance with many documents."""
        test_database.create_collection("perf_test")
        search_engine = SearchEngine(test_database, test_vectorizer)
        
        # Add many documents
        for i in range(100):
            text = f"テスト用ドキュメント {i} 認証とセキュリティについて説明します"
            metadata = {"index": i, "category": "test"}
            test_database.add_document(text, metadata, f"perf_doc_{i}")
        
        # Measure search time
        import time
        start_time = time.time()
        
        results = search_engine.vector_search("認証", top_k=10)
        
        search_time = time.time() - start_time
        
        # Should be reasonably fast
        assert search_time < 5.0  # 5 seconds max
        assert len(results["results"]) == 10
    
    def test_hybrid_search_efficiency(self, test_database, test_vectorizer):
        """Test hybrid search is reasonably efficient."""
        test_database.create_collection("hybrid_perf_test")
        search_engine = SearchEngine(test_database, test_vectorizer)
        
        # Add test documents
        for i in range(50):
            text = f"ハイブリッド検索テスト {i} システム設計とデータベース"
            test_database.add_document(text, {"index": i}, f"hybrid_doc_{i}")
        
        # Measure hybrid search time
        import time
        start_time = time.time()
        
        results = search_engine.hybrid_search("システム設計", top_k=5)
        
        search_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert search_time < 10.0  # 10 seconds max
        assert len(results["results"]) <= 5


class TestSearchEngineEdgeCases:
    """Test edge cases for SearchEngine."""
    
    def test_search_with_no_results(self, search_engine, mock_database):
        """Test search when no documents match."""
        mock_database.search.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "ids": [[]]
        }
        
        results = search_engine.vector_search("nonexistent_query")
        
        assert results["results"] == []
        assert results["total_found"] == 0
    
    def test_search_with_special_characters(self, search_engine):
        """Test search with special characters in query."""
        special_query = "!@#$%^&*()_+-={}[]|\\:;\"'<>?,./"
        
        # Should not raise exception
        results = search_engine.vector_search(special_query)
        assert "results" in results
    
    def test_search_with_very_long_query(self, search_engine):
        """Test search with extremely long query."""
        long_query = "検索クエリ " * 1000
        
        # Should handle gracefully
        results = search_engine.vector_search(long_query)
        assert "results" in results
    
    def test_hybrid_search_with_alpha_edge_values(self, search_engine):
        """Test hybrid search with alpha at edge values."""
        query = "テスト"
        
        with patch.object(search_engine, 'vector_search') as mock_vs, \
             patch.object(search_engine, 'keyword_search') as mock_ks:
            
            mock_vs.return_value = {"results": []}
            mock_ks.return_value = {"results": []}
            
            # Test alpha = 0 (pure vector)
            search_engine.hybrid_search(query, alpha=0.0)
            
            # Test alpha = 1 (pure keyword)  
            search_engine.hybrid_search(query, alpha=1.0)
            
            # Both should work without errors
            assert mock_vs.call_count == 2
            assert mock_ks.call_count == 2