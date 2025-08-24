# 「第2の脳」RAGシステム Dockerfile
FROM python:3.11-slim

# メタデータ
LABEL maintainer="your.email@example.com"
LABEL version="1.0"
LABEL description="RAG Second Brain System - A Second Brain for Development"

# 環境変数
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV RAG_HOME=/app
ENV RAG_CONFIG_PATH=/app/config/config.yaml
ENV RAG_DATA_PATH=/app/data

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリの設定
WORKDIR /app

# Pythonの依存関係ファイルをコピー
COPY requirements.txt .

# Python依存関係のインストール
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY rag/ ./rag/
COPY config.yaml ./config/config.yaml
COPY setup.py .
COPY pytest.ini .

# データディレクトリの作成
RUN mkdir -p /app/data /app/logs /app/samples

# サンプルデータの作成
RUN cat > /app/samples/sample_auth.md << 'EOF'
# 認証システム設計

## 概要
JWTトークンを使用した認証システムの設計について説明します。

## 認証フロー
1. ユーザーがログイン情報を入力
2. サーバーが認証情報を検証
3. 有効な場合、JWTトークンを発行
4. クライアントはトークンを保存
5. 以降のAPIリクエストでトークンを送信

## セキュリティ考慮事項
- トークンの有効期限設定
- リフレッシュトークンの実装
- HTTPS通信の必須化
- XSS対策
EOF

RUN cat > /app/samples/sample_database.md << 'EOF'
# データベース設計指針

## 設計原則
1. 正規化による重複排除
2. 適切なインデックス設計
3. パフォーマンスを考慮したクエリ設計

## テーブル設計
### users テーブル
- id: PRIMARY KEY
- email: UNIQUE, NOT NULL
- password_hash: NOT NULL
- created_at: TIMESTAMP
- updated_at: TIMESTAMP

## 最適化手法
- インデックスの適切な配置
- クエリの実行計画確認
- 定期的な統計情報更新
EOF

# パッケージのインストール
RUN pip install -e .

# 非rootユーザーの作成
RUN useradd --create-home --shell /bin/bash raguser \
    && chown -R raguser:raguser /app
USER raguser

# ヘルスチェックスクリプト
COPY healthcheck.sh /app/healthcheck.sh
USER root
RUN chmod +x /app/healthcheck.sh
USER raguser

# ポートの公開（MCPサーバー用）
EXPOSE 8000

# ボリューム定義
VOLUME ["/app/data", "/app/logs", "/app/config"]

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/healthcheck.sh

# エントリーポイント
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
USER root
RUN chmod +x /app/docker-entrypoint.sh
USER raguser

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["cli"]