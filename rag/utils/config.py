"""Configuration management for RAG system."""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
import yaml

logger = logging.getLogger(__name__)


def get_config_path() -> str:
    """Get configuration file path from environment or default.
    
    Returns:
        Path to configuration file
    """
    # Check environment variable first
    config_path = os.environ.get("RAG_CONFIG_PATH")
    if config_path:
        return config_path
    
    # Use default path in user's home directory
    return str(Path.home() / ".rag" / "config.yaml")


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file.
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = get_config_path()
    
    config_manager = ConfigManager(config_path)
    return config_manager.config


class ConfigManager:
    """Manages system configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize config manager.
        
        Args:
            config_path: Path to configuration file
        """
        if config_path is None:
            config_path = get_config_path()
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        logger.info(f"Configuration loaded from {self.config_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Configuration dictionary
        """
        # Default configuration
        default_config = {
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
                "chunk_overlap": 200,
                "separator": "\n\n"
            },
            "search": {
                "default_top_k": 5,
                "hybrid_alpha": 0.5
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
        
        # If config file doesn't exist, return defaults
        if not self.config_path.exists():
            logger.info(f"Config file not found at {self.config_path}, using defaults")
            return default_config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
            
            if file_config is None:
                file_config = {}
            
            # Merge file config with defaults
            merged_config = self._merge_configs(default_config, file_config)
            
            logger.debug(f"Configuration merged from file: {self.config_path}")
            return merged_config
            
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in config file {self.config_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            raise
    
    def _merge_configs(self, default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries.
        
        Args:
            default: Default configuration
            override: Override configuration
            
        Returns:
            Merged configuration
        """
        merged = default.copy()
        
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated key path (e.g., 'database.path')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def update(self, key_path: str, value: Any) -> None:
        """Update configuration value using dot notation.
        
        Args:
            key_path: Dot-separated key path
            value: New value to set
        """
        keys = key_path.split('.')
        config_dict = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config_dict:
                config_dict[key] = {}
            config_dict = config_dict[key]
        
        # Set the value
        config_dict[keys[-1]] = value
        logger.debug(f"Updated config: {key_path} = {value}")
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration.
        
        Returns:
            Database configuration dictionary
        """
        db_config = self.get("database", {}).copy()
        
        # Expand path
        if "path" in db_config:
            db_config["path"] = self.expand_path(db_config["path"])
        
        return db_config
    
    def get_embedding_config(self) -> Dict[str, Any]:
        """Get embedding configuration.
        
        Returns:
            Embedding configuration dictionary
        """
        return self.get("embedding", {}).copy()
    
    def get_chunking_config(self) -> Dict[str, Any]:
        """Get chunking configuration.
        
        Returns:
            Chunking configuration dictionary
        """
        return self.get("chunking", {}).copy()
    
    def get_search_config(self) -> Dict[str, Any]:
        """Get search configuration.
        
        Returns:
            Search configuration dictionary
        """
        return self.get("search", {}).copy()
    
    def expand_path(self, path: str) -> str:
        """Expand path with user home directory.
        
        Args:
            path: Path string (may contain ~)
            
        Returns:
            Expanded absolute path
        """
        expanded = Path(path).expanduser()
        return str(expanded.absolute())
    
    def save_config(self, config_path: Optional[str] = None) -> None:
        """Save current configuration to file.
        
        Args:
            config_path: Optional path to save config file
        """
        if config_path is None:
            config_path = self.config_path
        else:
            config_path = Path(config_path)
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Configuration saved to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save config to {config_path}: {e}")
            raise
    
    def validate_config(self) -> bool:
        """Validate configuration structure and values.
        
        Returns:
            True if configuration is valid
        """
        try:
            # Check required sections
            required_sections = ["database", "embedding", "chunking", "search"]
            for section in required_sections:
                if section not in self.config:
                    logger.warning(f"Missing required config section: {section}")
                    return False
            
            # Validate database config
            db_config = self.get_database_config()
            if "path" not in db_config:
                logger.warning("Missing database.path in configuration")
                return False
            
            # Validate embedding config
            emb_config = self.get_embedding_config()
            if "model" not in emb_config:
                logger.warning("Missing embedding.model in configuration")
                return False
            
            # Validate chunking config
            chunk_config = self.get_chunking_config()
            required_chunk_keys = ["chunk_size", "chunk_overlap"]
            for key in required_chunk_keys:
                if key not in chunk_config:
                    logger.warning(f"Missing chunking.{key} in configuration")
                    return False
            
            logger.debug("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration.
        
        Returns:
            Configuration summary
        """
        return {
            "config_file": str(self.config_path),
            "database": {
                "type": self.get("database.type"),
                "path": self.get("database.path"),
                "collection": self.get("database.collection_name")
            },
            "embedding": {
                "model": self.get("embedding.model"),
                "device": self.get("embedding.device")
            },
            "chunking": {
                "chunk_size": self.get("chunking.chunk_size"),
                "chunk_overlap": self.get("chunking.chunk_overlap")
            },
            "search": {
                "default_top_k": self.get("search.default_top_k"),
                "hybrid_alpha": self.get("search.hybrid_alpha")
            }
        }