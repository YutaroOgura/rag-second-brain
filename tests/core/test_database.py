"""Tests for DatabaseManager class."""

import pytest
from unittest.mock import Mock, patch
import tempfile
import shutil
from pathlib import Path

from rag.core.database import DatabaseManager


class TestDatabaseManager:
    """Test cases for DatabaseManager."""
    
    def test_init_creates_client(self, temp_data_dir):
        """Test that initialization creates ChromaDB client."""
        db_path = str(temp_data_dir / "test_chroma")
        db = DatabaseManager(db_path)
        
        assert db.client is not None
        assert db.path == db_path
        assert db.collection is None
    
    def test_create_collection_success(self, test_database):
        """Test successful collection creation."""
        collection_name = "test_collection"
        collection = test_database.create_collection(collection_name)
        
        assert collection is not None
        assert test_database.collection is not None
        assert test_database.collection.name == collection_name
    
    def test_create_collection_already_exists(self, test_database):
        """Test creating collection that already exists."""
        collection_name = "existing_collection"
        
        # Create collection first time
        collection1 = test_database.create_collection(collection_name)
        # Create same collection again
        collection2 = test_database.create_collection(collection_name)
        
        assert collection1.name == collection2.name
    
    def test_add_document_success(self, test_database, sample_documents):
        """Test successful document addition."""
        test_database.create_collection("test_docs")
        doc = sample_documents[0]
        
        doc_id = test_database.add_document(
            text=doc["text"],
            metadata=doc["metadata"],
            doc_id=doc["id"]
        )
        
        assert doc_id == doc["id"]
    
    def test_add_document_without_collection_raises_error(self, test_database):
        """Test that adding document without collection raises error."""
        with pytest.raises(ValueError, match="No collection"):
            test_database.add_document("test text", {})
    
    def test_add_document_generates_id_if_not_provided(self, test_database):
        """Test that document ID is generated if not provided."""
        test_database.create_collection("test_docs")
        
        doc_id = test_database.add_document("test text", {})
        
        assert doc_id is not None
        assert isinstance(doc_id, str)
        assert len(doc_id) > 0
    
    def test_search_success(self, test_database, sample_documents):
        """Test successful document search."""
        test_database.create_collection("test_docs")
        
        # Add sample documents
        for doc in sample_documents:
            test_database.add_document(doc["text"], doc["metadata"], doc["id"])
        
        results = test_database.search("認証", n_results=2)
        
        assert len(results) > 0
        assert "documents" in results
        assert "metadatas" in results
        assert "distances" in results
    
    def test_search_without_collection_raises_error(self, test_database):
        """Test that searching without collection raises error."""
        with pytest.raises(ValueError, match="No collection"):
            test_database.search("test query")
    
    def test_search_empty_query_raises_error(self, test_database):
        """Test that searching with empty query raises error."""
        test_database.create_collection("test_docs")
        
        with pytest.raises(ValueError, match="Query cannot be empty"):
            test_database.search("")
    
    def test_delete_document_success(self, test_database, sample_documents):
        """Test successful document deletion."""
        test_database.create_collection("test_docs")
        doc = sample_documents[0]
        
        # Add document
        test_database.add_document(doc["text"], doc["metadata"], doc["id"])
        
        # Delete document
        success = test_database.delete_document(doc["id"])
        
        assert success is True
    
    def test_delete_nonexistent_document(self, test_database):
        """Test deleting non-existent document."""
        test_database.create_collection("test_docs")
        
        success = test_database.delete_document("nonexistent_id")
        
        assert success is False
    
    def test_delete_document_without_collection_raises_error(self, test_database):
        """Test that deleting document without collection raises error."""
        with pytest.raises(ValueError, match="No collection"):
            test_database.delete_document("test_id")
    
    def test_list_documents(self, test_database, sample_documents):
        """Test listing all documents."""
        test_database.create_collection("test_docs")
        
        # Add sample documents
        for doc in sample_documents:
            test_database.add_document(doc["text"], doc["metadata"], doc["id"])
        
        documents = test_database.list_documents()
        
        assert len(documents) == len(sample_documents)
    
    def test_get_collection_info(self, test_database, sample_documents):
        """Test getting collection information."""
        collection_name = "test_docs"
        test_database.create_collection(collection_name)
        
        # Add sample documents
        for doc in sample_documents:
            test_database.add_document(doc["text"], doc["metadata"], doc["id"])
        
        info = test_database.get_collection_info()
        
        assert info["name"] == collection_name
        assert info["count"] == len(sample_documents)
    
    def test_filter_by_metadata(self, test_database, sample_documents):
        """Test filtering documents by metadata."""
        test_database.create_collection("test_docs")
        
        # Add sample documents
        for doc in sample_documents:
            test_database.add_document(doc["text"], doc["metadata"], doc["id"])
        
        # Filter by category
        results = test_database.search(
            query="設計",
            filters={"category": "設計書"},
            n_results=10
        )
        
        assert len(results["documents"][0]) >= 2  # Should find at least 2 design docs
    
    def test_update_document(self, test_database, sample_documents):
        """Test updating an existing document."""
        test_database.create_collection("test_docs")
        doc = sample_documents[0]
        
        # Add original document
        test_database.add_document(doc["text"], doc["metadata"], doc["id"])
        
        # Update document
        updated_text = "更新されたテキスト"
        updated_metadata = {**doc["metadata"], "updated": True}
        
        success = test_database.update_document(
            doc_id=doc["id"],
            text=updated_text,
            metadata=updated_metadata
        )
        
        assert success is True


@pytest.mark.integration
class TestDatabaseManagerIntegration:
    """Integration tests for DatabaseManager."""
    
    def test_real_chromadb_operations(self):
        """Test actual ChromaDB operations with real data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db = DatabaseManager(temp_dir)
            collection = db.create_collection("integration_test")
            
            # Add document
            doc_id = db.add_document(
                text="これは統合テスト用のドキュメントです",
                metadata={"test": True, "type": "integration"}
            )
            
            # Search document
            results = db.search("統合テスト")
            
            assert len(results["documents"][0]) > 0
            assert results["metadatas"][0][0]["test"] is True
            
            # Clean up
            db.delete_document(doc_id)


@pytest.mark.slow
class TestDatabaseManagerPerformance:
    """Performance tests for DatabaseManager."""
    
    def test_bulk_document_insertion(self, test_database):
        """Test inserting many documents."""
        test_database.create_collection("perf_test")
        
        # Generate test documents
        documents = [
            {
                "text": f"テストドキュメント {i} の内容です",
                "metadata": {"index": i, "type": "performance_test"}
            }
            for i in range(100)
        ]
        
        # Measure insertion time
        import time
        start_time = time.time()
        
        for i, doc in enumerate(documents):
            test_database.add_document(doc["text"], doc["metadata"], f"perf_doc_{i}")
        
        end_time = time.time()
        insertion_time = end_time - start_time
        
        # Should be able to insert 100 documents reasonably quickly
        assert insertion_time < 30.0  # 30 seconds limit
        
        # Verify all documents were inserted
        info = test_database.get_collection_info()
        assert info["count"] == 100
    
    def test_search_performance(self, test_database):
        """Test search performance with many documents."""
        test_database.create_collection("search_perf_test")
        
        # Add test documents
        for i in range(50):
            test_database.add_document(
                text=f"検索用テストドキュメント {i} です。認証とデータベースについて説明します。",
                metadata={"index": i},
                doc_id=f"search_doc_{i}"
            )
        
        # Measure search time
        import time
        start_time = time.time()
        
        results = test_database.search("認証", n_results=10)
        
        end_time = time.time()
        search_time = end_time - start_time
        
        # Search should be fast
        assert search_time < 2.0  # 2 seconds limit
        assert len(results["documents"][0]) > 0