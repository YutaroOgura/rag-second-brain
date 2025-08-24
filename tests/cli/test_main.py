"""Tests for CLI main commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
from pathlib import Path

from rag.cli.main import cli, search, index


class TestCLICommands:
    """Test cases for CLI commands."""
    
    def setup_method(self):
        """Setup for each test."""
        self.runner = CliRunner()
    
    def test_cli_group_help(self):
        """Test CLI group help message."""
        result = self.runner.invoke(cli, ["--help"])
        
        assert result.exit_code == 0
        assert "RAG Document Management System" in result.output
        assert "search" in result.output
        assert "index" in result.output
    
    @patch('rag.cli.main.SearchEngine')
    @patch('rag.cli.main.DatabaseManager')
    @patch('rag.cli.main.Vectorizer')
    def test_search_command_success(self, mock_vectorizer_class, mock_db_class, mock_search_class):
        """Test successful search command."""
        # Setup mocks
        mock_db = Mock()
        mock_vectorizer = Mock()
        mock_search_engine = Mock()
        
        mock_db_class.return_value = mock_db
        mock_vectorizer_class.return_value = mock_vectorizer
        mock_search_class.return_value = mock_search_engine
        
        # Mock search results
        mock_search_engine.vector_search.return_value = {
            "results": [
                {
                    "text": "認証システムの実装について",
                    "score": 0.95,
                    "metadata": {"project_id": "test", "file_path": "/test/auth.md"},
                    "id": "doc1"
                }
            ],
            "total_found": 1,
            "search_type": "vector"
        }
        
        result = self.runner.invoke(search, ["認証システム"])
        
        assert result.exit_code == 0
        assert "認証システムの実装について" in result.output
        assert "Score: 0.95" in result.output
        mock_search_engine.vector_search.assert_called_once()
    
    @patch('rag.cli.main.SearchEngine')
    @patch('rag.cli.main.DatabaseManager')
    @patch('rag.cli.main.Vectorizer')
    def test_search_command_with_options(self, mock_vectorizer_class, mock_db_class, mock_search_class):
        """Test search command with various options."""
        # Setup mocks
        mock_search_engine = Mock()
        mock_search_class.return_value = mock_search_engine
        mock_search_engine.vector_search.return_value = {"results": [], "total_found": 0}
        
        # Test with project filter
        result = self.runner.invoke(search, [
            "テスト",
            "--project", "test_project",
            "--top-k", "10",
            "--type", "hybrid"
        ])
        
        assert result.exit_code == 0
        # Verify the search was called with correct parameters
    
    @patch('rag.cli.main.SearchEngine')
    @patch('rag.cli.main.DatabaseManager')
    @patch('rag.cli.main.Vectorizer')
    def test_search_command_json_output(self, mock_vectorizer_class, mock_db_class, mock_search_class):
        """Test search command with JSON output format."""
        # Setup mocks
        mock_search_engine = Mock()
        mock_search_class.return_value = mock_search_engine
        
        search_results = {
            "results": [
                {
                    "text": "テストドキュメント",
                    "score": 0.8,
                    "metadata": {"project_id": "test"},
                    "id": "doc1"
                }
            ],
            "total_found": 1,
            "search_type": "vector",
            "query": "テスト"
        }
        
        mock_search_engine.vector_search.return_value = search_results
        
        result = self.runner.invoke(search, ["テスト", "--format", "json"])
        
        assert result.exit_code == 0
        
        # Parse JSON output
        output_data = json.loads(result.output)
        assert output_data["query"] == "テスト"
        assert len(output_data["results"]) == 1
        assert output_data["results"][0]["text"] == "テストドキュメント"
    
    def test_search_command_empty_query(self):
        """Test search command with empty query."""
        result = self.runner.invoke(search, [""])
        
        assert result.exit_code != 0
        assert "Query cannot be empty" in result.output
    
    @patch('rag.cli.main.DocumentLoader')
    @patch('rag.cli.main.DatabaseManager')
    def test_index_command_single_file(self, mock_db_class, mock_loader_class):
        """Test indexing a single file."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# テストドキュメント\n\n認証システムについて説明します。")
            temp_file = f.name
        
        try:
            # Setup mocks
            mock_db = Mock()
            mock_loader = Mock()
            
            mock_db_class.return_value = mock_db
            mock_loader_class.return_value = mock_loader
            
            mock_loader.load_file.return_value = {
                "content": "# テストドキュメント\n\n認証システムについて説明します。",
                "metadata": {"file_path": temp_file}
            }
            
            result = self.runner.invoke(index, [temp_file, "--project", "test_project"])
            
            assert result.exit_code == 0
            assert "Successfully indexed" in result.output
            mock_loader.load_file.assert_called_once()
            
        finally:
            Path(temp_file).unlink()
    
    @patch('rag.cli.main.DocumentLoader')
    @patch('rag.cli.main.DatabaseManager')
    def test_index_command_directory_recursive(self, mock_db_class, mock_loader_class):
        """Test indexing a directory recursively."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = []
            for i in range(3):
                file_path = Path(temp_dir) / f"test_{i}.md"
                file_path.write_text(f"# テストファイル {i}\n\n内容 {i}")
                test_files.append(file_path)
            
            # Setup mocks
            mock_db = Mock()
            mock_loader = Mock()
            
            mock_db_class.return_value = mock_db
            mock_loader_class.return_value = mock_loader
            
            # Mock loader to return content for each file
            def mock_load_file(path):
                return {
                    "content": f"Content for {path}",
                    "metadata": {"file_path": str(path)}
                }
            
            mock_loader.load_file.side_effect = mock_load_file
            mock_loader.find_files.return_value = [str(f) for f in test_files]
            
            result = self.runner.invoke(index, [temp_dir, "--recursive", "--project", "test_project"])
            
            assert result.exit_code == 0
            assert "Successfully indexed 3 files" in result.output
            assert mock_loader.find_files.called
    
    def test_index_command_nonexistent_file(self):
        """Test indexing non-existent file."""
        result = self.runner.invoke(index, ["/nonexistent/file.md"])
        
        assert result.exit_code != 0
        assert "File not found" in result.output or "does not exist" in result.output
    
    @patch('rag.cli.main.DatabaseManager')
    def test_index_command_project_auto_detect(self, mock_db_class):
        """Test project auto-detection during indexing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Auto-detect test")
            temp_file = f.name
        
        try:
            with patch('rag.cli.main.detect_project_from_path') as mock_detect:
                mock_detect.return_value = "auto_detected_project"
                
                result = self.runner.invoke(index, [temp_file, "--auto-detect-project"])
                
                # Should attempt to auto-detect project
                mock_detect.assert_called_once()
                
        finally:
            Path(temp_file).unlink()
    
    def test_search_command_invalid_type(self):
        """Test search command with invalid search type."""
        result = self.runner.invoke(search, ["test", "--type", "invalid_type"])
        
        assert result.exit_code != 0
    
    def test_search_command_invalid_format(self):
        """Test search command with invalid output format."""
        result = self.runner.invoke(search, ["test", "--format", "invalid_format"])
        
        assert result.exit_code != 0
    
    @patch('rag.cli.main.SearchEngine')
    @patch('rag.cli.main.DatabaseManager')
    @patch('rag.cli.main.Vectorizer')
    def test_search_command_no_results(self, mock_vectorizer_class, mock_db_class, mock_search_class):
        """Test search command when no results found."""
        # Setup mocks
        mock_search_engine = Mock()
        mock_search_class.return_value = mock_search_engine
        
        mock_search_engine.vector_search.return_value = {
            "results": [],
            "total_found": 0,
            "search_type": "vector"
        }
        
        result = self.runner.invoke(search, ["nonexistent_query"])
        
        assert result.exit_code == 0
        assert "No results found" in result.output
    
    @patch('rag.cli.main.load_config')
    def test_config_loading(self, mock_load_config):
        """Test that configuration is loaded properly."""
        mock_config = {
            "database": {"path": "test_path"},
            "embedding": {"model": "test_model"}
        }
        mock_load_config.return_value = mock_config
        
        with patch('rag.cli.main.DatabaseManager') as mock_db, \
             patch('rag.cli.main.Vectorizer') as mock_vec:
            
            result = self.runner.invoke(search, ["test"])
            
            # Config should be loaded
            mock_load_config.assert_called_once()


class TestCLIIntegration:
    """Integration tests for CLI commands."""
    
    def setup_method(self):
        """Setup for each test."""
        self.runner = CliRunner()
    
    def test_cli_with_real_temp_data(self):
        """Test CLI with actual temporary data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test markdown file
            test_file = Path(temp_dir) / "test_doc.md"
            test_content = """# テストドキュメント

## 認証システム

JWTトークンを使用した認証システムの実装について説明します。

## データベース設計

ユーザー情報を格納するテーブル設計について。
"""
            test_file.write_text(test_content, encoding='utf-8')
            
            # Mock the dependencies but use real file operations
            with patch('rag.cli.main.DatabaseManager') as mock_db, \
                 patch('rag.cli.main.Vectorizer') as mock_vec, \
                 patch('rag.cli.main.DocumentLoader') as mock_loader:
                
                mock_loader.return_value.load_file.return_value = {
                    "content": test_content,
                    "metadata": {"file_path": str(test_file)}
                }
                
                result = self.runner.invoke(index, [str(test_file), "--project", "test"])
                
                assert result.exit_code == 0


class TestCLIErrorHandling:
    """Test error handling in CLI commands."""
    
    def setup_method(self):
        """Setup for each test."""
        self.runner = CliRunner()
    
    @patch('rag.cli.main.DatabaseManager')
    def test_database_connection_error(self, mock_db_class):
        """Test handling of database connection errors."""
        mock_db_class.side_effect = Exception("Database connection failed")
        
        result = self.runner.invoke(search, ["test"])
        
        assert result.exit_code != 0
        assert "Error" in result.output
    
    @patch('rag.cli.main.Vectorizer')
    def test_vectorizer_initialization_error(self, mock_vec_class):
        """Test handling of vectorizer initialization errors."""
        mock_vec_class.side_effect = Exception("Model loading failed")
        
        result = self.runner.invoke(search, ["test"])
        
        assert result.exit_code != 0
        assert "Error" in result.output
    
    def test_invalid_file_path_format(self):
        """Test handling of invalid file paths."""
        result = self.runner.invoke(index, [""])
        
        assert result.exit_code != 0


@pytest.mark.slow
class TestCLIPerformance:
    """Performance tests for CLI commands."""
    
    def setup_method(self):
        """Setup for each test."""
        self.runner = CliRunner()
    
    @patch('rag.cli.main.SearchEngine')
    @patch('rag.cli.main.DatabaseManager')
    @patch('rag.cli.main.Vectorizer')
    def test_search_response_time(self, mock_vectorizer_class, mock_db_class, mock_search_class):
        """Test search command response time."""
        import time
        
        # Setup mocks with delay to simulate processing
        mock_search_engine = Mock()
        mock_search_class.return_value = mock_search_engine
        
        def slow_search(*args, **kwargs):
            time.sleep(0.1)  # Simulate processing time
            return {"results": [], "total_found": 0}
        
        mock_search_engine.vector_search = slow_search
        
        start_time = time.time()
        result = self.runner.invoke(search, ["test"])
        end_time = time.time()
        
        # Should complete reasonably quickly
        assert end_time - start_time < 2.0
        assert result.exit_code == 0
    
    def test_index_command_large_file(self):
        """Test indexing a large file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            # Create large content
            large_content = "# 大きなファイル\n\n" + "テストコンテンツ。" * 10000
            f.write(large_content)
            temp_file = f.name
        
        try:
            with patch('rag.cli.main.DatabaseManager') as mock_db, \
                 patch('rag.cli.main.DocumentLoader') as mock_loader:
                
                mock_loader.return_value.load_file.return_value = {
                    "content": large_content,
                    "metadata": {"file_path": temp_file}
                }
                
                import time
                start_time = time.time()
                result = self.runner.invoke(index, [temp_file, "--project", "test"])
                end_time = time.time()
                
                # Should handle large files within reasonable time
                assert end_time - start_time < 10.0
                assert result.exit_code == 0
                
        finally:
            Path(temp_file).unlink()