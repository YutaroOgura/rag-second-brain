#!/bin/bash
set -e

# 「第2の脳」RAGシステム Dockerエントリーポイント

# 色付きログ
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 初期化処理
initialize() {
    log_info "RAG Second Brain システムを初期化中..."
    
    # データディレクトリの確認と作成
    mkdir -p /app/data/chroma /app/logs
    
    # 設定ファイルの存在確認
    if [ ! -f "$RAG_CONFIG_PATH" ]; then
        log_warning "設定ファイルが見つかりません: $RAG_CONFIG_PATH"
        log_info "デフォルト設定を使用します"
        
        # デフォルト設定を作成
        mkdir -p /app/config
        cat > /app/config/config.yaml << EOF
database:
  type: chromadb
  path: "/app/data/chroma"
  collection_name: "documents"

embedding:
  model: "sentence-transformers/multilingual-e5-base"
  batch_size: 32
  device: "cpu"

chunking:
  strategy: "fixed"
  chunk_size: 1000
  chunk_overlap: 200
  separator: "\n\n"

search:
  default_top_k: 5
  hybrid_alpha: 0.5

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "/app/logs/rag.log"
EOF
    fi
    
    # サンプルデータの初期インデックス（初回起動時のみ）
    if [ ! -f /app/data/.initialized ]; then
        log_info "初回起動: サンプルデータをインデックス中..."
        python3 -m rag.cli.main index /app/samples --project sample --recursive || log_warning "サンプルデータのインデックスに失敗"
        touch /app/data/.initialized
        log_success "サンプルデータのインデックス完了"
    fi
    
    log_success "初期化完了"
}

# コマンド実行
case "$1" in
    "cli")
        initialize
        log_info "CLIモードで起動"
        exec python3 -m rag.cli.main "${@:2}"
        ;;
    "mcp-server")
        initialize
        log_info "MCPサーバーモードで起動"
        exec python3 -m rag.mcp.server
        ;;
    "test")
        log_info "テストモードで起動"
        exec python3 -m pytest tests/ -v
        ;;
    "shell")
        initialize
        log_info "インタラクティブシェルで起動"
        exec /bin/bash
        ;;
    "help")
        echo "使用可能なコマンド:"
        echo "  cli [args]     - CLIモード（デフォルト）"
        echo "  mcp-server     - MCPサーバーモード"
        echo "  test           - テスト実行"
        echo "  shell          - インタラクティブシェル"
        echo "  help           - このヘルプメッセージ"
        echo ""
        echo "CLI使用例:"
        echo "  docker run rag-second-brain cli search '認証システム'"
        echo "  docker run rag-second-brain cli index /data --project my-project"
        echo "  docker run rag-second-brain cli stats"
        ;;
    *)
        # 任意のコマンド実行
        initialize
        log_info "カスタムコマンド実行: $*"
        exec "$@"
        ;;
esac