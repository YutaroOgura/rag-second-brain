# ローカルRAGドキュメント管理システム 要件定義書

## 1. システム概要

### 1.1 目的
複数のシステム開発プロジェクトのドキュメントを一元管理し、同一サーバー上の各プロジェクトからRAG検索を可能にするシステムの構築。

### 1.2 主要機能
- ドキュメントのベクトル化と保存
- ハイブリッド検索（ベクトル検索＋キーワード検索）
- 外部データソースのキャッシュ管理
- ClaudeCodeとの連携

## 2. ユースケース

### 2.1 プロジェクトドキュメント管理
- 設計書、仕様書のMarkdown/HTMLファイルをベクトル化して保存
- プロジェクトごとに論理的に分離して管理
- ClaudeCodeのフック機能と連携した自動更新

### 2.2 外部データソースキャッシュ
- Jira、Confluence、Web検索結果などをキャッシュ
- MCP経由で取得したデータの再利用
- API呼び出し回数の削減とレスポンス速度の向上

## 3. 機能要件

### 3.1 ドキュメント管理機能

#### 3.1.1 対応形式
- Markdown（.md）
- HTML（.html）

#### 3.1.2 チャンク分割
- デフォルト：1000-1500文字（ページ相当）
- 設定ファイルで調整可能
- RAGベストプラクティスに基づく最適値

#### 3.1.3 メタデータ
```json
{
  "file_path": "元ファイルのフルパス",
  "project_id": "プロジェクト識別子",
  "created_at": "登録日時",
  "updated_at": "更新日時",
  "category": "要件定義/基本設計/詳細設計など",
  "tags": ["タグ1", "タグ2"],
  "author": "作成者",
  "related_system": "関連システム名",
  "source_type": "local/jira/confluence/web/aws",
  "source_url": "元データのURL（外部データの場合）",
  "fetched_at": "取得日時（外部データの場合）",
  "ttl": "キャッシュ有効期限（外部データの場合）",
  "query": "検索時のクエリ（外部データの場合）"
}
```

### 3.2 検索機能

#### 3.2.1 検索方式
- ベクトル検索（意味的類似性）
- キーワード検索（完全一致/部分一致）
- ハイブリッド検索（両方の組み合わせ）
- メタデータフィルタリング

#### 3.2.2 検索結果
- マッチしたテキスト内容
- 関連度スコア
- 元ファイルへのフルパス
- 該当箇所の位置情報（行番号、セクション）
- 前後の文脈
- ハイライト情報
- 完全なメタデータ

### 3.3 削除機能
- 個別ドキュメント削除
- プロジェクト単位削除
- 条件指定削除（日付、カテゴリー、ソースタイプ等）

### 3.4 キャッシュ管理機能
- TTL（Time To Live）による有効期限管理
- 期限切れデータの識別
- 重複データの排除

## 4. API仕様

### 4.1 ドキュメント管理API

```python
# ドキュメント登録
POST /documents
{
    "project_id": "project_1",
    "file_path": "/path/to/document.md",
    "category": "基本設計",
    "tags": ["認証", "API"],
    "author": "開発者名",
    "related_system": "ユーザー管理システム"
}

# ドキュメント削除
DELETE /documents/{document_id}
DELETE /documents/project/{project_id}
DELETE /documents/batch
{
    "conditions": {
        "created_before": "2024-01-01",
        "category": "要件定義"
    }
}
```

### 4.2 検索API

```python
# ハイブリッド検索
POST /search
{
    "query": "ユーザー認証の実装方法",
    "project_id": "project_1",  # オプション
    "search_type": "hybrid",     # vector/keyword/hybrid
    "filters": {
        "category": "基本設計",
        "tags": ["認証"]
    },
    "top_k": 5
}

# レスポンス
{
    "results": [
        {
            "text": "マッチしたテキスト",
            "score": 0.95,
            "file_path": "/path/to/document.md",
            "position": {
                "line_start": 100,
                "line_end": 120,
                "section": "3.2 認証機能"
            },
            "context": {
                "before": "前の文脈",
                "after": "後の文脈"
            },
            "highlights": [
                {"start": 10, "end": 25}
            ],
            "metadata": {...}
        }
    ]
}
```

### 4.3 外部データ管理API

```python
# 外部データ登録
POST /external-data
{
    "source_type": "jira",
    "project_id": "project_1",
    "content": "チケット内容",
    "source_url": "https://jira.example.com/browse/PROJ-123",
    "query": "認証バグ",
    "ttl_hours": 24,
    "metadata": {
        "ticket_id": "PROJ-123",
        "status": "In Progress"
    }
}

# キャッシュステータス確認
GET /cache-status
{
    "source_type": "jira",
    "query": "認証バグ"
}
```

## 5. 非機能要件

### 5.1 運用要件
- CLIツールとして直接実行
- REST APIはオプション（将来の拡張用）
- 同期処理
- 認証なし（ローカル利用のみ）

### 5.2 ログ要件
- ログレベル：設定可能（デフォルト：標準）
- 標準レベル：エラー、警告、ドキュメント登録/削除操作

### 5.3 性能要件
- 検索レスポンス：1秒以内（ローカル環境）
- 同時接続：個人利用のため考慮不要

## 6. 技術スタック

```yaml
言語: Python 3.10+
CLIフレームワーク: Click
Webフレームワーク: FastAPI（オプション）
ベクトルDB: ChromaDB
埋め込みモデル: sentence-transformers/multilingual-e5-base
ドキュメント処理: LangChain
チャンク分割: LangChain TextSplitter
パッケージ管理: pip / pipx（グローバルインストール用）
ログ: Python logging
```

## 7. プロジェクト構造

```
rag_documents/
├── setup.py              # パッケージ設定
├── requirements.txt      # Python依存関係
├── config.yaml          # デフォルト設定ファイル
├── README.md            # 使用方法ドキュメント
├── rag/                 # メインパッケージ
│   ├── __init__.py
│   ├── cli.py          # CLIエントリーポイント
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── search.py   # searchコマンド
│   │   ├── index.py    # indexコマンド
│   │   ├── delete.py   # deleteコマンド
│   │   └── sync.py     # syncコマンド
│   ├── core/
│   │   ├── __init__.py
│   │   ├── vectorizer.py   # ベクトル化処理
│   │   ├── chunker.py      # チャンク分割
│   │   ├── database.py     # ChromaDB操作
│   │   └── cache_manager.py # キャッシュ管理
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py  # データモデル
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py   # ログ設定
│   │   └── config.py   # 設定管理
│   └── api/            # オプション
│       ├── __init__.py
│       ├── main.py     # FastAPIアプリ
│       └── routes.py   # APIルート
├── data/
│   ├── chroma/         # ChromaDB永続化（デフォルト）
│   └── logs/           # ログファイル
├── hooks/              # ClaudeCode連携用
│   ├── post-save.sh
│   └── pre-commit.sh
└── tests/
    └── test_*.py       # テストファイル
```

## 8. CLI使用方法

### 8.1 基本コマンド

```bash
# インストール
pip install -e .  # 開発環境
pipx install .    # グローバルインストール

# 検索
rag search "認証機能の実装" --project laravel_project
rag search "認証" -p laravel_project --keyword  # キーワード検索
rag search "認証" -p laravel_project --hybrid   # ハイブリッド検索

# ドキュメント登録
rag index ./docs/design.md --project laravel_project --tags api,auth
rag index ./docs/ --project laravel_project --recursive  # ディレクトリ全体

# 同期（プロジェクト内の全ドキュメント更新）
rag sync --project laravel_project

# 削除
rag delete --document-id doc_123
rag delete --project laravel_project  # プロジェクト全体
rag delete --older-than 30d          # 30日以前のドキュメント

# キャッシュ管理
rag cache --status                   # キャッシュ状況確認
rag cache --clear --source jira      # Jiraキャッシュクリア

# インタラクティブモード
rag interactive  # 対話的に検索
```

### 8.2 ClaudeCodeフック連携

```bash
# .claude/hooks/post-save.sh
#!/bin/bash
if [[ $FILE_PATH == *.md ]]; then
    rag index "$FILE_PATH" --auto-detect-project
fi

# .claude/hooks/pre-commit.sh
#!/bin/bash
git diff --name-only | grep ".md$" | xargs -I {} rag index {} --update
```

### 8.3 他プロジェクトからの利用

```bash
# Bashスクリプトから
result=$(rag search "認証" --format json)
echo $result | jq '.results[0].text'

# Pythonから（サブプロセス）
import subprocess
import json

result = subprocess.run(
    ['rag', 'search', '認証', '--format', 'json'],
    capture_output=True, text=True
)
data = json.loads(result.stdout)

# Make等のビルドツールから
search:
	@rag search "$(QUERY)" --project $(PROJECT)
```

### 8.4 設定ファイル

```yaml
# ~/.rag/config.yaml
default_project: my_project
chroma_path: ~/.rag/chroma
log_level: INFO
chunk_size: 1000
chunk_overlap: 200
embedding_model: multilingual-e5-base
```

## 9. 実装優先順位

### Phase 1: MVP（必須機能）
1. CLIツール基本実装（search, index）
2. ChromaDBセットアップ
3. ベクトル化・チャンク分割機能
4. 基本的な検索機能

### Phase 2: 拡張機能
1. ハイブリッド検索実装
2. メタデータフィルタリング
3. 削除・同期コマンド実装
4. インタラクティブモード

### Phase 3: 外部連携
1. 外部データソース対応（Jira、Confluence等）
2. キャッシュ管理機能
3. ClaudeCodeフック連携スクリプト
4. REST API実装（オプション）

## 10. 制約事項
- 個人利用限定（認証機能なし）
- 同一サーバー内でのみ利用
- 日本語ドキュメント対応必須