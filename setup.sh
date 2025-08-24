#!/bin/bash

# 「第2の脳」RAGシステム セットアップスクリプト
# Usage: curl -sSL https://raw.githubusercontent.com/your-repo/setup.sh | bash

set -e

echo "🧠 第2の脳 RAGシステム セットアップ開始..."

# 色付き出力用の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
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

# システム要件チェック
check_requirements() {
    log_info "システム要件をチェック中..."
    
    # Python 3.8+ チェック
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 が見つかりません"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log_info "Python version: $PYTHON_VERSION"
    
    # pip チェック
    if ! python3 -m pip --version &> /dev/null; then
        log_error "pip が見つかりません"
        exit 1
    fi
    
    # Git チェック（オプショナル）
    if command -v git &> /dev/null; then
        log_info "Git version: $(git --version)"
    else
        log_warning "Git が見つかりません（オプショナル）"
    fi
    
    log_success "システム要件チェック完了"
}

# インストールディレクトリの設定
setup_directories() {
    log_info "インストールディレクトリを設定中..."
    
    export RAG_HOME="${RAG_HOME:-$HOME/.rag}"
    export RAG_CONFIG="$RAG_HOME/config.yaml"
    export RAG_DATA="$RAG_HOME/data"
    
    mkdir -p "$RAG_HOME"
    mkdir -p "$RAG_DATA"
    mkdir -p "$RAG_HOME/logs"
    
    log_success "ディレクトリ設定完了: $RAG_HOME"
}

# 依存関係のインストール
install_dependencies() {
    log_info "依存関係をインストール中..."
    
    # 仮想環境の作成
    if [ ! -d "$RAG_HOME/venv" ]; then
        log_info "仮想環境を作成中..."
        python3 -m venv "$RAG_HOME/venv"
    fi
    
    # 仮想環境の有効化
    source "$RAG_HOME/venv/bin/activate"
    
    # pipのアップグレード
    pip install --upgrade pip
    
    # 必須パッケージのインストール
    log_info "必須パッケージをインストール中..."
    pip install chromadb>=0.4.22
    pip install sentence-transformers>=2.2.2
    pip install click>=8.1.7
    pip install rich>=13.7.0
    pip install pyyaml>=6.0.1
    pip install numpy>=1.24.0
    pip install python-dotenv>=1.0.0
    pip install pydantic>=2.5.0
    
    # オプショナルパッケージ
    log_info "オプショナルパッケージをインストール中..."
    pip install pytest>=7.4.3
    pip install pytest-asyncio>=0.21.1
    pip install pytest-cov>=4.1.0
    
    log_success "依存関係のインストール完了"
}

# RAGシステムのセットアップ
setup_rag_system() {
    log_info "RAGシステムをセットアップ中..."
    
    # ソースコードの配置（実際のプロジェクトでは git clone など）
    if [ ! -d "$RAG_HOME/src" ]; then
        mkdir -p "$RAG_HOME/src"
        # TODO: 実際のデプロイ時はここで git clone
        log_warning "ソースコードを $RAG_HOME/src に配置してください"
    fi
    
    # 設定ファイルの作成
    if [ ! -f "$RAG_CONFIG" ]; then
        log_info "デフォルト設定ファイルを作成中..."
        cat > "$RAG_CONFIG" << EOF
# RAG Second Brain Configuration
database:
  type: chromadb
  path: "$RAG_DATA/chroma"
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
  file: "$RAG_HOME/logs/rag.log"
EOF
        log_success "設定ファイルを作成: $RAG_CONFIG"
    fi
    
    # 起動スクリプトの作成
    cat > "$RAG_HOME/rag" << 'EOF'
#!/bin/bash
# RAG Second Brain 起動スクリプト

RAG_HOME="${RAG_HOME:-$HOME/.rag}"
source "$RAG_HOME/venv/bin/activate"

export PYTHONPATH="$RAG_HOME/src:$PYTHONPATH"
export RAG_CONFIG_PATH="$RAG_HOME/config.yaml"

python3 -m rag.cli.main "$@"
EOF
    
    chmod +x "$RAG_HOME/rag"
    
    # パスの追加
    if ! grep -q "$RAG_HOME" "$HOME/.bashrc" 2>/dev/null; then
        echo "export PATH=\"$RAG_HOME:\$PATH\"" >> "$HOME/.bashrc"
        log_info "PATHを ~/.bashrc に追加しました"
    fi
    
    log_success "RAGシステムのセットアップ完了"
}

# MCPサーバーのセットアップ
setup_mcp_server() {
    log_info "MCPサーバーをセットアップ中..."
    
    # MCP設定ファイルの作成
    MCP_CONFIG="$HOME/.claude_code_mcp.json"
    if [ ! -f "$MCP_CONFIG" ]; then
        log_info "MCP設定ファイルを作成中..."
        cat > "$MCP_CONFIG" << EOF
{
  "mcpServers": {
    "rag-second-brain": {
      "command": "python3",
      "args": ["-m", "rag.mcp.server"],
      "cwd": "$RAG_HOME/src",
      "env": {
        "RAG_CONFIG_PATH": "$RAG_CONFIG",
        "PYTHONPATH": "$RAG_HOME/src"
      }
    }
  }
}
EOF
        log_success "MCP設定ファイルを作成: $MCP_CONFIG"
    fi
    
    log_success "MCPサーバーのセットアップ完了"
}

# 初期データの準備
prepare_sample_data() {
    log_info "サンプルデータを準備中..."
    
    SAMPLE_DIR="$RAG_HOME/samples"
    mkdir -p "$SAMPLE_DIR"
    
    # サンプルドキュメントの作成
    cat > "$SAMPLE_DIR/sample_auth.md" << 'EOF'
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
    
    cat > "$SAMPLE_DIR/sample_database.md" << 'EOF'
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
    
    log_success "サンプルデータの準備完了"
}

# 動作テスト
run_tests() {
    log_info "動作テストを実行中..."
    
    source "$RAG_HOME/venv/bin/activate"
    export PYTHONPATH="$RAG_HOME/src:$PYTHONPATH"
    export RAG_CONFIG_PATH="$RAG_CONFIG"
    
    # 基本的なimportテスト
    python3 -c "import sys; sys.path.insert(0, '$RAG_HOME/src'); from rag.core.database import DatabaseManager; print('✓ DatabaseManager import OK')" || log_error "DatabaseManager import failed"
    
    # サンプルデータのインデックステスト（依存関係が揃っている場合）
    # python3 "$RAG_HOME/rag" index "$RAG_HOME/samples" --project sample --recursive || log_warning "Sample indexing failed (dependencies may be missing)"
    
    log_success "基本テスト完了"
}

# メイン処理
main() {
    echo "🚀 「第2の脳」RAGシステム インストール開始"
    echo "================================================"
    
    check_requirements
    setup_directories
    install_dependencies
    setup_rag_system
    setup_mcp_server
    prepare_sample_data
    run_tests
    
    echo ""
    echo "🎉 セットアップ完了！"
    echo "================================================"
    echo "✓ インストール先: $RAG_HOME"
    echo "✓ 設定ファイル: $RAG_CONFIG"
    echo "✓ コマンド: $RAG_HOME/rag"
    echo ""
    echo "📖 使用方法:"
    echo "  source ~/.bashrc  # パスを更新"
    echo "  rag --help        # ヘルプ表示"
    echo "  rag index ./docs --project my-project --recursive"
    echo "  rag search 'キーワード' --type hybrid"
    echo ""
    echo "🔧 ClaudeCode連携:"
    echo "  ClaudeCodeを再起動して、MCPサーバーが利用可能になります"
    echo ""
    echo "📚 詳細: $RAG_HOME/README.md"
}

# エラーハンドリング
trap 'log_error "インストールが中断されました"; exit 1' ERR

# 実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi