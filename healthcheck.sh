#!/bin/bash
# RAG Second Brain ヘルスチェックスクリプト

set -e

# 基本的なPythonインポートテスト
python3 -c "
import sys
sys.path.insert(0, '/app')
try:
    from rag.core.database import DatabaseManager
    from rag.core.vectorizer import Vectorizer
    from rag.core.search import SearchEngine
    print('✓ All core modules import successfully')
    exit(0)
except ImportError as e:
    print(f'✗ Import failed: {e}')
    exit(1)
except Exception as e:
    print(f'✗ Unexpected error: {e}')
    exit(1)
"

# 設定ファイルの存在確認
if [ ! -f "$RAG_CONFIG_PATH" ]; then
    echo "✗ Config file not found: $RAG_CONFIG_PATH"
    exit 1
fi

# データディレクトリの存在確認
if [ ! -d "$RAG_DATA_PATH" ]; then
    echo "✗ Data directory not found: $RAG_DATA_PATH"
    exit 1
fi

echo "✓ RAG Second Brain is healthy"
exit 0