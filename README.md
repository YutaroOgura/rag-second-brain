# 第2の脳 RAGシステム - Second Brain for Development

## 🧠 コンセプト
**「開発しながら作る第2の脳」**

開発プロセスで生成される知識・経験・ドキュメントを自動的に蓄積し、必要な時に即座にアクセスできる個人専用の知識ベースシステム。

## 🎯 特徴

- **MCPサーバー**: ClaudeCodeからネイティブアクセス
- **CLIツール**: コマンドラインから高速検索
- **自動記録**: 開発しながら知識が蓄積
- **文脈認識**: 現在の作業に関連する情報を自動提案
- **完全ローカル**: プライバシー保護、高速レスポンス

## 📚 ドキュメント

- [CONCEPT.md](./CONCEPT.md) - システムコンセプト
- [REQUIREMENTS.md](./REQUIREMENTS.md) - 要件定義書
- [ARCHITECTURE.md](./ARCHITECTURE.md) - アーキテクチャ設計
- [MCP_SPECIFICATION.md](./MCP_SPECIFICATION.md) - MCPサーバー仕様
- [CLI_DESIGN.md](./CLI_DESIGN.md) - CLIツール設計

## 🚀 クイックスタート

### インストール
```bash
# 開発環境
git clone <repository>
cd rag_documents
pip install -e .

# グローバルインストール
pipx install .
```

### MCPサーバー設定
```json
// claude_desktop_config.json に追加
{
  "mcpServers": {
    "rag-system": {
      "command": "python",
      "args": ["-m", "rag.mcp"],
      "env": {
        "RAG_PROJECT": "my_project"
      }
    }
  }
}
```

### 基本的な使い方
```bash
# ドキュメント登録
rag index ./docs/ --recursive

# 検索
rag search "認証機能の実装"

# インタラクティブモード
rag interactive
```

## 🏗️ プロジェクト構造

```
rag_documents/
├── rag/                 # メインパッケージ
│   ├── core/           # 共通コア機能
│   ├── cli/            # CLIインターフェース
│   └── mcp/            # MCPサーバー
├── data/               # データ保存
│   └── chroma/         # ベクトルDB
└── tests/              # テスト
```

## 🔧 技術スタック

- **言語**: Python 3.10+
- **ベクトルDB**: ChromaDB
- **埋め込みモデル**: sentence-transformers
- **CLIフレームワーク**: Click
- **MCPサーバー**: MCP SDK

## 📈 ロードマップ

### Phase 1: MVP ✅
- 基本的な検索・登録機能
- CLIツール実装
- MCPサーバー実装

### Phase 2: 拡張機能 🚧
- ハイブリッド検索
- メタデータフィルタリング
- インタラクティブモード

### Phase 3: 外部連携 📅
- Jira/Confluence連携
- キャッシュ管理
- Web検索結果の統合

## 🤝 コントリビューション

個人利用を前提としていますが、改善提案は歓迎します。

## 📄 ライセンス

個人利用限定

---

*"Your Second Brain for Development - 開発のための第2の脳"*