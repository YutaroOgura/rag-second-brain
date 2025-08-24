# MVP実装タスクリスト

## 現在のステータス
- ✅ プロジェクト構造の初期化完了
- ✅ 基本ファイルの作成完了
- 🚀 **次**: コア機能の実装開始

## Day 1-2: プロジェクト基盤 ✅ 完了

### 完了したタスク
- ✅ プロジェクトディレクトリ構造の作成
- ✅ requirements.txt の作成
- ✅ setup.py の作成
- ✅ config.yaml の作成
- ✅ .gitignore の作成
- ✅ パッケージ __init__.py ファイルの作成

## Day 3-4: ChromaDB統合 🚀 次のタスク

### 実装予定
1. **rag/core/database.py**
   - [ ] DatabaseManagerクラスの実装
   - [ ] ChromaDBクライアントの初期化
   - [ ] create_collection メソッド
   - [ ] add_document メソッド
   - [ ] search メソッド
   - [ ] delete_document メソッド

2. **tests/test_database.py**
   - [ ] DatabaseManagerの単体テスト
   - [ ] 接続テスト
   - [ ] CRUD操作のテスト

## Day 5-6: ドキュメント処理

### 実装予定
1. **rag/core/chunker.py**
   - [ ] DocumentChunkerクラス
   - [ ] chunk_text メソッド
   - [ ] extract_metadata メソッド

2. **rag/core/loader.py**
   - [ ] DocumentLoaderクラス
   - [ ] load_markdown メソッド
   - [ ] load_html メソッド

## Day 7-8: ベクトル化と検索

### 実装予定
1. **rag/core/vectorizer.py**
   - [ ] Vectorizerクラス
   - [ ] モデルの初期化
   - [ ] vectorize メソッド
   - [ ] batch_vectorize メソッド

2. **rag/core/search.py**
   - [ ] SearchEngineクラス
   - [ ] vector_search メソッド
   - [ ] format_results メソッド

## Day 9-10: CLIツール

### 実装予定
1. **rag/cli/main.py**
   - [ ] Clickアプリケーションのセットアップ
   - [ ] search コマンド
   - [ ] index コマンド
   - [ ] 出力フォーマッター

## Day 11-12: MCPサーバー

### 実装予定
1. **rag/mcp/server.py**
   - [ ] RAGMCPServerクラス
   - [ ] rag_search ツール
   - [ ] rag_index ツール
   - [ ] エラーハンドリング

## Day 13-14: 統合とテスト

### 実装予定
- [ ] 統合テスト
- [ ] ドキュメントの完成
- [ ] インストール手順の検証
- [ ] デモの準備

## 実装の進め方

### 今すぐ実行可能なコマンド

1. **仮想環境のセットアップ**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .  # 開発モードでインストール
```

2. **最初のコード実装開始**
```bash
# DatabaseManagerから開始
code rag/core/database.py
```

### 次のステップ

1. **rag/core/database.py の実装**
   - ChromaDBの基本操作を実装
   - 簡単なテストスクリプトで動作確認

2. **テストファイルの作成**
   - tests/test_database.py を作成
   - 基本的な動作確認

3. **サンプルデータの準備**
   - examples/sample.md を作成
   - テスト用のMarkdownファイル

## コーディング開始の準備

### 環境変数ファイル (.env)
```bash
# 必要に応じて作成
RAG_PROJECT=my_project
RAG_CONFIG_PATH=./config.yaml
RAG_LOG_LEVEL=DEBUG
```

### 最初のテストコード
```python
# test_setup.py - 環境確認用
import chromadb
import sentence_transformers

print("ChromaDB version:", chromadb.__version__)
print("Sentence Transformers available")
print("Setup complete!")
```

## 注意事項

- 各タスク完了後は必ずコミット
- テストは同時に書く
- ドキュメントは随時更新
- エラーハンドリングを忘れない

---

**現在の優先事項**: `rag/core/database.py` の実装を開始する