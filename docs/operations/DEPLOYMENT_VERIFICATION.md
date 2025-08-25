# 🧠「第2の脳」RAGシステム - デプロイメント検証ガイド

## 🎯 検証概要

このドキュメントは、「第2の脳」RAGシステムの他プロジェクトへの展開前に実行すべき検証手順を定義します。

---

## ✅ 検証チェックリスト

### Phase 1: 環境準備検証

#### 1.1 システム要件確認
```bash
# Python バージョン確認
python3 --version  # 3.8+ が必要

# 必要コマンドの存在確認
command -v git || echo "Git が必要です"
command -v curl || echo "Curl が必要です"
command -v pip || echo "Pip が必要です"

# システムリソース確認
free -h  # メモリ4GB+推奨
df -h    # ストレージ2GB+推奨
```

#### 1.2 ネットワーク接続確認
```bash
# PyPIへの接続確認
pip install --dry-run requests

# GitHubへの接続確認
curl -I https://github.com/

# 外部APIアクセス確認（必要な場合）
curl -I https://huggingface.co/
```

### Phase 2: インストール検証

#### 2.1 自動セットアップ検証
```bash
# セットアップスクリプトの実行
curl -sSL https://raw.githubusercontent.com/your-repo/rag-documents/main/setup.sh | bash

# インストール成功確認
source ~/.bashrc
which rag
rag --version
```

#### 2.2 手動インストール検証
```bash
# リポジトリクローン
git clone https://github.com/your-repo/rag-documents.git
cd rag-documents

# 依存関係インストール
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .

# 基本動作確認
python3 -c "from rag.core.database import DatabaseManager; print('✓ Import successful')"
```

#### 2.3 Docker検証
```bash
# Dockerイメージビルド
docker build -t rag-second-brain:latest .

# コンテナ起動確認
docker run --rm rag-second-brain:latest --help

# Docker Compose検証
docker-compose up -d
docker-compose ps
docker-compose logs
docker-compose down
```

### Phase 3: 基本機能検証

#### 3.1 CLI基本機能
```bash
# ヘルプ表示確認
rag --help
rag search --help
rag index --help

# 設定確認
rag stats

# テストドキュメント作成
mkdir -p test_docs
echo "# テストドキュメント\nこれはテスト用のドキュメントです。" > test_docs/test.md

# インデックス作成
rag index test_docs --project test-project --recursive

# 検索実行
rag search "テスト" --type vector --top-k 3
rag search "テスト" --type keyword --top-k 3
rag search "テスト" --type hybrid --top-k 3

# プロジェクト管理
rag projects
rag documents --project test-project
```

#### 3.2 多言語対応確認
```bash
# 日本語ドキュメント
echo "# 日本語テスト\n機械学習とデータサイエンスについて" > test_docs/japanese.md

# 英語ドキュメント
echo "# English Test\nMachine learning and data science concepts" > test_docs/english.md

# インデックス作成と検索
rag index test_docs --project multilang-test --recursive
rag search "機械学習" --project multilang-test
rag search "machine learning" --project multilang-test
```

### Phase 4: MCP統合検証

#### 4.1 MCPサーバー起動確認
```bash
# MCPサーバー手動起動テスト
python3 -m rag.mcp.server &
MCP_PID=$!

# サーバープロセス確認
ps aux | grep "rag.mcp.server"

# サーバー停止
kill $MCP_PID
```

#### 4.2 ClaudeCode統合確認
```bash
# MCPサーバー設定確認
cat ~/.claude_code_mcp.json

# 設定ファイルの妥当性確認（JSONバリデーション）
python3 -c "import json; json.load(open('~/.claude_code_mcp.json'.replace('~', '$HOME')))"
```

### Phase 5: パフォーマンス検証

#### 5.1 大量ドキュメント処理
```bash
# テストドキュメント大量作成
mkdir -p perf_test
for i in {1..100}; do
  echo "# Document $i\nThis is test document number $i with some content for testing purposes." > perf_test/doc_$i.md
done

# パフォーマンス測定
time rag index perf_test --project perf-test --recursive

# 検索パフォーマンス
time rag search "test" --project perf-test --top-k 10
```

#### 5.2 メモリ使用量監視
```bash
# メモリ使用量確認（バックグラウンド実行）
(
  while true; do
    ps aux | grep rag | grep -v grep | awk '{print $6}' | paste -sd+ | bc
    sleep 5
  done
) &
MONITOR_PID=$!

# 検索実行
rag search "test" --project perf-test --top-k 50

# モニタリング停止
kill $MONITOR_PID
```

### Phase 6: エラーハンドリング検証

#### 6.1 設定ファイル異常系
```bash
# 不正な設定ファイル作成
cp ~/.rag/config.yaml ~/.rag/config.yaml.backup
echo "invalid: yaml: content" > ~/.rag/config.yaml

# エラーハンドリング確認
rag stats 2>&1 | grep -i error

# 設定復旧
mv ~/.rag/config.yaml.backup ~/.rag/config.yaml
```

#### 6.2 存在しないファイル・ディレクトリ
```bash
# 存在しないディレクトリをインデックス
rag index /non/existent/path --project error-test 2>&1 | grep -i error

# 存在しないプロジェクトで検索
rag search "test" --project non-existent-project 2>&1 | grep -i error
```

#### 6.3 権限エラー
```bash
# 権限のないディレクトリ作成
sudo mkdir -p /root/protected_docs
sudo echo "protected content" > /root/protected_docs/protected.md
sudo chmod 600 /root/protected_docs/protected.md

# 権限エラーハンドリング確認
rag index /root/protected_docs --project permission-test 2>&1 | grep -i permission
```

---

## 🚦 検証結果判定基準

### ✅ 成功基準

#### インストール
- [ ] セットアップスクリプト完了（終了コード0）
- [ ] `rag --help` 正常実行
- [ ] 必要なPythonパッケージ全てインストール完了

#### 基本機能
- [ ] ドキュメントインデックス成功
- [ ] 3つの検索タイプすべて動作
- [ ] 検索結果に適切なスコア・メタデータ含む
- [ ] プロジェクト管理機能動作

#### パフォーマンス
- [ ] 100ドキュメントのインデックス < 2分
- [ ] 検索レスポンス < 5秒
- [ ] メモリ使用量 < 2GB

#### 統合
- [ ] MCPサーバー起動成功
- [ ] ClaudeCode設定ファイル正常

### ⚠️ 警告条件
- インデックス時間 > 2分（性能調整推奨）
- 検索時間 > 5秒（チューニング推奨）
- メモリ使用量 > 2GB（リソース確認推奨）

### ❌ 失敗条件
- セットアップスクリプト異常終了
- 基本検索機能が動作しない
- MCPサーバー起動失敗
- メモリ使用量 > 4GB

---

## 🛠️ トラブルシューティングガイド

### よくある問題と解決策

#### 問題1: ModuleNotFoundError
```bash
# 解決策: 仮想環境の再作成
rm -rf ~/.rag/venv
python3 -m venv ~/.rag/venv
source ~/.rag/venv/bin/activate
pip install -r requirements.txt
```

#### 問題2: Permission denied
```bash
# 解決策: ディレクトリ権限の修正
sudo chown -R $USER:$USER ~/.rag/
chmod -R 755 ~/.rag/
```

#### 問題3: GPU not available
```yaml
# 解決策: config.yamlの修正
embedding:
  device: "cpu"  # GPUからCPUに変更
```

#### 問題4: ポート競合
```yaml
# 解決策: docker-compose.ymlポート変更
services:
  rag-mcp-server:
    ports:
      - "8002:8000"  # 別ポートに変更
```

---

## 📝 検証レポートテンプレート

### 検証実行情報
- **実行日時**: ___________
- **実行環境**: ___________
- **実行者**: ___________
- **バージョン**: ___________

### 検証結果
- **Phase 1 - 環境準備**: ✅ / ⚠️ / ❌
- **Phase 2 - インストール**: ✅ / ⚠️ / ❌
- **Phase 3 - 基本機能**: ✅ / ⚠️ / ❌
- **Phase 4 - MCP統合**: ✅ / ⚠️ / ❌
- **Phase 5 - パフォーマンス**: ✅ / ⚠️ / ❌
- **Phase 6 - エラーハンドリング**: ✅ / ⚠️ / ❌

### 問題・改善点
```
[発見された問題や改善が必要な点を記載]
```

### 総合判定
- **プロダクション展開可否**: ✅ 可能 / ⚠️ 条件付き可能 / ❌ 要修正

---

## 🎯 次ステップ

### 検証成功時
1. プロダクション環境への展開実行
2. 運用監視設定
3. ユーザートレーニング実施
4. フィードバック収集開始

### 検証失敗時
1. 問題の根本原因分析
2. 修正版の開発・テスト
3. 再検証実行
4. ドキュメント更新

---

**🎉 検証完了後、安心してプロダクション展開を実行できます！**