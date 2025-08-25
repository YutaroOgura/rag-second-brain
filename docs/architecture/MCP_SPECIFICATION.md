# MCP Server 仕様書

## 概要
RAGシステムをMCP (Model Context Protocol) サーバーとして実装し、ClaudeCodeから直接アクセス可能にする。

## MCPサーバー機能

### 提供するTools

#### 1. rag_search
**説明**: ドキュメントをベクトル検索・キーワード検索・ハイブリッド検索

**パラメータ**:
```typescript
{
  query: string;           // 検索クエリ（必須）
  project?: string;        // プロジェクトID
  search_type?: "vector" | "keyword" | "hybrid";  // デフォルト: hybrid
  top_k?: number;          // 取得件数（デフォルト: 5）
  filters?: {
    category?: string;
    tags?: string[];
    created_after?: string;
    created_before?: string;
  };
}
```

**レスポンス**:
```typescript
{
  results: Array<{
    text: string;
    score: number;
    file_path: string;
    position: {
      line_start: number;
      line_end: number;
      section?: string;
    };
    metadata: object;
    highlights: Array<{start: number, end: number}>;
  }>;
  total_found: number;
  search_time_ms: number;
}
```

#### 2. rag_index
**説明**: ドキュメントをインデックスに追加

**パラメータ**:
```typescript
{
  path: string;            // ファイルまたはディレクトリパス（必須）
  project?: string;        // プロジェクトID
  recursive?: boolean;     // ディレクトリを再帰的に処理
  metadata?: {
    category?: string;
    tags?: string[];
    author?: string;
    related_system?: string;
  };
  update?: boolean;        // 既存を更新
  auto_detect?: boolean;   // プロジェクトを自動検出
}
```

**レスポンス**:
```typescript
{
  indexed_files: string[];
  total_chunks: number;
  errors: string[];
  time_taken_ms: number;
}
```

#### 3. rag_delete
**説明**: ドキュメントを削除

**パラメータ**:
```typescript
{
  document_id?: string;    // ドキュメントID
  project?: string;        // プロジェクト全体を削除
  filters?: {
    older_than?: string;   // "30d", "1w"等
    category?: string;
    source_type?: string;
  };
}
```

**レスポンス**:
```typescript
{
  deleted_count: number;
  deleted_ids: string[];
}
```

#### 4. rag_suggest
**説明**: 現在のコンテキストに基づいて関連ドキュメントを提案

**パラメータ**:
```typescript
{
  context: string;         // 現在のファイル内容や選択テキスト
  project?: string;
  top_k?: number;
  context_type?: "code" | "markdown" | "comment";
}
```

**レスポンス**:
```typescript
{
  suggestions: Array<{
    text: string;
    relevance: number;
    reason: string;       // なぜ関連があるか
    file_path: string;
    snippet: string;      // 関連部分の抜粋
  }>;
}
```

#### 5. rag_sync
**説明**: プロジェクトのドキュメントを同期

**パラメータ**:
```typescript
{
  project: string;
  path?: string;
  full?: boolean;          // 全ドキュメント再インデックス
  remove_deleted?: boolean; // 削除されたファイルも削除
}
```

**レスポンス**:
```typescript
{
  added: string[];
  updated: string[];
  deleted: string[];
  unchanged: number;
}
```

#### 6. rag_external
**説明**: 外部データソース（Jira、Confluence等）のデータを登録

**パラメータ**:
```typescript
{
  source_type: "jira" | "confluence" | "web" | "custom";
  content: string;
  project: string;
  metadata: {
    source_url?: string;
    query?: string;
    ttl_hours?: number;
    [key: string]: any;
  };
}
```

**レスポンス**:
```typescript
{
  document_id: string;
  expires_at?: string;
}
```

### 提供するResources

#### 1. Projects List
**URI**: `rag://projects`

**レスポンス**:
```typescript
{
  projects: Array<{
    id: string;
    name: string;
    document_count: number;
    last_updated: string;
  }>;
}
```

#### 2. Search Results
**URI**: `rag://search/{project}/{query}`

**レスポンス**:
```typescript
{
  query: string;
  project: string;
  results: SearchResult[];
  cached_at?: string;
}
```

#### 3. Document Content
**URI**: `rag://document/{document_id}`

**レスポンス**:
```typescript
{
  id: string;
  content: string;
  metadata: object;
  chunks: Array<{
    text: string;
    position: object;
  }>;
}
```

#### 4. Project Statistics
**URI**: `rag://stats/{project}`

**レスポンス**:
```typescript
{
  project: string;
  total_documents: number;
  total_chunks: number;
  categories: object;
  tags: string[];
  last_indexed: string;
}
```

### 提供するPrompts

#### 1. search_context
**説明**: 検索時のコンテキスト補完

```typescript
{
  name: "rag_search_context",
  description: "RAG検索のコンテキストを提供",
  arguments: [
    {
      name: "query",
      description: "検索クエリ",
      required: true
    }
  ]
}
```

**プロンプトテンプレート**:
```
Based on the search query "{query}", here are related documents from the knowledge base:

{search_results}

You can use this information to provide more accurate and contextual responses.
```

#### 2. code_documentation
**説明**: コードに対する関連ドキュメント提供

```typescript
{
  name: "rag_code_docs",
  description: "コードの関連ドキュメントを提供",
  arguments: [
    {
      name: "code",
      description: "対象コード",
      required: true
    }
  ]
}
```

## 実装詳細

### MCPサーバークラス構造

```python
# mcp/server.py
from mcp.server import Server, tool, resource, prompt
from typing import Dict, List, Any, Optional
import asyncio

class RAGMCPServer(Server):
    """RAG System MCP Server Implementation"""
    
    def __init__(self):
        super().__init__("rag-system")
        self.db_manager = None
        self.search_engine = None
        self.vectorizer = None
    
    async def initialize(self):
        """サーバー初期化"""
        from rag.core import DatabaseManager, SearchEngine, Vectorizer
        
        config = load_config()
        self.db_manager = DatabaseManager(config.chroma_path)
        self.search_engine = SearchEngine(self.db_manager)
        self.vectorizer = Vectorizer(config.embedding_model)
    
    @tool()
    async def rag_search(
        self, 
        query: str,
        project: Optional[str] = None,
        search_type: str = "hybrid",
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """ドキュメント検索ツール"""
        try:
            results = await self.search_engine.search(
                query=query,
                project=project,
                search_type=search_type,
                top_k=top_k,
                filters=filters
            )
            
            return {
                "results": [r.to_dict() for r in results],
                "total_found": len(results),
                "search_time_ms": results.search_time
            }
        except Exception as e:
            return {"error": str(e)}
    
    @tool()
    async def rag_index(
        self,
        path: str,
        project: Optional[str] = None,
        recursive: bool = False,
        metadata: Optional[Dict] = None,
        update: bool = False,
        auto_detect: bool = False
    ) -> Dict[str, Any]:
        """ドキュメントインデックスツール"""
        # 実装
    
    @tool()
    async def rag_suggest(
        self,
        context: str,
        project: Optional[str] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """コンテキスト関連ドキュメント提案ツール"""
        # コンテキストを解析
        # 関連キーワード抽出
        # 検索実行
        # 結果を関連度順にソート
        pass
    
    @resource(uri="rag://projects")
    async def list_projects(self) -> Dict[str, Any]:
        """プロジェクト一覧リソース"""
        projects = await self.db_manager.list_projects()
        return {"projects": projects}
    
    @resource(uri="rag://search/{project}/{query}")
    async def cached_search(self, project: str, query: str) -> Dict[str, Any]:
        """キャッシュされた検索結果リソース"""
        # キャッシュチェック
        # なければ検索実行
        pass
    
    @prompt(name="rag_search_context")
    async def search_context_prompt(self, query: str) -> str:
        """検索コンテキストプロンプト"""
        results = await self.rag_search(query, top_k=3)
        
        context = f"Based on the search query '{query}', "
        context += "here are related documents:\n\n"
        
        for i, result in enumerate(results["results"], 1):
            context += f"{i}. {result['file_path']}:\n"
            context += f"   {result['text'][:200]}...\n\n"
        
        return context
```

### エラーハンドリング

```python
class RAGMCPError(Exception):
    """MCP Server base exception"""
    pass

class IndexError(RAGMCPError):
    """インデックス作成エラー"""
    pass

class SearchError(RAGMCPError):
    """検索エラー"""
    pass

@tool()
async def rag_search(self, query: str, **kwargs):
    try:
        # 検索実行
        results = await self.search_engine.search(query, **kwargs)
        return {"success": True, "results": results}
    
    except SearchError as e:
        return {
            "success": False,
            "error": "search_failed",
            "message": str(e)
        }
    
    except Exception as e:
        logger.error(f"Unexpected error in rag_search: {e}")
        return {
            "success": False,
            "error": "internal_error",
            "message": "An unexpected error occurred"
        }
```

## ClaudeCodeとの統合

### 設定ファイル例

```json
// claude_desktop_config.json
{
  "mcpServers": {
    "rag-system": {
      "command": "python",
      "args": ["-m", "rag.mcp"],
      "env": {
        "RAG_PROJECT": "my_project",
        "RAG_CONFIG_PATH": "~/.rag/config.yaml",
        "RAG_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 使用シナリオ

#### シナリオ1: コード編集中の自動参照
```
1. ユーザーが認証機能のコードを編集
2. ClaudeCodeが自動的にrag_suggestを呼び出し
3. 関連する設計書や仕様書を提案
4. AIが文脈を理解して適切なアドバイス
```

#### シナリオ2: 質問応答時の自動検索
```
1. ユーザー「このAPIの仕様を教えて」
2. ClaudeCodeが自動的にrag_searchを実行
3. 関連ドキュメントを取得
4. AIが正確な情報を基に回答
```

#### シナリオ3: ドキュメント自動更新
```
1. ユーザーが設計書を更新して保存
2. ClaudeCodeがrag_indexを自動実行
3. ベクトルDBが最新状態に
4. 次回検索時に最新情報を参照
```

## パフォーマンス考慮事項

### 1. 非同期処理
- すべてのツールは非同期実装
- 大量ファイルのインデックスは進捗を返す

### 2. キャッシュ戦略
- 頻繁な検索クエリはキャッシュ
- TTLベースの自動無効化

### 3. バッチ処理
- 複数ファイルのインデックスはバッチ化
- ベクトル化は一括処理

## セキュリティ考慮事項

### 1. ローカル限定
- localhost接続のみ許可
- 外部ネットワークアクセスなし

### 2. ファイルアクセス制限
- 設定されたプロジェクトディレクトリのみ
- シンボリックリンクの追跡制限

### 3. サニタイゼーション
- 入力パラメータの検証
- パストラバーサル攻撃の防止