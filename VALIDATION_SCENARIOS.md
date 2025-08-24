# 🧪 「第2の脳」RAGシステム 検証シナリオ

## 📋 検証の目的
他プロジェクトでの実運用前に、システムの安定性・性能・使用性を包括的に検証

---

## 🎯 検証シナリオ一覧

### Phase 1: 基盤システム検証 ⚡

#### Scenario 1.1: 環境セットアップ検証
**目的**: 新しい環境での確実なセットアップ
```bash
# ローカル環境での検証
./deploy.sh test
```

**成功基準**:
- [ ] セットアップが10分以内に完了
- [ ] 全ての依存関係が正常にインストール
- [ ] 基本コマンドが実行可能
- [ ] 設定ファイルが正常に作成

**検証コマンド**:
```bash
# 基本動作確認
rag --help
rag stats
python3 -c "from rag.core.database import DatabaseManager; print('OK')"
```

#### Scenario 1.2: Docker環境検証
**目的**: コンテナ環境での動作確認
```bash
# Docker環境での検証
./deploy.sh docker
```

**成功基準**:
- [ ] Dockerイメージが正常にビルド
- [ ] コンテナが正常起動（5分以内）
- [ ] ヘルスチェックが成功
- [ ] ボリュームマウントが正常動作

**検証コマンド**:
```bash
docker run rag-second-brain:latest cli --help
docker run rag-second-brain:latest cli stats
docker-compose ps
docker-compose logs
```

---

### Phase 2: 機能検証 🛠️

#### Scenario 2.1: ドキュメントインデックス検証
**目的**: 様々な形式のドキュメントが正常にインデックスされる

**テストデータ**:
```bash
# テストドキュメントの作成
mkdir -p test_docs

# Markdown
cat > test_docs/auth_system.md << 'EOF'
# 認証システム設計

## JWT認証の実装
- トークン生成: `jwt.sign()`
- 検証: `jwt.verify()`
- リフレッシュ: `jwt.refresh()`

## セキュリティ対策
1. HTTPS必須
2. トークン有効期限設定
3. リフレッシュトークンローテーション
EOF

# HTML
cat > test_docs/database_design.html << 'EOF'
<h1>データベース設計指針</h1>
<h2>正規化</h2>
<p>第3正規形まで実施</p>
<h2>インデックス戦略</h2>
<ul>
<li>プライマリキー</li>
<li>外部キー</li>
<li>検索条件カラム</li>
</ul>
EOF

# テキストファイル
cat > test_docs/api_specification.txt << 'EOF'
API仕様書

エンドポイント一覧:
- POST /auth/login - ログイン
- GET /users/profile - プロファイル取得
- PUT /users/profile - プロファイル更新
- DELETE /auth/logout - ログアウト
EOF
```

**検証手順**:
```bash
# 単一ファイルインデックス
rag index test_docs/auth_system.md --project test-project

# ディレクトリ一括インデックス
rag index test_docs --project test-project --recursive

# インデックス結果確認
rag documents --project test-project
rag stats
```

**成功基準**:
- [ ] 全ファイル形式（MD, HTML, TXT）が正常インデックス
- [ ] 日本語コンテンツが正常処理
- [ ] メタデータが正確に抽出
- [ ] プロジェクトIDが正しく設定

#### Scenario 2.2: 検索機能検証
**目的**: 各種検索タイプが期待通りに動作

**検証クエリ**:
```bash
# ベクトル検索（セマンティック）
rag search "認証システムの実装方法" --type vector --top-k 3

# キーワード検索
rag search "JWT トークン" --type keyword --top-k 3

# ハイブリッド検索
rag search "データベース 設計 パフォーマンス" --type hybrid --alpha 0.5 --top-k 5

# プロジェクトフィルタ検索
rag search "API" --project test-project --type vector
```

**成功基準**:
- [ ] 各検索タイプが適切な結果を返す
- [ ] スコア順でソートされている
- [ ] プロジェクトフィルタが機能
- [ ] 日本語クエリが正常処理
- [ ] レスポンス時間 < 3秒

#### Scenario 2.3: 出力フォーマット検証
**目的**: 様々な出力形式が正常動作

```bash
# テーブル出力（デフォルト）
rag search "認証" --format table

# JSON出力
rag search "認証" --format json > results.json
cat results.json | jq .

# シンプル出力
rag search "認証" --format simple
```

**成功基準**:
- [ ] テーブル出力が読みやすく表示
- [ ] JSON出力が有効なJSON形式
- [ ] シンプル出力が機械処理に適用
- [ ] 文字化けなし

---

### Phase 3: 統合検証 🔄

#### Scenario 3.1: ClaudeCode統合検証
**目的**: MCPサーバー経由でClaudeCodeから利用可能

**前提条件**:
```json
// ~/.claude_code_mcp.json
{
  "mcpServers": {
    "rag-second-brain": {
      "command": "python3",
      "args": ["-m", "rag.mcp.server"],
      "cwd": "/path/to/rag-documents",
      "env": {
        "RAG_CONFIG_PATH": "/path/to/config.yaml"
      }
    }
  }
}
```

**検証手順**:
1. ClaudeCodeを再起動
2. MCPサーバーが認識されることを確認
3. 以下のコマンドをClaudeCodeで実行:

```
@rag_search query="認証システム" search_type="hybrid" top_k=3
@rag_stats
@rag_index path="./new_docs" project_id="test" recursive=true
```

**成功基準**:
- [ ] MCPサーバーが正常起動
- [ ] ClaudeCodeから検索実行可能
- [ ] 結果が適切にフォーマット表示
- [ ] エラーハンドリングが適切

#### Scenario 3.2: 実プロジェクト検証
**目的**: 実際のプロジェクトドキュメントでの動作確認

**検証手順**:
```bash
# 実際のプロジェクトドキュメントを使用
rag index ~/projects/frontend/README.md --project frontend
rag index ~/projects/backend/docs --project backend --recursive
rag index ~/work/specifications --project specs --recursive

# 実際の開発シナリオでの検索
rag search "React hooks useEffect" --project frontend
rag search "API エラーハンドリング" --project backend
rag search "要件定義 ユーザーストーリー" --project specs
```

**成功基準**:
- [ ] 100+ ドキュメントが正常処理
- [ ] 実際の開発クエリに有用な回答
- [ ] レスポンス時間が実用レベル
- [ ] メモリ使用量が適切

---

### Phase 4: 性能・負荷検証 ⚡

#### Scenario 4.1: 大量データ検証
**目的**: 大量ドキュメントでの性能確認

**テストデータ作成**:
```bash
# 大量テストデータの生成
mkdir -p large_test_docs
for i in {1..100}; do
    cat > large_test_docs/doc_$i.md << EOF
# ドキュメント $i

## 概要
これはテスト用ドキュメント$iです。
認証システム、データベース設計、API仕様について記載します。

## 技術詳細
- 技術スタック: React, Node.js, PostgreSQL
- 認証方式: JWT
- データベース: PostgreSQL
- インフラ: Docker, AWS

## 実装詳細$i
具体的な実装方法について説明します。
EOF
done
```

**性能測定**:
```bash
# インデックス性能
time rag index large_test_docs --project large-test --recursive

# 検索性能
time rag search "認証システム 実装"
time rag search "データベース 設計"
time rag search "API 仕様"

# 統計確認
rag stats
```

**成功基準**:
- [ ] 100ドキュメントのインデックス < 5分
- [ ] 検索レスポンス < 3秒
- [ ] メモリ使用量 < 2GB
- [ ] システムが安定動作

#### Scenario 4.2: 継続運用検証
**目的**: 長期運用での安定性確認

**継続テスト**:
```bash
# 継続検索テスト（1時間）
for i in {1..360}; do
    rag search "テスト検索 $((i % 10))" --top-k 3 > /dev/null
    sleep 10
done

# リソース監視
while true; do
    ps aux | grep -E "(python.*rag|chromadb)" >> resource_usage.log
    sleep 60
done
```

**成功基準**:
- [ ] メモリリーク無し
- [ ] レスポンス時間が安定
- [ ] エラー発生無し
- [ ] CPUが安定

---

### Phase 5: エラー処理・復旧検証 🚨

#### Scenario 5.1: 異常系テスト
**目的**: エラー条件での適切な処理確認

```bash
# 存在しないファイルのインデックス
rag index /nonexistent/file.md --project test

# 空クエリでの検索
rag search "" --type vector

# 無効なプロジェクトでの検索
rag search "test" --project nonexistent-project

# 破損した設定ファイル
echo "invalid: yaml: content:" > ~/.rag/config.yaml
rag stats
```

**成功基準**:
- [ ] 適切なエラーメッセージ表示
- [ ] システムクラッシュ無し
- [ ] 復旧手順が明確
- [ ] ログに適切な情報記録

#### Scenario 5.2: データ復旧テスト
**目的**: データ損失からの復旧確認

```bash
# データベースの削除
rm -rf ~/.rag/data/chroma

# 復旧確認
rag stats  # エラー表示確認
rag index test_docs --project recovery-test --recursive  # 再構築
rag search "認証" --type vector  # 動作確認
```

**成功基準**:
- [ ] データ損失を適切に検出
- [ ] 再インデックスが正常実行
- [ ] データが完全復旧

---

## 📊 検証結果テンプレート

### 検証実行記録
```markdown
## 検証実行結果

**実行日**: YYYY-MM-DD
**実行者**: [名前]
**環境**: [OS/Python version/etc]

### Phase 1: 基盤システム検証
- [ ] Scenario 1.1: 環境セットアップ検証 - ✅/❌
- [ ] Scenario 1.2: Docker環境検証 - ✅/❌

### Phase 2: 機能検証  
- [ ] Scenario 2.1: ドキュメントインデックス検証 - ✅/❌
- [ ] Scenario 2.2: 検索機能検証 - ✅/❌
- [ ] Scenario 2.3: 出力フォーマット検証 - ✅/❌

### Phase 3: 統合検証
- [ ] Scenario 3.1: ClaudeCode統合検証 - ✅/❌
- [ ] Scenario 3.2: 実プロジェクト検証 - ✅/❌

### Phase 4: 性能・負荷検証
- [ ] Scenario 4.1: 大量データ検証 - ✅/❌
- [ ] Scenario 4.2: 継続運用検証 - ✅/❌

### Phase 5: エラー処理・復旧検証
- [ ] Scenario 5.1: 異常系テスト - ✅/❌
- [ ] Scenario 5.2: データ復旧テスト - ✅/❌

### 総合判定
- [ ] 本格運用可能 - ✅/❌
```

---

## 🚀 検証実行スクリプト

自動化された検証を実行するスクリプト:

```bash
#!/bin/bash
# validation.sh - 自動検証スクリプト

echo "🧪 RAGシステム 自動検証開始"

# Phase 1: 基盤検証
echo "📋 Phase 1: 基盤システム検証"
./deploy.sh test --skip-tests
if [ $? -eq 0 ]; then echo "✅ 環境セットアップ OK"; else echo "❌ 環境セットアップ NG"; fi

# Phase 2: 機能検証  
echo "📋 Phase 2: 機能検証"
# ... 各シナリオの実行

# 検証結果レポート生成
echo "📊 検証結果レポート生成"
python3 generate_validation_report.py

echo "🎉 自動検証完了"
```

これらの検証シナリオを通じて、「第2の脳」RAGシステムが他プロジェクトで確実に運用可能であることを保証します。

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "\u30d7\u30ed\u30b8\u30a7\u30af\u30c8\u7ba1\u7406\u8a08\u753b\u306e\u7b56\u5b9a", "status": "completed", "activeForm": "\u30d7\u30ed\u30b8\u30a7\u30af\u30c8\u7ba1\u7406\u8a08\u753b\u7b56\u5b9a\u5b8c\u4e86"}, {"content": "\u30c7\u30d7\u30ed\u30a4\u30e1\u30f3\u30c8\u7528\u30b9\u30af\u30ea\u30d7\u30c8\u3092\u4f5c\u6210", "status": "completed", "activeForm": "\u30c7\u30d7\u30ed\u30a4\u30e1\u30f3\u30c8\u7528\u30b9\u30af\u30ea\u30d7\u30c8\u4f5c\u6210\u5b8c\u4e86"}, {"content": "\u904b\u7528\u30de\u30cb\u30e5\u30a2\u30eb\u3092\u4f5c\u6210", "status": "completed", "activeForm": "\u904b\u7528\u30de\u30cb\u30e5\u30a2\u30eb\u4f5c\u6210\u5b8c\u4e86"}, {"content": "Docker\u5316\u3092\u691c\u8a0e\u30fb\u5b9f\u88c5", "status": "completed", "activeForm": "Docker\u5316\u3092\u5b9f\u88c5\u5b8c\u4e86"}, {"content": "\u74b0\u5883\u69cb\u7bc9\u81ea\u52d5\u5316\u30b9\u30af\u30ea\u30d7\u30c8\u3092\u4f5c\u6210", "status": "completed", "activeForm": "\u74b0\u5883\u69cb\u7bc9\u81ea\u52d5\u5316\u30b9\u30af\u30ea\u30d7\u30c8\u4f5c\u6210\u5b8c\u4e86"}, {"content": "\u30c6\u30b9\u30c8\u74b0\u5883\u3067\u306e\u691c\u8a3c\u30b7\u30ca\u30ea\u30aa\u4f5c\u6210", "status": "completed", "activeForm": "\u30c6\u30b9\u30c8\u74b0\u5883\u3067\u306e\u691c\u8a3c\u30b7\u30ca\u30ea\u30aa\u4f5c\u6210\u5b8c\u4e86"}, {"content": "\u6700\u7d42\u30c7\u30ea\u30d0\u30ea\u30fc\u30d1\u30c3\u30b1\u30fc\u30b8\u306e\u4f5c\u6210", "status": "in_progress", "activeForm": "\u6700\u7d42\u30c7\u30ea\u30d0\u30ea\u30fc\u30d1\u30c3\u30b1\u30fc\u30b8\u4f5c\u6210\u4e2d"}]