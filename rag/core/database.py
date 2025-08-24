"""Database management using ChromaDB for vector storage and retrieval."""

import hashlib
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages ChromaDB operations for document storage and retrieval."""
    
    def __init__(self, path: str = "./data/chroma"):
        """Initialize database manager.
        
        Args:
            path: Path to ChromaDB persistent storage
        """
        # Expand user home directory
        import os
        self.path = os.path.expanduser(path)
        self.collection = None
        
        try:
            # Create ChromaDB client with persistent storage
            self.client = chromadb.PersistentClient(
                path=self.path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            logger.info(f"ChromaDB client initialized at {path}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def create_collection(self, name: str = "documents") -> chromadb.Collection:
        """Create or get existing collection.
        
        Args:
            name: Collection name
            
        Returns:
            ChromaDB collection instance
        """
        try:
            # Try to get existing collection first
            self.collection = self.client.get_collection(name)
            logger.info(f"Retrieved existing collection: {name}")
        except Exception:
            # Collection doesn't exist, create new one
            try:
                self.collection = self.client.create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"}  # Use cosine similarity
                )
                logger.info(f"Created new collection: {name}")
            except Exception as e:
                logger.error(f"Failed to create/get collection {name}: {e}")
                raise
        
        return self.collection
    
    def add_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> str:
        """Add document to collection.
        
        Args:
            text: Document text content
            metadata: Document metadata
            doc_id: Optional document ID (generated if not provided)
            
        Returns:
            Document ID
            
        Raises:
            ValueError: If no collection exists or text is empty
        """
        if not self.collection:
            raise ValueError("No collection available. Call create_collection() first.")
        
        if not text or not text.strip():
            raise ValueError("Document text cannot be empty")
        
        # Generate ID if not provided
        if not doc_id:
            doc_id = f"doc_{hashlib.md5(text.encode()).hexdigest()[:16]}"
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        # Add timestamp
        from datetime import datetime
        metadata["created_at"] = datetime.now().isoformat()
        
        try:
            self.collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            logger.debug(f"Added document {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"Failed to add document {doc_id}: {e}")
            raise
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List]:
        """Search documents in collection.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            filters: Metadata filters
            
        Returns:
            Dictionary with search results
            
        Raises:
            ValueError: If no collection exists or query is empty
        """
        if not self.collection:
            raise ValueError("No collection available. Call create_collection() first.")
        
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        try:
            # Prepare where clause for filtering
            where_clause = None
            if filters:
                where_clause = filters
            
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause
            )
            
            logger.debug(f"Search completed: {len(results['documents'][0])} results")
            return results
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            raise
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete document from collection.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            True if deleted successfully, False if not found
            
        Raises:
            ValueError: If no collection exists
        """
        if not self.collection:
            raise ValueError("No collection available. Call create_collection() first.")
        
        try:
            # Check if document exists
            existing = self.collection.get(ids=[doc_id])
            if not existing["ids"]:
                logger.warning(f"Document {doc_id} not found")
                return False
            
            self.collection.delete(ids=[doc_id])
            logger.debug(f"Deleted document {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise
    
    def update_document(
        self,
        doc_id: str,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update existing document.
        
        Args:
            doc_id: Document ID to update
            text: New document text (optional)
            metadata: New metadata (optional)
            
        Returns:
            True if updated successfully, False if not found
            
        Raises:
            ValueError: If no collection exists or no updates provided
        """
        if not self.collection:
            raise ValueError("No collection available. Call create_collection() first.")
        
        if text is None and metadata is None:
            raise ValueError("At least one of text or metadata must be provided")
        
        try:
            # Check if document exists
            existing = self.collection.get(ids=[doc_id])
            if not existing["ids"]:
                logger.warning(f"Document {doc_id} not found")
                return False
            
            # Prepare update data
            update_data = {}
            if text is not None:
                update_data["documents"] = [text]
            if metadata is not None:
                # Add update timestamp
                from datetime import datetime
                metadata["updated_at"] = datetime.now().isoformat()
                update_data["metadatas"] = [metadata]
            
            self.collection.update(
                ids=[doc_id],
                **update_data
            )
            
            logger.debug(f"Updated document {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {e}")
            raise
    
    def list_documents(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all documents in collection.
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            List of document dictionaries
            
        Raises:
            ValueError: If no collection exists
        """
        if not self.collection:
            raise ValueError("No collection available. Call create_collection() first.")
        
        try:
            results = self.collection.get(limit=limit)
            
            documents = []
            for i, doc_id in enumerate(results["ids"]):
                doc = {
                    "id": doc_id,
                    "text": results["documents"][i] if i < len(results["documents"]) else "",
                    "metadata": results["metadatas"][i] if i < len(results["metadatas"]) else {}
                }
                documents.append(doc)
            
            return documents
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information.
        
        Returns:
            Dictionary with collection stats
            
        Raises:
            ValueError: If no collection exists
        """
        if not self.collection:
            raise ValueError("No collection available. Call create_collection() first.")
        
        try:
            # Get collection count
            results = self.collection.get()
            count = len(results["ids"])
            
            return {
                "name": self.collection.name,
                "count": count,
                "metadata": self.collection.metadata
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            raise
    
    def delete_by_metadata(self, filters: Dict[str, Any]) -> List[str]:
        """Delete documents by metadata filters.
        
        Args:
            filters: Metadata filters for deletion
            
        Returns:
            List of deleted document IDs
            
        Raises:
            ValueError: If no collection exists
        """
        if not self.collection:
            raise ValueError("No collection available. Call create_collection() first.")
        
        try:
            # First, find matching documents
            results = self.collection.get(where=filters)
            doc_ids = results["ids"]
            
            if doc_ids:
                # Delete found documents
                self.collection.delete(ids=doc_ids)
                logger.debug(f"Deleted {len(doc_ids)} documents matching filters")
            
            return doc_ids
        except Exception as e:
            logger.error(f"Failed to delete documents by metadata: {e}")
            raise
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects in the database.
        
        Returns:
            List of project information
        """
        if not self.collection:
            raise ValueError("No collection available. Call create_collection() first.")
        
        try:
            # Get all documents
            results = self.collection.get()
            
            # Extract unique project IDs
            projects = {}
            for metadata in results["metadatas"]:
                if metadata and "project_id" in metadata:
                    project_id = metadata["project_id"]
                    if project_id not in projects:
                        projects[project_id] = {
                            "id": project_id,
                            "name": project_id,  # Use ID as name for now
                            "document_count": 0
                        }
                    projects[project_id]["document_count"] += 1
            
            return list(projects.values())
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            raise
    
    def reset_collection(self) -> None:
        """Reset (clear all documents from) the collection.
        
        WARNING: This will delete all documents in the collection!
        """
        if not self.collection:
            raise ValueError("No collection available. Call create_collection() first.")
        
        try:
            collection_name = self.collection.name
            self.client.delete_collection(collection_name)
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Reset collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            raise