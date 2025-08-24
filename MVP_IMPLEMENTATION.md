# MVP実装計画 - 第2の脳 RAGシステム

## 🎯 MVP目標
**2週間で動作する最小限のシステムを構築**
- 基本的な検索・登録機能
- CLIツールの基本コマンド
- MCPサーバーの最小限実装

## 📅 実装スケジュール

### Day 1-2: プロジェクト基盤構築
**目標**: 開発環境を整え、基本構造を作成

#### タスクリスト
- [ ] プロジェクト構造の作成
- [ ] 依存関係の定義（requirements.txt）
- [ ] setup.pyの作成
- [ ] 基本的な設定ファイル
- [ ] Gitリポジトリの初期化
- [ ] 開発環境のセットアップ

#### 成果物
```
rag_documents/
├── setup.py
├── requirements.txt
├── .gitignore
├── config.yaml
└── rag/
    ├── __init__.py
    └── version.py
```

### Day 3-4: ChromaDB統合
**目標**: ベクトルデータベースの基本操作を実装

#### タスクリスト
- [ ] ChromaDBクライアントの初期化
- [ ] コレクション管理
- [ ] 基本的なCRUD操作
- [ ] 永続化設定
- [ ] エラーハンドリング
- [ ] 単体テストの作成

#### 実装ファイル
```python
# rag/core/database.py
class DatabaseManager:
    def __init__(self, path: str)
    def create_collection(self, name: str)
    def add_document(self, text: str, metadata: dict)
    def search(self, query: str, n_results: int)
    def delete_document(self, doc_id: str)
```

### Day 5-6: ドキュメント処理
**目標**: ファイルの読み込みとチャンク分割を実装

#### タスクリスト
- [ ] Markdownファイルの読み込み
- [ ] テキストのチャンク分割
- [ ] メタデータ抽出
- [ ] ファイルパス管理
- [ ] HTMLファイルの基本対応
- [ ] テストデータの準備

#### 実装ファイル
```python
# rag/core/chunker.py
class DocumentChunker:
    def chunk_text(self, text: str) -> List[Chunk]
    def extract_metadata(self, file_path: str) -> dict

# rag/core/loader.py
class DocumentLoader:
    def load_markdown(self, path: str) -> str
    def load_html(self, path: str) -> str
```

### Day 7-8: ベクトル化と検索
**目標**: 埋め込みモデルによるベクトル化と検索機能

#### タスクリスト
- [ ] sentence-transformersのセットアップ
- [ ] テキストのベクトル化
- [ ] バッチ処理の実装
- [ ] 類似度検索
- [ ] 検索結果のフォーマット
- [ ] パフォーマンステスト

#### 実装ファイル
```python
# rag/core/vectorizer.py
class Vectorizer:
    def __init__(self, model_name: str)
    def vectorize(self, text: str) -> np.ndarray
    def batch_vectorize(self, texts: List[str]) -> np.ndarray

# rag/core/search.py
class SearchEngine:
    def vector_search(self, query: str, top_k: int)
    def format_results(self, results: List)
```

### Day 9-10: CLIツール実装
**目標**: 基本的なコマンドラインインターフェース

#### タスクリスト
- [ ] Clickフレームワークのセットアップ
- [ ] searchコマンドの実装
- [ ] indexコマンドの実装
- [ ] 出力フォーマット（テキスト/JSON）
- [ ] エラーメッセージ
- [ ] ヘルプドキュメント

#### 実装ファイル
```python
# rag/cli/main.py
@click.group()
def cli():
    pass

@cli.command()
def search(query: str, project: str, top_k: int):
    pass

@cli.command()
def index(path: str, project: str):
    pass
```

### Day 11-12: MCPサーバー基本実装
**目標**: ClaudeCodeから使える最小限のMCPサーバー

#### タスクリスト
- [ ] MCPサーバーの基本構造
- [ ] rag_searchツールの実装
- [ ] rag_indexツールの実装
- [ ] エラーハンドリング
- [ ] 設定ファイルのテンプレート
- [ ] 動作確認手順書

#### 実装ファイル
```python
# rag/mcp/server.py
class RAGMCPServer(Server):
    async def initialize(self)
    
    @tool()
    async def rag_search(self, query: str)
    
    @tool()
    async def rag_index(self, path: str)
```

### Day 13-14: 統合テストとドキュメント
**目標**: システム全体の動作確認と使用方法の文書化

#### タスクリスト
- [ ] 統合テストの実装
- [ ] インストール手順書
- [ ] 使用方法ガイド
- [ ] トラブルシューティング
- [ ] サンプルデータの準備
- [ ] デモシナリオの作成

## 🛠️ 実装の優先順位

### 必ず実装（MVP必須）
1. ✅ ChromaDBへの保存と検索
2. ✅ Markdownファイルの処理
3. ✅ CLIのsearch/indexコマンド
4. ✅ MCPのrag_searchツール

### できれば実装（MVP推奨）
1. ⏳ プロジェクトID管理
2. ⏳ 基本的なメタデータ
3. ⏳ JSON出力形式
4. ⏳ エラーハンドリング

### 後回し（Post-MVP）
1. 📅 ハイブリッド検索
2. 📅 削除機能
3. 📅 キャッシュ機能
4. 📅 インタラクティブモード

## 📋 日次チェックリスト

### 毎日実施
- [ ] コードのコミット
- [ ] テストの実行
- [ ] ドキュメントの更新
- [ ] 次の日のタスク確認

### 週次レビュー
- [ ] 進捗の確認
- [ ] 計画の調整
- [ ] 技術的課題の洗い出し
- [ ] 次週の目標設定

## 🚀 クイックスタート手順

### 1. 環境準備
```bash
# Python環境の準備
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install chromadb sentence-transformers click
```

### 2. プロジェクト構造の作成
```bash
# ディレクトリ作成
mkdir -p rag/{core,cli,mcp}
mkdir -p tests data/chroma

# 基本ファイルの作成
touch rag/__init__.py
touch rag/core/{__init__.py,database.py,vectorizer.py,chunker.py,search.py}
touch rag/cli/{__init__.py,main.py}
touch rag/mcp/{__init__.py,server.py}
```

### 3. 最初のコード実装
```python
# rag/core/database.py - 最初に実装するファイル
import chromadb
from chromadb.config import Settings

class DatabaseManager:
    def __init__(self, path: str = "./data/chroma"):
        self.client = chromadb.PersistentClient(
            path=path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = None
    
    def create_collection(self, name: str = "documents"):
        """コレクションを作成または取得"""
        self.collection = self.client.get_or_create_collection(name)
        return self.collection
    
    def add_document(self, text: str, metadata: dict = None):
        """ドキュメントを追加"""
        if not self.collection:
            self.create_collection()
        
        # シンプルなID生成（後で改善）
        doc_id = f"doc_{hash(text)}"
        
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )
        return doc_id
```

## 📊 成功指標

### 技術的指標
- [ ] 10個のドキュメントを登録できる
- [ ] 検索が1秒以内に完了する
- [ ] CLIコマンドが正常に動作する
- [ ] MCPサーバーがClaudeCodeから呼び出せる

### 品質指標
- [ ] 基本的なエラーハンドリングがある
- [ ] テストカバレッジ50%以上
- [ ] ドキュメントが整備されている
- [ ] インストールが5分以内で完了

## ⚠️ リスクと対策

### リスク1: MCPサーバーの実装難易度
**対策**: 最初はCLIに注力し、MCPは最小限の実装に留める

### リスク2: 日本語処理の精度
**対策**: multilingual-e5-baseモデルを使用し、必要に応じて調整

### リスク3: 時間不足
**対策**: 必須機能に集中し、推奨機能は余裕があれば実装

## 📝 実装メモ

### コーディング規約
- 型ヒントを使用
- docstringを記述
- エラーは適切に処理
- テストを同時に書く

### コミットメッセージ
```
feat: 新機能追加
fix: バグ修正
docs: ドキュメント更新
test: テスト追加
refactor: リファクタリング
```

## 🎯 次のアクション

1. **今すぐ実行**
   ```bash
   cd /home/ogura/work/my-project/rag_documents
   mkdir -p rag/{core,cli,mcp}
   touch setup.py requirements.txt
   ```

2. **最初のコード**
   - `rag/core/database.py`から実装開始
   - ChromaDBの基本操作を確認

3. **テスト環境**
   - サンプルのMarkdownファイルを準備
   - 簡単な動作確認スクリプトを作成

---

*さあ、第2の脳の構築を始めましょう！*