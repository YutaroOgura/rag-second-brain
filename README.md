# RAG Second Brain

日本語と英語の混在ドキュメントに対応した高精度な検索システム。MCP (Model Context Protocol) 統合により、Claude/ChatGPTから直接アクセス可能。

## 🎯 主な特徴

- **日本語形態素解析**: MeCab代替の軽量な日本語処理エンジン
- **ハイブリッド検索**: Vector + Keyword + Grep の3層検索
- **MCP統合**: Claude Codeから直接利用可能
- **フォールバック機能**: 検索失敗時の3段階リトライ
- **トークン最適化**: MCP制限（25,000トークン）内で動作

## 📊 検索精度の改善実績

| 検索クエリ | 改善前 | 改善後 | 改善率 |
|-----------|--------|--------|--------|
| Slack通知 | 0.14 | 0.59 | **4.2倍** |
| API認証 | 0.22 | 0.68 | **3.1倍** |
| Docker環境 | 0.18 | 0.55 | **3.0倍** |

## 📚 ドキュメント

詳細なドキュメントは[docs/INDEX.md](docs/INDEX.md)を参照：

- [アーキテクチャ設計](docs/architecture/ARCHITECTURE.md)
- [実装ガイド](docs/implementation/IMPLEMENTATION_PLAN.md)
- [MCPセットアップ](docs/setup/MCP_SETUP_GUIDE.md)
- [運用マニュアル](docs/operations/OPERATIONS_MANUAL.md)

## 🚀 クイックスタート

### インストール
```bash
# リポジトリのクローン
git clone https://github.com/yourusername/rag-second-brain.git
cd rag-second-brain

# Python環境のセットアップ
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 設定ファイルの準備
cp .env.example .env
```

### MCP統合（Claude Code用）
```json
// .mcp.json に追加
{
  "mcpServers": {
    "rag-second-brain": {
      "command": "node",
      "args": ["/path/to/rag-second-brain/mcp-server.js"],
      "env": {
        "RAG_HOME": "/home/username/.rag"
      }
    }
  }
}
```

### 基本的な使い方
```bash
# ドキュメントのインデックス作成
rag index /path/to/documents --project myproject

# 検索実行（複数の検索モード）
rag search "検索クエリ" --type hybrid --top-k 5
rag search "Slack通知" --type hybrid_grep  # Grep+Vector検索

# プロジェクト統計表示
rag stats --project myproject
```

## 🏗️ プロジェクト構造

```
rag-second-brain/
├── src/                    # ソースコード
│   ├── japanese_analyzer.py  # 日本語形態素解析
│   ├── dictionary_generator.py # 辞書生成
│   ├── query_preprocessor.py # クエリ前処理
│   └── fallback_search.py    # フォールバック検索
├── mcp-server.js          # MCP統合サーバー
├── tests/                  # テストコード
├── docs/                   # ドキュメント
│   ├── architecture/      # アーキテクチャ設計
│   ├── implementation/    # 実装詳細
│   ├── operations/        # 運用ガイド
│   ├── reports/          # レポート
│   └── setup/            # セットアップガイド
└── data/                  # データファイル
```

## 🔧 技術スタック

- **言語**: Python 3.10+ / Node.js 18+
- **ベクトルDB**: ChromaDB
- **埋め込みモデル**: intfloat/multilingual-e5-base
- **日本語処理**: カスタム形態素解析エンジン
- **MCP統合**: Node.js MCPサーバー

## 📈 開発フェーズ

### Phase 1: フォールバック検索 ✅
- 3段階フォールバック検索実装
- 検索精度4.2倍改善達成
- 複合語前処理機能

### Phase 2: 日本語最適化 ✅
- MeCab代替の軽量形態素解析
- 専門用語辞書（50+用語）
- 複合語抽出機能

### Phase 3: MCP改善 ✅
- トークン制限対策（80文字制限）
- Grep+Vectorハイブリッド検索
- MCPレスポンス最適化

## 🧪 テスト

```bash
# 単体テスト実行
python -m pytest tests/

# 統合テスト
python tests/test_phase2_integration.py

# 改善効果の確認
./test_hybrid_search.sh
```

## 🤝 コントリビューション

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## 📄 ライセンス

MIT License

---

**最終更新**: 2025年8月25日  
**バージョン**: 2.0.0 (Phase 2完了)