# RAG CLIツール設計書

## 概要
コマンドラインから直接実行できるRAGドキュメント管理ツール。ClaudeCodeや他の開発ツールとの連携を重視した設計。

## コマンド体系

### 基本構造
```
rag <command> [arguments] [options]
```

## 主要コマンド

### 1. search - ドキュメント検索
```bash
rag search <query> [options]

Options:
  -p, --project TEXT      プロジェクトID
  -k, --top-k INTEGER     取得件数 (default: 5)
  -t, --type [vector|keyword|hybrid]  検索タイプ (default: vector)
  -f, --format [text|json|table]      出力形式 (default: text)
  --filter-category TEXT  カテゴリーフィルタ
  --filter-tags TEXT      タグフィルタ（カンマ区切り）
  --show-context         前後の文脈を表示
  --no-highlight         ハイライト無効化

Examples:
  rag search "認証機能"
  rag search "認証" -p laravel_project -k 10
  rag search "API" --type keyword --filter-tags api,rest
  rag search "設計" --format json | jq '.results[0]'
```

### 2. index - ドキュメント登録
```bash
rag index <path> [options]

Options:
  -p, --project TEXT      プロジェクトID (必須または自動検出)
  -r, --recursive         ディレクトリを再帰的に処理
  --category TEXT         カテゴリー
  --tags TEXT            タグ（カンマ区切り）
  --author TEXT          作成者
  --related-system TEXT   関連システム
  --update               既存ドキュメントを更新
  --auto-detect-project   Gitから自動検出
  --dry-run              実行せずに処理内容を表示

Examples:
  rag index ./docs/design.md -p my_project --tags api,auth
  rag index ./docs/ -r --auto-detect-project
  rag index . -r --category "基本設計" --update
```

### 3. delete - ドキュメント削除
```bash
rag delete [options]

Options:
  --document-id TEXT      ドキュメントID
  --project TEXT         プロジェクト全体を削除
  --older-than TEXT      指定期間より古いものを削除 (e.g., 30d, 1w)
  --category TEXT        カテゴリー指定削除
  --source-type TEXT     ソースタイプ指定削除
  --confirm              確認プロンプトをスキップ
  --dry-run              実行せずに削除対象を表示

Examples:
  rag delete --document-id doc_123
  rag delete --project old_project --confirm
  rag delete --older-than 30d --source-type web
```

### 4. sync - プロジェクト同期
```bash
rag sync [options]

Options:
  -p, --project TEXT      プロジェクトID
  --path TEXT            同期対象パス (default: current dir)
  --full                 全ドキュメント再インデックス
  --modified-only        変更されたファイルのみ
  --remove-deleted       削除されたファイルをDBからも削除

Examples:
  rag sync -p my_project
  rag sync --full --remove-deleted
  rag sync --modified-only --path ./docs
```

### 5. cache - キャッシュ管理
```bash
rag cache <action> [options]

Actions:
  status                 キャッシュ状況表示
  clear                  キャッシュクリア
  refresh                期限切れキャッシュ更新

Options:
  --source-type TEXT     ソースタイプ指定
  --project TEXT         プロジェクト指定
  --expired-only         期限切れのみ対象

Examples:
  rag cache status
  rag cache clear --source-type jira
  rag cache refresh --expired-only
```

### 6. external - 外部データ登録
```bash
rag external <source> <content> [options]

Options:
  -p, --project TEXT      プロジェクトID
  --source-url TEXT      元データURL
  --ttl INTEGER          TTL（時間）
  --query TEXT           検索クエリ（キャッシュキー）

Examples:
  rag external jira "チケット内容" -p my_project --source-url "https://jira.example.com/browse/PROJ-123"
  rag external confluence "ページ内容" --ttl 24 --query "API設計"
```

### 7. interactive - インタラクティブモード
```bash
rag interactive [options]

Options:
  -p, --project TEXT      デフォルトプロジェクト
  --history              検索履歴を保存

Features:
  - 対話的な検索
  - 検索結果の詳細表示
  - 履歴機能
  - 補完機能

Example:
  rag interactive -p my_project
  > search: 認証
  > filter: category=基本設計
  > show: 1  # 1番目の結果を詳細表示
```

### 8. config - 設定管理
```bash
rag config [options]

Options:
  --show                 現在の設定を表示
  --set KEY VALUE        設定値を変更
  --reset                デフォルトに戻す
  --edit                 エディタで編集

Examples:
  rag config --show
  rag config --set default_project my_project
  rag config --set chunk_size 1500
  rag config --edit
```

## グローバルオプション

```bash
Options (全コマンド共通):
  --config PATH          設定ファイルパス
  --verbose             詳細出力
  --quiet               最小出力
  --log-level TEXT      ログレベル
  --help                ヘルプ表示
  --version             バージョン表示
```

## 出力形式

### Text形式（デフォルト）
```
[1] score: 0.95 | docs/api_design.md:120-145
カテゴリー: 基本設計 | タグ: api, rest
─────────────────────────────────────
APIの認証には、JWTトークンを使用します。
トークンの有効期限は24時間とし...
─────────────────────────────────────
```

### JSON形式
```json
{
  "query": "認証",
  "results": [
    {
      "score": 0.95,
      "file_path": "docs/api_design.md",
      "position": {"line_start": 120, "line_end": 145},
      "text": "APIの認証には...",
      "metadata": {
        "category": "基本設計",
        "tags": ["api", "rest"]
      }
    }
  ]
}
```

### Table形式
```
┌──────┬────────────────────┬───────┬────────────┐
│ Score│ File              │ Lines │ Category   │
├──────┼────────────────────┼───────┼────────────┤
│ 0.95 │ docs/api_design.md│120-145│ 基本設計    │
│ 0.87 │ docs/auth.md      │ 45-67 │ 詳細設計    │
└──────┴────────────────────┴───────┴────────────┘
```

## 環境変数

```bash
RAG_CONFIG_PATH    # 設定ファイルパス
RAG_PROJECT        # デフォルトプロジェクト
RAG_CHROMA_PATH    # ChromaDB保存パス
RAG_LOG_LEVEL      # ログレベル
```

## エラーハンドリング

- 明確なエラーメッセージ
- 終了コード：
  - 0: 成功
  - 1: 一般エラー
  - 2: ドキュメント未検出
  - 3: 接続エラー
  - 4: 設定エラー

## ClaudeCode連携例

```bash
# 保存時に自動インデックス
# .claude/hooks/post-save.sh
#!/bin/bash
if [[ $FILE_PATH == *.md ]]; then
    rag index "$FILE_PATH" --auto-detect-project --update
    echo "✓ Indexed: $FILE_PATH"
fi

# コミット前に変更分を更新
# .claude/hooks/pre-commit.sh
#!/bin/bash
for file in $(git diff --name-only --cached | grep ".md$"); do
    rag index "$file" --update
done

# エディタ選択テキストの関連ドキュメント検索
# .claude/hooks/search-selection.sh
#!/bin/bash
rag search "$SELECTED_TEXT" --format json | jq -r '.results[0].text'
```