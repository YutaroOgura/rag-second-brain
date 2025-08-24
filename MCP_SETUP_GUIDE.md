# 🔌 MCP（Model Context Protocol）設定ガイド

## 📋 概要

「第2の脳」RAGシステムはMCPサーバーとして動作し、ClaudeCodeから直接利用できます。

---

## ⚙️ ClaudeCode用設定

### 1. 基本設定（~/.claude_code_mcp.json）

```json
{
  "mcpServers": {
    "rag-second-brain": {
      "command": "python3",
      "args": ["-m", "rag.mcp.server"],
      "cwd": "/home/user/.rag/src",
      "env": {
        "PYTHONPATH": "/home/user/.rag/src",
        "RAG_CONFIG_PATH": "/home/user/.rag/config.yaml"
      }
    }
  }
}
```

### 2. 仮想環境を使用する場合

```json
{
  "mcpServers": {
    "rag-second-brain": {
      "command": "/home/user/.rag/venv/bin/python",
      "args": ["-m", "rag.mcp.server"],
      "cwd": "/home/user/.rag/src",
      "env": {
        "PYTHONPATH": "/home/user/.rag/src",
        "RAG_CONFIG_PATH": "/home/user/.rag/config.yaml"
      }
    }
  }
}
```

### 3. Docker環境での設定

```json
{
  "mcpServers": {
    "rag-second-brain": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--network", "host",
        "-v", "/home/user/.rag/data:/app/data",
        "-v", "/home/user/.rag/config.yaml:/app/config.yaml",
        "rag-second-brain:latest",
        "python", "-m", "rag.mcp.server"
      ]
    }
  }
}
```

---

## 🚀 セットアップ手順

### 方法1: 自動セットアップ（推奨）

```bash
# セットアップスクリプト実行時にMCP設定も自動で行われます
curl -sSL https://raw.githubusercontent.com/your-repo/rag-documents/main/setup.sh | bash
```

### 方法2: 手動セットアップ

```bash
# 1. MCPサーバーのインストール確認
python3 -c "from rag.mcp.server import RAGMCPServer; print('✓ MCP server ready')"

# 2. MCP設定ファイル作成
mkdir -p ~/.claude_code
cat > ~/.claude_code_mcp.json << 'EOF'
{
  "mcpServers": {
    "rag-second-brain": {
      "command": "python3",
      "args": ["-m", "rag.mcp.server"],
      "cwd": "$HOME/.rag/src",
      "env": {
        "PYTHONPATH": "$HOME/.rag/src",
        "RAG_CONFIG_PATH": "$HOME/.rag/config.yaml"
      }
    }
  }
}
EOF

# 3. パスを実際のユーザーディレクトリに置換
sed -i "s|\$HOME|$HOME|g" ~/.claude_code_mcp.json

# 4. 設定確認
cat ~/.claude_code_mcp.json
```

---

## 📝 利用可能なMCPツール

### 1. rag_search
**ドキュメント検索**
```
@rag_search query="データベース設計" search_type="hybrid" project_id="backend" top_k=5 alpha=0.5
```

**パラメータ:**
- `query` (必須): 検索クエリ
- `search_type`: "vector" | "keyword" | "hybrid" (デフォルト: "vector")
- `project_id`: プロジェクトID（省略可）
- `top_k`: 検索結果数（デフォルト: 5）
- `alpha`: ハイブリッド検索の重み（0-1、デフォルト: 0.5）

### 2. rag_index
**ドキュメントのインデックス作成**
```
@rag_index path="./docs" project_id="my-project" recursive=true
```

**パラメータ:**
- `path` (必須): インデックス対象パス
- `project_id` (必須): プロジェクトID
- `recursive`: サブディレクトリも含む（デフォルト: false）

### 3. rag_delete
**ドキュメント削除**
```
@rag_delete doc_id="doc_123456"
```

**パラメータ:**
- `doc_id` (必須): ドキュメントID

### 4. rag_projects
**プロジェクト一覧取得**
```
@rag_projects
```

### 5. rag_stats
**統計情報取得**
```
@rag_stats project_id="my-project"
```

**パラメータ:**
- `project_id`: プロジェクトID（省略可、省略時は全体統計）

---

## 🔍 利用可能なMCPリソース

### 1. config
**現在の設定情報**
```
URI: rag://config
```

### 2. projects
**プロジェクト一覧**
```
URI: rag://projects
```

### 3. project/{id}
**特定プロジェクトの詳細**
```
URI: rag://project/my-project
```

---

## 💡 利用可能なMCPプロンプト

### 1. search_help
**検索機能の使い方**
```
プロンプト名: rag_search_help
```

### 2. index_help
**インデックス作成の使い方**
```
プロンプト名: rag_index_help
```

---

## 🧪 動作確認

### 1. MCPサーバー直接起動テスト

```bash
# 仮想環境有効化
source ~/.rag/venv/bin/activate

# MCPサーバー起動テスト
python -m rag.mcp.server
# Ctrl+C で終了
```

### 2. ClaudeCode統合テスト

1. ClaudeCodeを再起動
2. 以下のコマンドを実行：

```
@rag_stats
```

成功すると統計情報が表示されます。

### 3. トラブルシューティング

#### エラー: "MCP server not found"
```bash
# MCP設定ファイル確認
cat ~/.claude_code_mcp.json

# パスが正しいか確認
ls -la ~/.rag/src/rag/mcp/server.py
```

#### エラー: "Module not found"
```bash
# 依存関係の再インストール
cd ~/.rag/src
pip install -r requirements.txt
pip install -e .
```

#### エラー: "Permission denied"
```bash
# 実行権限の付与
chmod +x ~/.rag/venv/bin/python
```

---

## 🔧 カスタマイズ

### 環境変数の追加

```json
{
  "mcpServers": {
    "rag-second-brain": {
      "command": "python3",
      "args": ["-m", "rag.mcp.server"],
      "cwd": "/home/user/.rag/src",
      "env": {
        "PYTHONPATH": "/home/user/.rag/src",
        "RAG_CONFIG_PATH": "/home/user/.rag/config.yaml",
        "RAG_LOG_LEVEL": "DEBUG",
        "RAG_EMBEDDING_DEVICE": "cuda"
      }
    }
  }
}
```

### 複数プロジェクト設定

```json
{
  "mcpServers": {
    "rag-project1": {
      "command": "python3",
      "args": ["-m", "rag.mcp.server"],
      "env": {
        "RAG_CONFIG_PATH": "/home/user/project1/rag_config.yaml"
      }
    },
    "rag-project2": {
      "command": "python3",
      "args": ["-m", "rag.mcp.server"],
      "env": {
        "RAG_CONFIG_PATH": "/home/user/project2/rag_config.yaml"
      }
    }
  }
}
```

---

## 📊 パフォーマンス設定

### 高速化設定

```json
{
  "mcpServers": {
    "rag-second-brain": {
      "command": "python3",
      "args": ["-m", "rag.mcp.server"],
      "env": {
        "RAG_CACHE_ENABLED": "true",
        "RAG_CACHE_TTL": "3600",
        "RAG_BATCH_SIZE": "32",
        "RAG_MAX_WORKERS": "4"
      }
    }
  }
}
```

---

## 🎯 ベストプラクティス

### 1. プロジェクト別管理
```bash
# プロジェクトごとにインデックス作成
@rag_index path="./backend" project_id="backend-api"
@rag_index path="./frontend" project_id="frontend-ui"

# プロジェクト別検索
@rag_search query="認証" project_id="backend-api"
```

### 2. 定期的なインデックス更新
```bash
# 開発開始時に最新ドキュメントをインデックス
@rag_index path="./docs" project_id="current-sprint" recursive=true
```

### 3. ハイブリッド検索の活用
```bash
# セマンティック検索とキーワード検索の組み合わせ
@rag_search query="ユーザー認証 JWT" search_type="hybrid" alpha=0.7
```

---

## 📚 関連ドキュメント

- [システム設計書](docs/ARCHITECTURE.md)
- [運用マニュアル](docs/OPERATIONS_MANUAL.md)
- [プロジェクト構造](PROJECT_STRUCTURE.md)

---

**🎉 MCPサーバーとしての「第2の脳」で、ClaudeCodeの能力を最大限活用しましょう！**