# 🧠「第2の脳」RAGシステム - プロジェクト構造

## 📁 プロジェクト全体構造

```
rag-documents/
├── 📂 rag/                           # メインソースコード
│   ├── __init__.py                   # パッケージ初期化
│   ├── 📂 core/                      # コア機能
│   │   ├── __init__.py
│   │   ├── database.py               # ChromaDB統合（DatabaseManager）
│   │   ├── vectorizer.py             # テキストベクトル化（Vectorizer）
│   │   └── search.py                 # 検索エンジン（SearchEngine）
│   ├── 📂 cli/                       # コマンドラインインターフェース
│   │   ├── __init__.py
│   │   └── main.py                   # CLI実装（Click + Rich UI）
│   ├── 📂 mcp/                       # MCPサーバー
│   │   ├── __init__.py
│   │   └── server.py                 # MCPサーバー実装
│   └── 📂 utils/                     # ユーティリティ
│       ├── __init__.py
│       ├── config.py                 # 設定管理（ConfigManager）
│       └── document_loader.py        # ドキュメント読み込み（DocumentLoader）
├── 📂 tests/                         # テストスイート（150+テストケース）
│   ├── __init__.py
│   ├── test_database.py              # データベーステスト（30+ケース）
│   ├── test_vectorizer.py            # ベクトル化テスト（25+ケース）
│   ├── test_search.py                # 検索エンジンテスト（35+ケース）
│   ├── test_cli.py                   # CLIテスト（25+ケース）
│   ├── test_mcp.py                   # MCPサーバーテスト（20+ケース）
│   └── test_document_loader.py       # ドキュメント読み込みテスト（20+ケース）
├── 📂 docs/                          # ドキュメント
│   ├── ARCHITECTURE.md               # システム設計書
│   ├── OPERATIONS_MANUAL.md          # 運用マニュアル
│   └── VALIDATION_SCENARIOS.md       # 検証シナリオ
├── 🛠️ setup.sh                      # 自動セットアップスクリプト
├── 🛠️ deploy.sh                     # マルチ環境デプロイスクリプト
├── 🛠️ healthcheck.sh                # Dockerヘルスチェック
├── 🐳 Dockerfile                     # Dockerコンテナ定義
├── 🐳 docker-compose.yml             # Docker Compose設定
├── ⚙️ config.yaml                    # デフォルト設定
├── 📋 requirements.txt               # Python依存関係
├── 📋 setup.py                       # パッケージセットアップ
├── 📖 README_PRODUCTION.md           # プロダクション運用ガイド
├── 📖 PROJECT_STRUCTURE.md           # このファイル（プロジェクト構造説明）
├── 🎯 CLAUDE.md                      # Claude Code指針
└── 🧪 .gitignore                     # Git除外設定
```

---

## 🎯 主要コンポーネント

### 🔧 コア機能 (`rag/core/`)

#### 1. **DatabaseManager** (`database.py`)
- **目的**: ChromaDBとの統合、ドキュメント管理
- **主要機能**:
  - ドキュメントの追加・検索・削除・更新
  - プロジェクト管理、コレクション管理
  - メタデータフィルタリング
- **キークラス**: `DatabaseManager`

#### 2. **Vectorizer** (`vectorizer.py`)
- **目的**: テキストのベクトル化、類似度計算
- **主要機能**:
  - 多言語対応埋め込みモデル
  - バッチ処理、GPU対応
  - 日本語前処理機能
- **キークラス**: `Vectorizer`

#### 3. **SearchEngine** (`search.py`)
- **目的**: 高度検索機能の実装
- **主要機能**:
  - ベクトル検索、キーワード検索、ハイブリッド検索
  - 結果ランキング、統計情報
  - クエリ提案機能
- **キークラス**: `SearchEngine`

### 🖥️ インターフェース層

#### 1. **CLI** (`rag/cli/main.py`)
- **目的**: コマンドライン操作インターフェース
- **主要コマンド**:
  - `rag search` - 検索実行
  - `rag index` - ドキュメントインデックス
  - `rag projects` - プロジェクト管理
  - `rag stats` - 統計情報表示
- **特徴**: Rich UIライブラリによる美しい表示

#### 2. **MCPサーバー** (`rag/mcp/server.py`)
- **目的**: ClaudeCode統合
- **主要機能**:
  - MCPプロトコル準拠
  - リアルタイム検索
  - コンテキスト自動生成
- **統合**: ClaudeCode `@rag_search` コマンド

### 🔧 サポート機能

#### 1. **設定管理** (`utils/config.py`)
- **目的**: YAML設定ファイル管理
- **機能**: 環境変数サポート、パス展開、設定検証

#### 2. **ドキュメント読み込み** (`utils/document_loader.py`)
- **目的**: 多形式ドキュメント処理
- **対応形式**: Markdown, HTML, TXT
- **機能**: メタデータ抽出、チャンキング、言語検出

---

## 🧪 品質保証

### テスト構造
- **単体テスト**: 各コンポーネントの個別機能テスト
- **統合テスト**: コンポーネント間相互作用テスト
- **パフォーマンステスト**: レスポンス時間、メモリ使用量
- **MCPテスト**: ClaudeCode統合テスト
- **エラーハンドリング**: 異常系テスト

### テストカバレッジ目標
- **コア機能**: 90%+
- **CLI**: 85%+
- **MCP**: 85%+
- **ユーティリティ**: 80%+

---

## 🚀 デプロイメント

### インストール方法

#### 1. **ワンコマンドセットアップ** (推奨)
```bash
curl -sSL https://raw.githubusercontent.com/your-repo/rag-documents/main/setup.sh | bash
```

#### 2. **Docker環境**
```bash
docker-compose up -d
```

#### 3. **手動インストール**
```bash
git clone [repo-url]
cd rag-documents
./setup.sh
```

### デプロイメント環境
- **local**: 開発・個人利用環境
- **docker**: コンテナ化環境
- **production**: 本番環境
- **test**: テスト・検証環境

---

## ⚙️ 設定・カスタマイズ

### 主要設定ファイル

#### 1. **~/.rag/config.yaml**
```yaml
embedding:
  model: "sentence-transformers/multilingual-e5-large"
  device: "cuda"  # GPU利用

database:
  path: "~/.rag/data/chroma"
  collection_name: "documents"

search:
  default_top_k: 7
  hybrid_alpha: 0.6
```

#### 2. **~/.claude_code_mcp.json**
```json
{
  "mcpServers": {
    "rag-second-brain": {
      "command": "python3",
      "args": ["-m", "rag.mcp.server"],
      "cwd": "/home/user/.rag/src"
    }
  }
}
```

---

## 📊 パフォーマンス指標

### 推奨システム要件
- **CPU**: 2コア以上
- **メモリ**: 4GB以上（8GB推奨）
- **ストレージ**: 2GB以上
- **Python**: 3.8以上

### 期待パフォーマンス
- **インデックス速度**: ~100文書/分
- **検索レスポンス**: <3秒（1000文書）
- **メモリ使用量**: ~1GB（10,000文書）
- **同時リクエスト**: 10req/秒

---

## 🔍 使用例

### 基本的な使用方法
```bash
# インデックス作成
rag index ./docs --project my-project --recursive

# 検索実行
rag search "データベース設計" --type hybrid --top-k 5

# プロジェクト管理
rag projects
rag stats
```

### ClaudeCode統合
```
@rag_search query="認証システムの実装" search_type="hybrid"
@rag_index path="./new-docs" project_id="new-feature"
@rag_stats
```

---

## 🛠️ 拡張性

### アーキテクチャの特徴
- **モジュラー設計**: 各コンポーネントの独立性
- **プラグインアーキテクチャ**: 新機能の容易な追加
- **外部データソース対応**: MCP経由でのデータ統合
- **多言語サポート**: i18n対応基盤

### 拡張ポイント
- **新しい文書形式**: DocumentLoaderの拡張
- **新しい埋め込みモデル**: Vectorizerの拡張
- **カスタム検索アルゴリズム**: SearchEngineの拡張
- **外部データソース**: MCPサーバーの拡張

---

## 🎯 今後の発展方向

### Phase 2 機能候補
- **Webインターフェース**: FastAPI + React
- **チーム機能**: 共有・権限管理
- **高度な分析**: ドキュメント関係性分析
- **自動分類**: ML-based categorization

### 技術的改善候補
- **パフォーマンス最適化**: インデックス並列化
- **スケーラビリティ**: 分散処理対応
- **モニタリング**: メトリクス収集・可視化
- **セキュリティ**: 認証・暗号化強化

---

## 📚 追加資料

- **[システム設計書](docs/ARCHITECTURE.md)**: 技術詳細・設計思想
- **[運用マニュアル](docs/OPERATIONS_MANUAL.md)**: 詳細運用手順
- **[検証シナリオ](docs/VALIDATION_SCENARIOS.md)**: テスト・検証方法
- **[プロダクション運用](README_PRODUCTION.md)**: 運用パッケージガイド

---

**🎉 「第2の脳」で開発効率を革新しましょう！**