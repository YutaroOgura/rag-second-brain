# 🧠「第2の脳」RAGシステム - プロダクション運用パッケージ

> **システム開発のための知識管理・検索システム**  
> ClaudeCodeとの統合で開発効率を飛躍的に向上

## 🚀 クイックスタート（3分で開始）

### 1. ワンコマンドインストール
```bash
curl -sSL https://raw.githubusercontent.com/your-repo/rag-documents/main/setup.sh | bash
```

### 2. 初回セットアップ
```bash
source ~/.bashrc
rag index ~/projects/your-project --project your-project --recursive
```

### 3. 検索実行
```bash
rag search "認証システム実装" --type hybrid
```

### 4. ClaudeCode統合
ClaudeCodeを再起動すると、MCPサーバーが自動認識され、`@rag_search`コマンドが利用可能になります。

---

## 📦 パッケージ内容

```
rag-second-brain/
├── 📁 rag/                    # メインソースコード
│   ├── core/                  # コア機能（DB、検索、ベクトル化）
│   ├── cli/                   # CLIインターフェース
│   ├── mcp/                   # MCPサーバー実装
│   └── utils/                 # ユーティリティ
├── 📁 tests/                  # 完全なテストスイート
│   ├── core/                  # 単体テスト
│   ├── cli/                   # CLIテスト
│   └── mcp/                   # MCPテスト
├── 📁 docs/                   # ドキュメント
│   ├── ARCHITECTURE.md        # システム設計書
│   ├── OPERATIONS_MANUAL.md   # 運用マニュアル
│   └── VALIDATION_SCENARIOS.md# 検証シナリオ
├── 🛠️ setup.sh               # 自動セットアップスクリプト
├── 🛠️ deploy.sh              # デプロイ自動化スクリプト
├── 🐳 Dockerfile             # Dockerコンテナ化
├── 🐳 docker-compose.yml     # Docker Compose設定
├── ⚙️ config.yaml            # デフォルト設定
└── 📋 requirements.txt       # Python依存関係
```

---

## 🎯 主要機能

### ✨ 3つの検索タイプ
- **🎯 ベクトル検索**: セマンティック（意味的）検索
- **🔍 キーワード検索**: 従来の文字列検索  
- **⚡ ハイブリッド検索**: 両方を組み合わせた高精度検索

### 🗂️ プロジェクト管理
- 複数プロジェクトの独立管理
- プロジェクト横断検索
- 自動プロジェクト検出

### 🌐 多言語対応
- 日本語・英語・中国語サポート
- 言語自動検出
- 多言語埋め込みモデル

### 🔌 ClaudeCode統合
- MCPサーバーによる本格統合
- リアルタイム検索
- コンテキスト生成

---

## 🏗️ インストール方法

### 方法1: 自動スクリプト（推奨）
```bash
# ワンコマンドセットアップ
curl -sSL https://raw.githubusercontent.com/your-repo/rag-documents/main/setup.sh | bash

# 手動実行の場合
git clone https://github.com/your-repo/rag-documents.git
cd rag-documents
chmod +x setup.sh
./setup.sh
```

### 方法2: Docker（分離環境）
```bash
# Docker Composeで起動
docker-compose up -d

# 直接Dockerで起動
docker run -d --name rag-second-brain \
  -v rag-data:/app/data \
  -v ~/.rag/config.yaml:/app/config/config.yaml \
  rag-second-brain:latest mcp-server
```

### 方法3: 手動インストール（カスタマイズ）
```bash
# 仮想環境作成
python3 -m venv ~/.rag/venv
source ~/.rag/venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# パッケージインストール
pip install -e .

# 設定ファイル配置
cp config.yaml ~/.rag/config.yaml
```

---

## 💡 使用例

### 基本的な使用方法
```bash
# ヘルプ表示
rag --help

# ドキュメントのインデックス
rag index ./docs --project my-project --recursive

# 検索実行
rag search "データベース設計パターン" --type hybrid --top-k 5

# システム状態確認
rag stats
```

### ClaudeCodeでの使用
```
# 検索
@rag_search query="認証システムの実装方法" search_type="hybrid"

# インデックス作成
@rag_index path="./new-feature/docs" project_id="new-feature" recursive=true

# 統計情報
@rag_stats
```

### プロジェクト管理
```bash
# プロジェクト一覧
rag projects

# 特定プロジェクトでの検索
rag search "API設計" --project backend-api

# プロジェクト自動検出
rag index ~/projects/frontend --auto-detect-project --recursive
```

---

## ⚙️ 設定・カスタマイズ

### 設定ファイル（~/.rag/config.yaml）
```yaml
# 高精度モデル（推奨）
embedding:
  model: "sentence-transformers/multilingual-e5-large"
  device: "cuda"  # GPU使用（利用可能な場合）
  batch_size: 64

# チャンキング戦略
chunking:
  chunk_size: 1500
  chunk_overlap: 300

# 検索パラメータ
search:
  default_top_k: 7
  hybrid_alpha: 0.6  # キーワード検索を重視
```

### MCPサーバー設定（~/.claude_code_mcp.json）
```json
{
  "mcpServers": {
    "rag-second-brain": {
      "command": "python3",
      "args": ["-m", "rag.mcp.server"],
      "cwd": "/home/user/.rag/src",
      "env": {
        "RAG_CONFIG_PATH": "/home/user/.rag/config.yaml"
      }
    }
  }
}
```

---

## 📈 パフォーマンス目安

### 推奨システム要件
- **CPU**: 2コア以上
- **メモリ**: 4GB以上（8GB推奨）
- **ストレージ**: 2GB以上の空き容量
- **Python**: 3.8以上

### パフォーマンス指標
- **インデックス速度**: ~100文書/分
- **検索レスポンス**: <3秒（1000文書環境）
- **メモリ使用量**: ~1GB（10,000文書環境）
- **同時検索**: 最大10リクエスト/秒

---

## 🔧 メンテナンス

### 日次メンテナンス
```bash
# 新規ドキュメントの自動インデックス
find ~/projects -name "*.md" -mtime -1 | while read file; do
  rag index "$file" --auto-detect-project
done

# 統計ログ記録
rag stats >> ~/.rag/logs/daily_stats.log
```

### 週次メンテナンス
```bash
# システム更新
cd ~/.rag/src && git pull
source ~/.rag/venv/bin/activate
pip install -r requirements.txt --upgrade

# バックアップ
tar -czf ~/.rag/backups/backup_$(date +%Y%m%d).tar.gz ~/.rag/data
```

---

## 🆘 トラブルシューティング

### よくある問題

#### 問題1: モジュールが見つからない
```bash
ModuleNotFoundError: No module named 'chromadb'
```
**解決策**:
```bash
source ~/.rag/venv/bin/activate
pip install -r requirements.txt
```

#### 問題2: 検索結果が表示されない
```bash
# インデックス状況確認
rag documents --limit 10
rag stats

# 再インデックス
rag index ./docs --project your-project --recursive
```

#### 問題3: MCPサーバーが認識されない
```bash
# 設定ファイル確認
cat ~/.claude_code_mcp.json

# 手動起動テスト
python3 -m rag.mcp.server
```

### ログ確認
```bash
# エラーログ確認
tail -f ~/.rag/logs/rag.log
grep ERROR ~/.rag/logs/rag.log

# デバッグ情報収集
rag stats > debug_info.txt
python3 --version >> debug_info.txt
```

---

## 📚 詳細ドキュメント

- **[システム設計書](ARCHITECTURE.md)**: 技術詳細・拡張方法
- **[運用マニュアル](OPERATIONS_MANUAL.md)**: 詳細な運用手順
- **[検証シナリオ](VALIDATION_SCENARIOS.md)**: テスト・検証方法
- **[開発ガイド](DEVELOPMENT.md)**: 開発・拡張ガイド

---

## 🌟 プロジェクト情報

- **バージョン**: 1.0.0
- **ライセンス**: MIT
- **サポート**: [GitHub Issues](https://github.com/your-repo/rag-documents/issues)
- **コミュニティ**: [Discussions](https://github.com/your-repo/rag-documents/discussions)

---

## 🚀 今すぐ始める

```bash
# 3分でスタート
curl -sSL https://raw.githubusercontent.com/your-repo/rag-documents/main/setup.sh | bash
source ~/.bashrc
rag index ~/projects --auto-detect-project --recursive
rag search "あなたの最初のクエリ" --type hybrid
```

**🎉 「第2の脳」で開発効率を革新しましょう！**