# 🧠「第2の脳」RAGシステム 運用マニュアル

## 📋 目次
- [クイックスタート](#クイックスタート)
- [基本操作](#基本操作)  
- [ClaudeCode統合](#claudecode統合)
- [トラブルシューティング](#トラブルシューティング)
- [メンテナンス](#メンテナンス)
- [拡張・カスタマイズ](#拡張カスタマイズ)

---

## 🚀 クイックスタート

### インストール（ワンコマンド）
```bash
# 自動セットアップスクリプト実行
curl -sSL https://raw.githubusercontent.com/your-repo/rag-documents/main/setup.sh | bash

# 手動セットアップの場合
git clone https://github.com/your-repo/rag-documents.git
cd rag-documents
./setup.sh
```

### 初回セットアップ確認
```bash
# パスの更新
source ~/.bashrc

# ヘルプ表示
rag --help

# システム状態確認
rag stats
```

---

## 🛠️ 基本操作

### 1. ドキュメントのインデックス作成

#### 単一ファイル
```bash
rag index README.md --project my-project
rag index docs/api.md --project backend-api
```

#### ディレクトリ（再帰的）
```bash
rag index ./docs --project documentation --recursive
rag index ~/projects/frontend/src --project frontend --recursive
```

#### プロジェクト自動検出
```bash
rag index ./my-project --auto-detect-project --recursive
```

### 2. 検索機能

#### ベクトル検索（セマンティック）
```bash
rag search "認証システムの実装方法" --type vector
rag search "データベース設計パターン" --type vector --top-k 10
```

#### キーワード検索
```bash
rag search "JWT token" --type keyword
rag search "MySQL インデックス" --type keyword --project backend
```

#### ハイブリッド検索（推奨）
```bash
rag search "認証 JWT 実装" --type hybrid --alpha 0.6
rag search "API設計 REST" --type hybrid --project api-docs
```

### 3. 管理コマンド

#### プロジェクト一覧
```bash
rag projects
```

#### ドキュメント一覧
```bash
rag documents --limit 20
rag documents --project my-project --limit 50
```

#### システム統計
```bash
rag stats
```

### 4. 出力フォーマット

#### JSON出力（他システム連携用）
```bash
rag search "認証システム" --format json > results.json
```

#### シンプル出力（スクリプト用）
```bash
rag search "API設計" --format simple
```

---

## 🔌 ClaudeCode統合

### MCPサーバー設定

RAGシステムはModel Context Protocol (MCP)に対応しており、ClaudeCodeから直接利用できます。

#### 1. 設定ファイル確認
```bash
cat ~/.claude_code_mcp.json
```

期待される設定:
```json
{
  "mcpServers": {
    "rag-second-brain": {
      "command": "python3",
      "args": ["-m", "rag.mcp.server"],
      "cwd": "/home/user/.rag/src",
      "env": {
        "RAG_CONFIG_PATH": "/home/user/.rag/config.yaml",
        "PYTHONPATH": "/home/user/.rag/src"
      }
    }
  }
}
```

#### 2. ClaudeCodeでの利用方法

**検索コマンド例:**
```
@rag_search query="認証システム実装" search_type="hybrid" top_k=5
```

**インデックス作成例:**
```
@rag_index path="./new-project/docs" project_id="new-project" recursive=true
```

**統計情報取得:**
```
@rag_stats
```

---

## 🔧 トラブルシューティング

### よくある問題と解決策

#### 1. インポートエラー
```
ModuleNotFoundError: No module named 'chromadb'
```
**解決策:**
```bash
source ~/.rag/venv/bin/activate
pip install -r requirements.txt
```

#### 2. 検索結果が表示されない
**原因:** ドキュメントがインデックスされていない

**解決策:**
```bash
# インデックス状況確認
rag stats
rag documents --limit 10

# ドキュメントの再インデックス
rag index ./docs --project your-project --recursive
```

#### 3. MCPサーバーが起動しない
**確認項目:**
```bash
# 設定ファイル確認
cat ~/.claude_code_mcp.json

# 手動起動テスト
cd ~/.rag/src
python3 -m rag.mcp.server

# ログ確認
tail -f ~/.rag/logs/rag.log
```

#### 4. 検索精度が低い
**調整方法:**
```bash
# ハイブリッド検索のアルファ値調整
rag search "query" --type hybrid --alpha 0.3  # キーワード重視
rag search "query" --type hybrid --alpha 0.7  # ベクトル重視

# より多くの結果を確認
rag search "query" --top-k 10
```

### ログ確認
```bash
# 最新ログ
tail -f ~/.rag/logs/rag.log

# エラーログのみ
grep ERROR ~/.rag/logs/rag.log

# 特定期間のログ
grep "2024-08-24" ~/.rag/logs/rag.log
```

---

## 🔄 メンテナンス

### 日次メンテナンス

#### 自動更新スクリプト
```bash
#!/bin/bash
# ~/.rag/daily_update.sh

# 新規/更新ドキュメントの自動検出とインデックス
find ~/projects -name "*.md" -mtime -1 | while read file; do
    rag index "$file" --auto-detect-project
done

# 統計ログの記録
rag stats >> ~/.rag/logs/daily_stats.log
```

#### Cronジョブ設定
```bash
crontab -e
# 毎日AM 2:00に実行
0 2 * * * ~/.rag/daily_update.sh
```

### 週次メンテナンス

```bash
#!/bin/bash
# ~/.rag/weekly_maintenance.sh

# データベース統計
rag stats > ~/.rag/reports/weekly_report_$(date +%Y%m%d).txt

# 古いログのローテーション
find ~/.rag/logs -name "*.log" -mtime +30 -delete

# バックアップ（オプション）
tar -czf ~/.rag/backups/backup_$(date +%Y%m%d).tar.gz ~/.rag/data
```

### アップデート

#### システム更新
```bash
cd ~/.rag/src
git pull origin main
source ~/.rag/venv/bin/activate
pip install -r requirements.txt --upgrade
```

---

## 🚀 拡張・カスタマイズ

### 設定カスタマイズ

#### ~/.rag/config.yaml の主要設定
```yaml
# 埋め込みモデルの変更（高精度）
embedding:
  model: "sentence-transformers/multilingual-e5-large"
  device: "cuda"  # GPU使用
  batch_size: 64

# チャンキング戦略の調整
chunking:
  chunk_size: 1500     # より大きなチャンク
  chunk_overlap: 300   # 重複を多めに
  separator: "\n\n"

# 検索パラメータの調整
search:
  default_top_k: 7     # デフォルト結果数
  hybrid_alpha: 0.6    # キーワード重視
```

### 新しいプロジェクトタイプの追加

#### カスタムファイル形式サポート
```python
# ~/.rag/src/rag/utils/custom_loader.py
from rag.utils.document_loader import DocumentLoader

class CustomDocumentLoader(DocumentLoader):
    def __init__(self):
        super().__init__()
        # 新しい拡張子をサポート
        self.supported_extensions['.rst'] = 'restructuredtext'
        self.supported_extensions['.adoc'] = 'asciidoc'
```

### 外部システム連携

#### API経由でのアクセス
```python
# FastAPI サーバーの起動（オプション）
from rag.api.server import app
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 📊 監視・メトリクス

### パフォーマンス監視
```bash
# 検索レスポンス時間計測
time rag search "テスト検索"

# メモリ使用量確認
ps aux | grep python | grep rag

# ディスク使用量確認
du -sh ~/.rag/data
```

### 利用統計
```bash
# 日次検索回数
grep "Search completed" ~/.rag/logs/rag.log | grep "$(date +%Y-%m-%d)" | wc -l

# 人気クエリ分析
grep "Search query:" ~/.rag/logs/rag.log | awk '{print $NF}' | sort | uniq -c | sort -nr
```

---

## 🆘 サポート

### コミュニティ・サポート
- GitHub Issues: [プロジェクトのIssues](https://github.com/your-repo/rag-documents/issues)
- ドキュメント: [オンラインドキュメント](https://your-docs-site.com)
- サンプル: `~/.rag/samples/` ディレクトリ

### デバッグ情報収集
```bash
# システム情報の収集
rag stats > debug_info.txt
python3 --version >> debug_info.txt
pip list | grep -E "(chromadb|sentence-transformers)" >> debug_info.txt
```

---

**🎯 これで「第2の脳」RAGシステムを他プロジェクトで活用する準備が整いました！**