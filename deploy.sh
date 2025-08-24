#!/bin/bash

# 「第2の脳」RAGシステム デプロイ自動化スクリプト
# 複数の環境（ローカル、Docker、プロダクション）への対応

set -e

# 色付きログ
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${PURPLE}[STEP]${NC} $1"; }

# バージョン情報
VERSION="1.0.0"
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# デフォルト値
DEPLOYMENT_TYPE="local"
PROJECT_NAME="rag-second-brain"
SKIP_TESTS=false
FORCE_REBUILD=false

# ヘルプメッセージ
show_help() {
    cat << EOF
🧠 「第2の脳」RAGシステム デプロイスクリプト v${VERSION}

Usage: $0 [OPTIONS] DEPLOYMENT_TYPE

DEPLOYMENT_TYPES:
  local      ローカル環境へのインストール（デフォルト）
  docker     Dockerコンテナでの実行
  production プロダクション環境へのデプロイ
  test       テスト環境での検証

OPTIONS:
  -h, --help              このヘルプを表示
  -v, --version           バージョン情報を表示
  -n, --name NAME         プロジェクト名（デフォルト: rag-second-brain）
  -s, --skip-tests        テストをスキップ
  -f, --force-rebuild     強制リビルド
  --config FILE           設定ファイルのパス
  --data-dir DIR          データディレクトリのパス

Examples:
  $0 local                     ローカル環境にインストール
  $0 docker                    Docker環境で起動
  $0 production --force-rebuild プロダクション環境に強制デプロイ
  $0 test --skip-tests         テスト環境で検証（テストスキップ）
EOF
}

# バージョン情報表示
show_version() {
    echo "RAG Second Brain Deployment Script"
    echo "Version: ${VERSION}"
    echo "Build Date: ${BUILD_DATE}"
}

# コマンドライン引数の処理
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--version)
                show_version
                exit 0
                ;;
            -n|--name)
                PROJECT_NAME="$2"
                shift 2
                ;;
            -s|--skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            -f|--force-rebuild)
                FORCE_REBUILD=true
                shift
                ;;
            --config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            --data-dir)
                DATA_DIR="$2"
                shift 2
                ;;
            local|docker|production|test)
                DEPLOYMENT_TYPE="$1"
                shift
                ;;
            *)
                log_error "不明なオプション: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 前提条件チェック
check_prerequisites() {
    log_step "前提条件をチェック中..."
    
    # 必須コマンドの確認
    local required_commands=("python3" "pip")
    
    if [[ "$DEPLOYMENT_TYPE" == "docker" ]]; then
        required_commands+=("docker")
        if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
            log_info "Docker Composeが利用可能"
        else
            log_warning "Docker Composeが見つかりません"
        fi
    fi
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "必須コマンドが見つかりません: $cmd"
            exit 1
        else
            log_info "$cmd: $(command -v "$cmd")"
        fi
    done
    
    # Python バージョンチェック
    local python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log_info "Python version: $python_version"
    
    log_success "前提条件チェック完了"
}

# ローカル環境デプロイ
deploy_local() {
    log_step "ローカル環境へのデプロイ開始..."
    
    # インストールディレクトリの設定
    export RAG_HOME="${RAG_HOME:-$HOME/.rag}"
    export RAG_CONFIG="${CONFIG_FILE:-$RAG_HOME/config.yaml}"
    export RAG_DATA="${DATA_DIR:-$RAG_HOME/data}"
    
    log_info "インストール先: $RAG_HOME"
    
    # ディレクトリ作成
    mkdir -p "$RAG_HOME" "$RAG_DATA" "$RAG_HOME/logs" "$RAG_HOME/src"
    
    # 仮想環境の作成・更新
    if [[ ! -d "$RAG_HOME/venv" ]] || [[ "$FORCE_REBUILD" == "true" ]]; then
        log_info "仮想環境を作成中..."
        rm -rf "$RAG_HOME/venv"
        python3 -m venv "$RAG_HOME/venv"
    fi
    
    # 仮想環境の有効化
    source "$RAG_HOME/venv/bin/activate"
    
    # 依存関係のインストール
    log_info "依存関係をインストール中..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # ソースコードのコピー
    log_info "ソースコードをコピー中..."
    cp -r rag/ "$RAG_HOME/src/"
    cp setup.py "$RAG_HOME/src/"
    
    # パッケージのインストール
    cd "$RAG_HOME/src"
    pip install -e .
    cd - > /dev/null
    
    # 設定ファイルの作成
    if [[ ! -f "$RAG_CONFIG" ]] || [[ "$FORCE_REBUILD" == "true" ]]; then
        log_info "設定ファイルを作成中..."
        cp config.yaml "$RAG_CONFIG"
        
        # パスを更新
        sed -i "s|path: \".*\"|path: \"$RAG_DATA/chroma\"|g" "$RAG_CONFIG"
    fi
    
    # 起動スクリプトの作成
    log_info "起動スクリプトを作成中..."
    cat > "$RAG_HOME/rag" << EOF
#!/bin/bash
RAG_HOME="$RAG_HOME"
source "\$RAG_HOME/venv/bin/activate"
export PYTHONPATH="\$RAG_HOME/src:\$PYTHONPATH"
export RAG_CONFIG_PATH="$RAG_CONFIG"
python3 -m rag.cli.main "\$@"
EOF
    chmod +x "$RAG_HOME/rag"
    
    # PATHの追加
    if ! grep -q "$RAG_HOME" "$HOME/.bashrc" 2>/dev/null; then
        echo "export PATH=\"$RAG_HOME:\$PATH\"" >> "$HOME/.bashrc"
        log_info "PATH を ~/.bashrc に追加"
    fi
    
    log_success "ローカル環境へのデプロイ完了"
    log_info "使用方法:"
    log_info "  source ~/.bashrc"
    log_info "  rag --help"
}

# Docker環境デプロイ
deploy_docker() {
    log_step "Docker環境でのデプロイ開始..."
    
    # Dockerイメージのビルド
    if [[ "$FORCE_REBUILD" == "true" ]]; then
        log_info "Dockerイメージを強制リビルド中..."
        docker build --no-cache -t "$PROJECT_NAME:latest" .
    else
        log_info "Dockerイメージをビルド中..."
        docker build -t "$PROJECT_NAME:latest" .
    fi
    
    # Docker Composeでの起動
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    else
        log_warning "Docker Composeが利用できません。直接Dockerで起動します"
        
        # 直接Docker実行
        log_info "Dockerコンテナを起動中..."
        docker run -d \
            --name "$PROJECT_NAME" \
            --restart unless-stopped \
            -v rag-data:/app/data \
            -v rag-logs:/app/logs \
            -v "$(pwd)/config.yaml:/app/config/config.yaml:ro" \
            -p 8000:8000 \
            "$PROJECT_NAME:latest" \
            mcp-server
        
        log_success "Dockerコンテナが起動しました"
        log_info "ログ確認: docker logs $PROJECT_NAME"
        log_info "停止: docker stop $PROJECT_NAME"
        return
    fi
    
    # Docker Composeでの起動
    log_info "Docker Composeでサービスを起動中..."
    $COMPOSE_CMD up -d
    
    log_success "Docker環境でのデプロイ完了"
    log_info "状態確認: $COMPOSE_CMD ps"
    log_info "ログ確認: $COMPOSE_CMD logs -f"
    log_info "停止: $COMPOSE_CMD down"
}

# プロダクション環境デプロイ
deploy_production() {
    log_step "プロダクション環境へのデプロイ開始..."
    
    # 環境チェック
    if [[ -z "${PRODUCTION_SERVER}" ]]; then
        log_error "PRODUCTION_SERVER環境変数が設定されていません"
        exit 1
    fi
    
    log_info "プロダクションサーバー: $PRODUCTION_SERVER"
    
    # デプロイ前テスト
    if [[ "$SKIP_TESTS" == "false" ]]; then
        log_info "デプロイ前テストを実行中..."
        python3 -m pytest tests/ -v --tb=short || {
            log_error "テストが失敗しました"
            exit 1
        }
    fi
    
    # プロダクション設定の準備
    log_info "プロダクション設定を準備中..."
    
    # 設定ファイルの調整
    cp config.yaml config_production.yaml
    
    # プロダクション用の調整
    sed -i 's|device: "cpu"|device: "cuda"|g' config_production.yaml  # GPU使用
    sed -i 's|batch_size: 32|batch_size: 64|g' config_production.yaml
    sed -i 's|level: "INFO"|level: "WARNING"|g' config_production.yaml
    
    log_info "プロダクション環境へのデプロイ準備完了"
    log_warning "実際のデプロイは手動で実行してください:"
    log_info "  scp -r . $PRODUCTION_SERVER:/opt/rag-second-brain/"
    log_info "  ssh $PRODUCTION_SERVER 'cd /opt/rag-second-brain && ./deploy.sh local'"
}

# テスト環境デプロイ
deploy_test() {
    log_step "テスト環境でのデプロイ開始..."
    
    # テスト用の一時ディレクトリ
    TEST_DIR="/tmp/rag-test-$$"
    mkdir -p "$TEST_DIR"
    
    log_info "テスト環境: $TEST_DIR"
    
    # テスト環境のセットアップ
    export RAG_HOME="$TEST_DIR"
    export RAG_CONFIG="$TEST_DIR/config.yaml"
    export RAG_DATA="$TEST_DIR/data"
    
    # ローカルデプロイの実行（テスト環境）
    deploy_local
    
    # 基本テストの実行
    if [[ "$SKIP_TESTS" == "false" ]]; then
        log_info "統合テストを実行中..."
        
        source "$RAG_HOME/venv/bin/activate"
        export PYTHONPATH="$RAG_HOME/src:$PYTHONPATH"
        export RAG_CONFIG_PATH="$RAG_CONFIG"
        
        # 基本動作テスト
        python3 -c "
import sys
sys.path.insert(0, '$RAG_HOME/src')
from rag.core.database import DatabaseManager
from rag.core.vectorizer import Vectorizer
from rag.core.search import SearchEngine
print('✓ All imports successful')
"
        
        # CLIテスト
        "$RAG_HOME/rag" --help > /dev/null
        "$RAG_HOME/rag" stats > /dev/null
        
        log_success "統合テスト完了"
    fi
    
    log_success "テスト環境でのデプロイ完了"
    log_info "テスト環境: $TEST_DIR"
    log_info "クリーンアップ: rm -rf $TEST_DIR"
}

# メイン処理
main() {
    echo "🧠 「第2の脳」RAGシステム デプロイ開始"
    echo "================================================"
    echo "Version: $VERSION"
    echo "Deployment Type: $DEPLOYMENT_TYPE"
    echo "Project Name: $PROJECT_NAME"
    echo "Build Date: $BUILD_DATE"
    echo "================================================"
    
    parse_args "$@"
    check_prerequisites
    
    case "$DEPLOYMENT_TYPE" in
        "local")
            deploy_local
            ;;
        "docker")
            deploy_docker
            ;;
        "production")
            deploy_production
            ;;
        "test")
            deploy_test
            ;;
        *)
            log_error "不明なデプロイタイプ: $DEPLOYMENT_TYPE"
            show_help
            exit 1
            ;;
    esac
    
    echo ""
    echo "🎉 デプロイ完了！"
    echo "================================================"
    echo "Type: $DEPLOYMENT_TYPE"
    echo "Project: $PROJECT_NAME"
    echo "Version: $VERSION"
    echo "================================================"
}

# エラーハンドリング
trap 'log_error "デプロイが中断されました"; exit 1' ERR

# スクリプト実行時のみmainを呼び出し
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi