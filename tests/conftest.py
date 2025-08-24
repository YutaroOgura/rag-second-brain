"""Pytest configuration and fixtures for RAG Second Brain tests."""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator
import chromadb
from chromadb.config import Settings

from rag.core.database import DatabaseManager
from rag.core.vectorizer import Vectorizer
from rag.utils.config import ConfigManager


@pytest.fixture(scope="session")
def temp_data_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test data."""
    temp_dir = Path(tempfile.mkdtemp(prefix="rag_test_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def test_config(temp_data_dir: Path) -> dict:
    """Create test configuration."""
    return {
        "database": {
            "type": "chromadb",
            "path": str(temp_data_dir / "chroma"),
            "collection_name": "test_documents"
        },
        "embedding": {
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "batch_size": 4,
            "device": "cpu"
        },
        "chunking": {
            "strategy": "fixed",
            "chunk_size": 500,
            "chunk_overlap": 50,
            "separator": "\n\n"
        },
        "search": {
            "default_top_k": 3,
            "hybrid_alpha": 0.5
        }
    }


@pytest.fixture(scope="function")
def test_database(test_config: dict) -> Generator[DatabaseManager, None, None]:
    """Create a test database manager."""
    db_manager = DatabaseManager(test_config["database"]["path"])
    db_manager.create_collection(test_config["database"]["collection_name"])
    yield db_manager
    # Cleanup is handled by temp_data_dir fixture


@pytest.fixture(scope="function")
def test_vectorizer(test_config: dict) -> Vectorizer:
    """Create a test vectorizer with small model."""
    return Vectorizer(test_config["embedding"]["model"])


@pytest.fixture
def sample_documents() -> list[dict]:
    """Sample documents for testing."""
    return [
        {
            "id": "doc1",
            "text": "認証システムの設計について説明します。JWTトークンを使用してユーザー認証を実装します。",
            "metadata": {
                "project_id": "test_project",
                "category": "設計書",
                "tags": ["認証", "JWT"],
                "file_path": "/test/auth_design.md"
            }
        },
        {
            "id": "doc2", 
            "text": "データベース設計の基本原則について。正規化を適切に行い、インデックスを設定することが重要です。",
            "metadata": {
                "project_id": "test_project",
                "category": "設計書",
                "tags": ["データベース", "正規化"],
                "file_path": "/test/db_design.md"
            }
        },
        {
            "id": "doc3",
            "text": "APIの実装方法について。RESTfulな設計を心がけ、適切なHTTPステータスコードを使用します。",
            "metadata": {
                "project_id": "test_project",
                "category": "実装ガイド",
                "tags": ["API", "REST"],
                "file_path": "/test/api_guide.md"
            }
        }
    ]


@pytest.fixture
def sample_markdown_files(temp_data_dir: Path) -> list[Path]:
    """Create sample markdown files for testing."""
    files = []
    
    # 認証に関するドキュメント
    auth_content = """# 認証システム設計書

## 概要
JWTトークンベースの認証システムを実装します。

## 仕様
- アクセストークン有効期限: 15分
- リフレッシュトークン有効期限: 7日
- 暗号化アルゴリズム: RS256

## 実装方法
```javascript
const jwt = require('jsonwebtoken');
// トークン生成ロジック
```
"""
    auth_file = temp_data_dir / "auth_design.md"
    auth_file.write_text(auth_content, encoding="utf-8")
    files.append(auth_file)
    
    # データベース設計ドキュメント
    db_content = """# データベース設計書

## テーブル構造

### users テーブル
- id: PRIMARY KEY
- email: UNIQUE
- password_hash: VARCHAR(255)
- created_at: TIMESTAMP

### posts テーブル
- id: PRIMARY KEY
- user_id: FOREIGN KEY
- title: VARCHAR(255)
- content: TEXT
"""
    db_file = temp_data_dir / "database_design.md"
    db_file.write_text(db_content, encoding="utf-8")
    files.append(db_file)
    
    return files


@pytest.fixture
def mock_embedding_vectors():
    """Mock embedding vectors for testing."""
    import numpy as np
    return {
        "doc1": np.random.rand(384).tolist(),
        "doc2": np.random.rand(384).tolist(), 
        "doc3": np.random.rand(384).tolist(),
    }