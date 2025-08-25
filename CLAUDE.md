# CLAUDE.md

*重要* : 全ての回答は`日本語`で出力してください。

このファイルは、RAG Second Brainプロジェクトを扱う際のClaude Code (claude.ai/code) への指針を提供します。

## プロジェクト概要

**RAG Second Brain** - 日本語と英語の混在ドキュメントに対応した高精度検索システム。

### 🎯 プロジェクトの中心機能
**MCP（Model Context Protocol）を使用したRAG検索機能がメインです。**
- Claude Codeから`rag_search`ツールで直接検索可能
- CLIツールは開発・デバッグ用の補助機能

### 最新の状態（2025年8月25日）
- **Phase 1**: フォールバック検索実装完了（検索精度4.2倍改善）
- **Phase 2**: 日本語形態素解析実装完了（MeCab代替エンジン）
- **改善実装**: トークン制限対策実装完了（80文字制限でトークン80%削減）

## 重要：現在の実装状態

### 使用中のMCPサーバー
現在は元の`mcp-server.js`を使用しています（`enhanced-mcp-server.js`は削除済み）。
全ての改善機能は`mcp-server.js`に統合されています。

### MCP設定（.mcp.json）
```json
"rag-second-brain": {
  "command": "node",
  "args": ["/home/ogura/work/ultra/rag-second-brain/mcp-server.js"],
  "env": {
    "RAG_HOME": "/home/ogura/.rag"
  }
}
```

## 重要：トラブルシューティング

### 🔥 MCP検索が失敗する場合の復旧手順

**症状**: `ModuleNotFoundError: No module named 'rag.cli.main'`

**原因**: CLIモジュール構造が破損している

**復旧手順**:
```bash
# 1. バックアップ作成
mv ~/.rag ~/.rag_backup_$(date +%Y%m%d_%H%M%S)

# 2. クリーンインストール
bash setup.sh

# 3. データベース復元
cp -r ~/.rag_backup_*/chroma ~/.rag/

# 4. MCPサーバー更新
cp mcp-server.js ~/.rag/
cp mcp-tools-implementation.js ~/.rag/

# 5. コレクション復元（必要な場合）
/home/ogura/.rag/venv/bin/python -c "
import chromadb
client = chromadb.PersistentClient(path='/home/ogura/.rag/chroma')
collection = client.get_or_create_collection('documents')
print(f'Collection restored: {collection.count()} documents')
"
```

### ⚠️ 同期時の注意事項
- **絶対に使用しないコマンド**: `rsync --delete` （既存ファイルを削除してしまう）
- **推奨**: 個別ファイルのコピー `cp file1 file2`

## トークン節約ガイドライン

### 検索時の推奨設定
```javascript
// 推奨: トークン効率の良い検索
rag_search({
  query: "検索クエリ",
  search_type: "hybrid",  // Vector+Keyword検索（標準）
  top_k: 3,  // 結果を3件に制限
  use_fallback: true  // フォールバック有効（デフォルト）
})

// 大量の結果が必要な場合
rag_search({
  query: "検索クエリ",
  search_type: "keyword",  // キーワード検索のみ
  top_k: 5  // 最大5件まで
})
```

### 利用可能な検索タイプ
- `vector`: ベクトル検索のみ
- `keyword`: キーワード検索のみ  
- `hybrid`: Vector + Keyword（推奨）
- `fallback`: フォールバック検索（内部使用）

## ディレクトリ構造

```
rag-second-brain/
├── src/                    # ソースコード（Python）
│   ├── japanese_analyzer.py  # 日本語処理の中核
│   └── fallback_search.py    # フォールバック検索
├── mcp-server.js          # MCPサーバー（全機能統合版）
├── docs/                   # プロジェクトドキュメント
│   ├── INDEX.md           # ドキュメント一覧
│   ├── architecture/      # システム設計
│   ├── implementation/    # 実装詳細
│   ├── operations/        # 運用マニュアル
│   ├── reports/           # 完了報告書
│   └── setup/             # セットアップガイド
├── tests/                 # テストコード
└── scripts/               # ユーティリティスクリプト
```

## 作業時の注意事項

### 日本語処理
- `JapaneseAnalyzer`クラスが形態素解析を担当
- 専門用語辞書に50+のUltra Pay関連用語を登録済み
- 複合語（「Slack通知」等）は自動認識される

### 検索の仕組み
- **基本検索**: RAGインデックスから検索（高速）
- **フォールバック検索**: 結果が少ない場合、自動的に別の検索方式を試行
- **トークン制限対策**: 検索結果のテキストを80文字に制限

### パフォーマンス
- 検索レスポンス: 500ms以下を維持
- トークン使用量: 5,000-8,000（MCP応答）
- メモリ使用量: 100MB以下

## デバッグ情報

### ログ確認
```bash
# MCPサーバーのプロセス確認
ps aux | grep mcp-server

# エラーログ確認
tail -f ~/.rag/logs/mcp-server.log
```

### よくある問題と解決策
1. **トークン制限エラー**: `top_k`を3以下に設定
2. **検索結果が少ない**: フォールバック機能を有効化（デフォルトで有効）
3. **日本語検索の精度が低い**: `search_type: "keyword"`を試す

## 開発ガイドライン

### 🔴 最重要ルール
**このプロジェクトの主体はMCPサーバー（`mcp-server.js`）です。**
- CLIツール（Pythonコード）は補助的な機能
- **Pythonコードを変更したら、必ずMCPサーバーにも同じ変更を反映すること**
- MCPサーバーの動作確認を最優先で行う

### 開発フロー
1. **Python変更時の手順**:
   - `src/`配下のPythonコードを変更
   - 同じロジックを`mcp-server.js`に実装
   - MCPツール（`rag_search`）で動作確認
   - CLIツールでも動作確認

2. **テスト実行**:
   - Python: `tests/test_phase2_integration.py`を実行
   - MCP: Claude Codeから`rag_search`を実行して確認

3. **ドキュメント更新**:
   - 新機能追加時は`docs/`に追加
   - パフォーマンス問題は`docs/reports/`に記録

### MCPサーバーの保守
- **変更禁止事項**:
  - トークン制限対策（80文字制限）を変更しない
  - フォールバック検索機能を無効化しない
  
- **変更時の確認事項**:
  - MCPレスポンスのトークン数が10,000以下であること
  - 検索結果が正しくフォーマットされていること