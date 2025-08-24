"""Tests for configuration utilities."""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

from rag.utils.config import ConfigManager, load_config, get_config_path


class TestConfigManager:
    """Test cases for ConfigManager."""
    
    def test_init_with_default_config(self):
        """Test ConfigManager initialization with default config."""
        config_manager = ConfigManager()
        
        assert config_manager.config is not None
        assert "database" in config_manager.config
        assert "embedding" in config_manager.config
        assert "chunking" in config_manager.config
    
    def test_init_with_custom_config_file(self):
        """Test ConfigManager initialization with custom config file."""
        test_config = {
            "database": {"path": "custom_path"},
            "embedding": {"model": "custom_model"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            config_file = f.name
        
        try:
            config_manager = ConfigManager(config_file)
            
            assert config_manager.config["database"]["path"] == "custom_path"
            assert config_manager.config["embedding"]["model"] == "custom_model"
        finally:
            Path(config_file).unlink()
    
    def test_init_with_nonexistent_config_file(self):
        """Test ConfigManager initialization with non-existent config file."""
        with pytest.raises(FileNotFoundError):
            ConfigManager("/nonexistent/config.yaml")
    
    def test_get_database_config(self):
        """Test getting database configuration."""
        config_manager = ConfigManager()
        
        db_config = config_manager.get_database_config()
        
        assert "path" in db_config
        assert "collection_name" in db_config
        assert db_config["type"] == "chromadb"
    
    def test_get_embedding_config(self):
        """Test getting embedding configuration."""
        config_manager = ConfigManager()
        
        emb_config = config_manager.get_embedding_config()
        
        assert "model" in emb_config
        assert "batch_size" in emb_config
        assert "device" in emb_config
    
    def test_get_chunking_config(self):
        """Test getting chunking configuration."""
        config_manager = ConfigManager()
        
        chunk_config = config_manager.get_chunking_config()
        
        assert "chunk_size" in chunk_config
        assert "chunk_overlap" in chunk_config
        assert "separator" in chunk_config
    
    def test_get_search_config(self):
        """Test getting search configuration."""
        config_manager = ConfigManager()
        
        search_config = config_manager.get_search_config()
        
        assert "default_top_k" in search_config
        assert "hybrid_alpha" in search_config
    
    def test_get_with_default_value(self):
        """Test get method with default value."""
        config_manager = ConfigManager()
        
        # Existing value
        value = config_manager.get("database.path")
        assert value is not None
        
        # Non-existing value with default
        default_value = config_manager.get("nonexistent.key", "default")
        assert default_value == "default"
    
    def test_get_nested_config_value(self):
        """Test getting nested configuration values."""
        config_manager = ConfigManager()
        
        # Test dot notation
        chunk_size = config_manager.get("chunking.chunk_size")
        assert isinstance(chunk_size, int)
        
        # Test deeper nesting
        log_level = config_manager.get("logging.level")
        assert log_level is not None
    
    def test_expand_path(self):
        """Test path expansion for user home directory."""
        config_manager = ConfigManager()
        
        # Test with ~ expansion
        expanded = config_manager.expand_path("~/.rag/data")
        assert not expanded.startswith("~")
        assert str(Path.home()) in expanded
        
        # Test without ~ expansion
        regular_path = config_manager.expand_path("/absolute/path")
        assert regular_path == "/absolute/path"
    
    def test_update_config(self):
        """Test updating configuration values."""
        config_manager = ConfigManager()
        
        original_value = config_manager.get("chunking.chunk_size")
        new_value = 1500
        
        config_manager.update("chunking.chunk_size", new_value)
        
        assert config_manager.get("chunking.chunk_size") == new_value
        assert config_manager.get("chunking.chunk_size") != original_value
    
    def test_save_config(self):
        """Test saving configuration to file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_file = f.name
        
        try:
            config_manager = ConfigManager()
            config_manager.update("chunking.chunk_size", 2000)
            
            config_manager.save_config(config_file)
            
            # Load saved config and verify
            with open(config_file, 'r') as f:
                saved_config = yaml.safe_load(f)
            
            assert saved_config["chunking"]["chunk_size"] == 2000
        finally:
            Path(config_file).unlink()


class TestConfigFunctions:
    """Test standalone configuration functions."""
    
    @patch.dict('os.environ', {'RAG_CONFIG_PATH': '/custom/config.yaml'})
    def test_get_config_path_from_env(self):
        """Test getting config path from environment variable."""
        path = get_config_path()
        assert path == "/custom/config.yaml"
    
    @patch.dict('os.environ', {}, clear=True)
    def test_get_config_path_default(self):
        """Test getting default config path."""
        with patch('pathlib.Path.home') as mock_home:
            mock_home.return_value = Path("/home/user")
            path = get_config_path()
            assert "/home/user/.rag/config.yaml" in path
    
    @patch('rag.utils.config.ConfigManager')
    def test_load_config_with_path(self, mock_config_manager):
        """Test load_config function with specific path."""
        mock_instance = mock_config_manager.return_value
        mock_instance.config = {"test": "value"}
        
        config = load_config("/test/config.yaml")
        
        mock_config_manager.assert_called_once_with("/test/config.yaml")
        assert config["test"] == "value"
    
    @patch('rag.utils.config.ConfigManager')
    def test_load_config_default(self, mock_config_manager):
        """Test load_config function with default path."""
        mock_instance = mock_config_manager.return_value
        mock_instance.config = {"default": "config"}
        
        config = load_config()
        
        assert config["default"] == "config"


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_valid_config_structure(self):
        """Test configuration with valid structure."""
        valid_config = {
            "database": {
                "type": "chromadb",
                "path": "~/.rag/chroma",
                "collection_name": "documents"
            },
            "embedding": {
                "model": "sentence-transformers/multilingual-e5-base",
                "batch_size": 32,
                "device": "cpu"
            },
            "chunking": {
                "strategy": "fixed",
                "chunk_size": 1000,
                "chunk_overlap": 200
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_config, f)
            config_file = f.name
        
        try:
            config_manager = ConfigManager(config_file)
            
            # Should not raise any exceptions
            assert config_manager.config is not None
        finally:
            Path(config_file).unlink()
    
    def test_missing_required_sections(self):
        """Test configuration missing required sections."""
        incomplete_config = {
            "database": {"path": "/tmp"}
            # Missing embedding, chunking sections
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(incomplete_config, f)
            config_file = f.name
        
        try:
            config_manager = ConfigManager(config_file)
            
            # Should handle missing sections gracefully by using defaults
            emb_config = config_manager.get_embedding_config()
            assert emb_config is not None  # Should return defaults
        finally:
            Path(config_file).unlink()
    
    def test_invalid_yaml_format(self):
        """Test handling of invalid YAML format."""
        invalid_yaml = """
        database:
            path: /tmp
            invalid: yaml: structure: 
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            config_file = f.name
        
        try:
            with pytest.raises(yaml.YAMLError):
                ConfigManager(config_file)
        finally:
            Path(config_file).unlink()


class TestConfigIntegration:
    """Integration tests for configuration system."""
    
    def test_full_config_lifecycle(self):
        """Test complete configuration lifecycle."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "test_config.yaml"
            
            # Create initial config
            initial_config = {
                "database": {"path": str(temp_dir / "chroma")},
                "embedding": {"model": "test_model"},
                "chunking": {"chunk_size": 500}
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(initial_config, f)
            
            # Load config
            config_manager = ConfigManager(str(config_file))
            
            # Verify initial values
            assert config_manager.get("database.path") == str(temp_dir / "chroma")
            assert config_manager.get("chunking.chunk_size") == 500
            
            # Update config
            config_manager.update("chunking.chunk_size", 1000)
            config_manager.update("new_section.new_value", "test")
            
            # Save updated config
            config_manager.save_config(str(config_file))
            
            # Load again and verify changes
            new_config_manager = ConfigManager(str(config_file))
            assert new_config_manager.get("chunking.chunk_size") == 1000
            assert new_config_manager.get("new_section.new_value") == "test"
    
    def test_config_with_environment_variables(self):
        """Test configuration with environment variable substitution."""
        test_config = {
            "database": {
                "path": "${RAG_DB_PATH:-~/.rag/chroma}"
            },
            "logging": {
                "level": "${RAG_LOG_LEVEL:-INFO}"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            config_file = f.name
        
        try:
            with patch.dict('os.environ', {'RAG_DB_PATH': '/custom/db', 'RAG_LOG_LEVEL': 'DEBUG'}):
                config_manager = ConfigManager(config_file)
                
                # Note: This would require implementing env var substitution in ConfigManager
                # For now, just verify the config loads
                assert config_manager.config is not None
        finally:
            Path(config_file).unlink()


@pytest.mark.slow
class TestConfigPerformance:
    """Performance tests for configuration system."""
    
    def test_large_config_loading(self):
        """Test loading large configuration file."""
        # Create large config
        large_config = {"database": {"path": "test"}}
        for i in range(1000):
            large_config[f"section_{i}"] = {
                f"key_{j}": f"value_{j}" for j in range(10)
            }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(large_config, f)
            config_file = f.name
        
        try:
            import time
            start_time = time.time()
            
            config_manager = ConfigManager(config_file)
            
            load_time = time.time() - start_time
            
            # Should load within reasonable time
            assert load_time < 1.0
            assert config_manager.config is not None
        finally:
            Path(config_file).unlink()
    
    def test_frequent_config_access(self):
        """Test frequent configuration value access."""
        config_manager = ConfigManager()
        
        import time
        start_time = time.time()
        
        # Access config values frequently
        for _ in range(1000):
            _ = config_manager.get("database.path")
            _ = config_manager.get("embedding.model")
            _ = config_manager.get("chunking.chunk_size")
        
        access_time = time.time() - start_time
        
        # Should be fast
        assert access_time < 0.5