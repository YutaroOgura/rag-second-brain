"""Tests for MCP Server implementation."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json

from rag.mcp.server import RAGMCPServer


class TestRAGMCPServer:
    """Test cases for RAG MCP Server."""
    
    @pytest.fixture
    def mock_database(self):
        """Create mock database manager."""
        mock_db = Mock()
        mock_db.search.return_value = {
            "documents": [["認証システムについて", "データベース設計"]],
            "metadatas": [[{"project_id": "test", "file_path": "/test.md"}, {"project_id": "test", "file_path": "/db.md"}]],
            "distances": [[0.2, 0.4]],
            "ids": [["doc1", "doc2"]]
        }
        return mock_db
    
    @pytest.fixture
    def mock_vectorizer(self):
        """Create mock vectorizer."""
        return Mock()
    
    @pytest.fixture
    def mock_search_engine(self, mock_database, mock_vectorizer):
        """Create mock search engine."""
        mock_engine = Mock()
        mock_engine.vector_search.return_value = {
            "results": [
                {
                    "text": "認証システムの実装について説明します",
                    "score": 0.8,
                    "metadata": {"project_id": "test", "category": "設計書"},
                    "id": "doc1"
                }
            ],
            "total_found": 1,
            "search_type": "vector"
        }
        mock_engine.hybrid_search.return_value = {
            "results": [
                {
                    "text": "ハイブリッド検索結果",
                    "score": 0.9,
                    "metadata": {"project_id": "test"},
                    "id": "hybrid1"
                }
            ],
            "total_found": 1,
            "search_type": "hybrid"
        }
        return mock_engine
    
    @pytest.fixture
    async def mcp_server(self, mock_database, mock_vectorizer, mock_search_engine):
        """Create MCP server instance with mocks."""
        server = RAGMCPServer()
        
        # Mock the initialization
        with patch.object(server, '_init_components') as mock_init:
            mock_init.return_value = (mock_database, mock_vectorizer, mock_search_engine)
            await server.initialize()
        
        server.database = mock_database
        server.vectorizer = mock_vectorizer
        server.search_engine = mock_search_engine
        
        return server
    
    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test MCP server initialization."""
        server = RAGMCPServer()
        
        with patch('rag.mcp.server.DatabaseManager') as mock_db, \
             patch('rag.mcp.server.Vectorizer') as mock_vec, \
             patch('rag.mcp.server.SearchEngine') as mock_search:
            
            await server.initialize()
            
            # Verify components were created
            mock_db.assert_called_once()
            mock_vec.assert_called_once()
            mock_search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rag_search_tool_success(self, mcp_server, mock_search_engine):
        """Test successful rag_search tool execution."""
        query = "認証システム"
        project_id = "test_project"
        top_k = 3
        
        result = await mcp_server.rag_search(
            query=query,
            project_id=project_id,
            top_k=top_k
        )
        
        # Verify search engine was called
        mock_search_engine.vector_search.assert_called_once_with(
            query, 
            project_id=project_id, 
            top_k=top_k
        )
        
        # Check result format
        assert "results" in result
        assert "success" in result
        assert result["success"] is True
        assert len(result["results"]) > 0
    
    @pytest.mark.asyncio
    async def test_rag_search_tool_with_search_type(self, mcp_server, mock_search_engine):
        """Test rag_search tool with different search types."""
        query = "テストクエリ"
        
        # Test hybrid search
        result = await mcp_server.rag_search(
            query=query,
            search_type="hybrid"
        )
        
        mock_search_engine.hybrid_search.assert_called_once()
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_rag_search_tool_empty_query_error(self, mcp_server):
        """Test rag_search tool with empty query."""
        result = await mcp_server.rag_search(query="")
        
        assert result["success"] is False
        assert "error" in result
        assert "empty" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_rag_search_tool_exception_handling(self, mcp_server, mock_search_engine):
        """Test rag_search tool exception handling."""
        mock_search_engine.vector_search.side_effect = Exception("Search failed")
        
        result = await mcp_server.rag_search(query="test")
        
        assert result["success"] is False
        assert "error" in result
        assert "search_failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_rag_index_tool_success(self, mcp_server, mock_database):
        """Test successful rag_index tool execution."""
        import tempfile
        from pathlib import Path
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# テストドキュメント\n\n認証システムについて")
            temp_file = f.name
        
        try:
            with patch('rag.mcp.server.DocumentLoader') as mock_loader:
                mock_loader.return_value.load_file.return_value = {
                    "content": "# テストドキュメント\n\n認証システムについて",
                    "metadata": {"file_path": temp_file}
                }
                
                result = await mcp_server.rag_index(
                    path=temp_file,
                    project_id="test_project"
                )
                
                # Verify file was loaded and indexed
                mock_loader.return_value.load_file.assert_called_once()
                assert result["success"] is True
                assert "indexed_files" in result
                
        finally:
            Path(temp_file).unlink()
    
    @pytest.mark.asyncio
    async def test_rag_index_tool_directory_recursive(self, mcp_server):
        """Test rag_index tool with directory recursion."""
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            for i in range(3):
                file_path = Path(temp_dir) / f"test_{i}.md"
                file_path.write_text(f"# テストファイル {i}")
            
            with patch('rag.mcp.server.DocumentLoader') as mock_loader:
                mock_loader.return_value.find_files.return_value = [
                    str(Path(temp_dir) / f"test_{i}.md") for i in range(3)
                ]
                
                def mock_load_file(path):
                    return {
                        "content": f"Content for {path}",
                        "metadata": {"file_path": path}
                    }
                
                mock_loader.return_value.load_file.side_effect = mock_load_file
                
                result = await mcp_server.rag_index(
                    path=temp_dir,
                    recursive=True,
                    project_id="test_project"
                )
                
                assert result["success"] is True
                assert len(result["indexed_files"]) == 3
    
    @pytest.mark.asyncio
    async def test_rag_index_tool_nonexistent_file(self, mcp_server):
        """Test rag_index tool with non-existent file."""
        result = await mcp_server.rag_index(
            path="/nonexistent/file.md",
            project_id="test_project"
        )
        
        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["message"].lower() or "does not exist" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_rag_suggest_tool_success(self, mcp_server, mock_search_engine):
        """Test successful rag_suggest tool execution."""
        context = """
        def authenticate_user(username, password):
            # ユーザー認証の実装
            pass
        """
        
        # Mock suggestion results
        mock_search_engine.vector_search.return_value = {
            "results": [
                {
                    "text": "認証システムの設計について",
                    "score": 0.85,
                    "metadata": {"category": "設計書"},
                    "id": "auth_doc"
                }
            ],
            "total_found": 1
        }
        
        result = await mcp_server.rag_suggest(
            context=context,
            project_id="test_project"
        )
        
        assert result["success"] is True
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0
        
        suggestion = result["suggestions"][0]
        assert "text" in suggestion
        assert "relevance" in suggestion
        assert "reason" in suggestion
    
    @pytest.mark.asyncio
    async def test_rag_delete_tool_success(self, mcp_server, mock_database):
        """Test successful rag_delete tool execution."""
        mock_database.delete_document.return_value = True
        
        result = await mcp_server.rag_delete(document_id="doc123")
        
        mock_database.delete_document.assert_called_once_with("doc123")
        assert result["success"] is True
        assert result["deleted_count"] == 1
    
    @pytest.mark.asyncio
    async def test_rag_delete_tool_project_deletion(self, mcp_server, mock_database):
        """Test rag_delete tool for project deletion."""
        mock_database.delete_by_metadata.return_value = ["doc1", "doc2", "doc3"]
        
        result = await mcp_server.rag_delete(project_id="test_project")
        
        mock_database.delete_by_metadata.assert_called_once_with({"project_id": "test_project"})
        assert result["success"] is True
        assert result["deleted_count"] == 3
    
    @pytest.mark.asyncio
    async def test_list_projects_resource(self, mcp_server, mock_database):
        """Test list_projects resource."""
        mock_database.list_projects.return_value = [
            {"id": "project1", "name": "プロジェクト1", "document_count": 10},
            {"id": "project2", "name": "プロジェクト2", "document_count": 5}
        ]
        
        result = await mcp_server.list_projects()
        
        assert "projects" in result
        assert len(result["projects"]) == 2
        assert result["projects"][0]["id"] == "project1"
    
    @pytest.mark.asyncio
    async def test_search_results_resource(self, mcp_server, mock_search_engine):
        """Test search_results resource."""
        project = "test_project"
        query = "認証システム"
        
        result = await mcp_server.cached_search(project=project, query=query)
        
        mock_search_engine.vector_search.assert_called_once()
        assert "query" in result
        assert "project" in result
        assert "results" in result
        assert result["query"] == query
        assert result["project"] == project
    
    @pytest.mark.asyncio
    async def test_search_context_prompt(self, mcp_server, mock_search_engine):
        """Test search_context_prompt."""
        query = "認証システムの実装"
        
        mock_search_engine.vector_search.return_value = {
            "results": [
                {
                    "text": "JWTトークンベースの認証システム",
                    "score": 0.9,
                    "metadata": {"file_path": "/auth/jwt.md"}
                },
                {
                    "text": "OAuth2認証の実装方法",
                    "score": 0.8,
                    "metadata": {"file_path": "/auth/oauth.md"}
                }
            ]
        }
        
        prompt_text = await mcp_server.search_context_prompt(query=query)
        
        assert query in prompt_text
        assert "JWTトークンベース" in prompt_text
        assert "OAuth2認証" in prompt_text
        assert "/auth/jwt.md" in prompt_text
    
    @pytest.mark.asyncio
    async def test_code_documentation_prompt(self, mcp_server, mock_search_engine):
        """Test code_documentation_prompt."""
        code = '''
        def authenticate_user(token):
            """ユーザー認証を行う"""
            return verify_jwt(token)
        '''
        
        mock_search_engine.vector_search.return_value = {
            "results": [
                {
                    "text": "JWT認証の実装ガイド",
                    "score": 0.85,
                    "metadata": {"category": "実装ガイド"}
                }
            ]
        }
        
        prompt_text = await mcp_server.code_documentation_prompt(code=code)
        
        assert "authentication" in prompt_text.lower() or "認証" in prompt_text
        assert "JWT認証の実装ガイド" in prompt_text


@pytest.mark.integration
class TestRAGMCPServerIntegration:
    """Integration tests for RAG MCP Server."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_search_workflow(self):
        """Test complete search workflow through MCP server."""
        server = RAGMCPServer()
        
        with patch('rag.mcp.server.DatabaseManager') as mock_db_class, \
             patch('rag.mcp.server.Vectorizer') as mock_vec_class, \
             patch('rag.mcp.server.SearchEngine') as mock_search_class:
            
            # Setup mocks
            mock_db = Mock()
            mock_vec = Mock()
            mock_search = Mock()
            
            mock_db_class.return_value = mock_db
            mock_vec_class.return_value = mock_vec
            mock_search_class.return_value = mock_search
            
            mock_search.vector_search.return_value = {
                "results": [{"text": "結果", "score": 0.8, "id": "1"}],
                "total_found": 1
            }
            
            await server.initialize()
            
            # Execute search
            result = await server.rag_search("テストクエリ")
            
            # Verify the complete flow
            assert result["success"] is True
            assert len(result["results"]) > 0
    
    @pytest.mark.asyncio
    async def test_end_to_end_index_workflow(self):
        """Test complete index workflow through MCP server."""
        import tempfile
        from pathlib import Path
        
        server = RAGMCPServer()
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# テストドキュメント\n\nテスト内容です。")
            temp_file = f.name
        
        try:
            with patch('rag.mcp.server.DatabaseManager') as mock_db_class, \
                 patch('rag.mcp.server.Vectorizer') as mock_vec_class, \
                 patch('rag.mcp.server.SearchEngine') as mock_search_class, \
                 patch('rag.mcp.server.DocumentLoader') as mock_loader_class:
                
                # Setup mocks
                mock_loader = Mock()
                mock_loader_class.return_value = mock_loader
                mock_loader.load_file.return_value = {
                    "content": "# テストドキュメント\n\nテスト内容です。",
                    "metadata": {"file_path": temp_file}
                }
                
                await server.initialize()
                
                # Execute indexing
                result = await server.rag_index(temp_file, project_id="test")
                
                # Verify the complete flow
                assert result["success"] is True
                assert len(result["indexed_files"]) == 1
                
        finally:
            Path(temp_file).unlink()


@pytest.mark.slow
class TestRAGMCPServerPerformance:
    """Performance tests for RAG MCP Server."""
    
    @pytest.mark.asyncio
    async def test_concurrent_search_requests(self, mcp_server, mock_search_engine):
        """Test handling concurrent search requests."""
        async def perform_search(query):
            return await mcp_server.rag_search(f"クエリ_{query}")
        
        # Execute multiple searches concurrently
        tasks = [perform_search(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should complete successfully
        assert len(results) == 10
        assert all(result["success"] for result in results)
    
    @pytest.mark.asyncio
    async def test_large_context_suggestion(self, mcp_server, mock_search_engine):
        """Test suggestion with large context."""
        large_context = "大きなコンテキスト。" * 1000
        
        result = await mcp_server.rag_suggest(context=large_context)
        
        # Should handle large context without issues
        assert result["success"] is True


class TestRAGMCPServerErrorHandling:
    """Test error handling in RAG MCP Server."""
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self):
        """Test server initialization failure handling."""
        server = RAGMCPServer()
        
        with patch('rag.mcp.server.DatabaseManager', side_effect=Exception("DB init failed")):
            with pytest.raises(Exception):
                await server.initialize()
    
    @pytest.mark.asyncio
    async def test_search_tool_database_error(self, mcp_server, mock_search_engine):
        """Test search tool with database error."""
        mock_search_engine.vector_search.side_effect = Exception("DB connection lost")
        
        result = await mcp_server.rag_search("test query")
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_index_tool_file_permission_error(self, mcp_server):
        """Test index tool with file permission error."""
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = await mcp_server.rag_index("/restricted/file.md")
            
            assert result["success"] is False
            assert "permission" in result["message"].lower() or "denied" in result["message"].lower()