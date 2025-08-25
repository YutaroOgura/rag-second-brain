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
    
    # pip チェック（Python 3.12対応）
    if python3 -m pip --version &> /dev/null; then
        log_info "pip version: $(python3 -m pip --version)"
    else
        log_warning "pip が見つかりません。インストールします..."
        # pipのインストール試行
        if command -v apt-get &> /dev/null; then
            log_info "apt-getでpython3-pipをインストール中..."
            sudo apt-get update && sudo apt-get install -y python3-pip python3-venv
        elif command -v brew &> /dev/null; then
            log_info "brewでpipをインストール中..."
            python3 -m ensurepip
        else
            log_info "get-pip.pyでpipをインストール中..."
            curl https://bootstrap.pypa.io/get-pip.py | python3
        fi
        
        # 再チェック
        if ! python3 -m pip --version &> /dev/null; then
            log_error "pipのインストールに失敗しました"
            log_error "手動でインストールしてください："
            log_error "  Ubuntu/Debian: sudo apt-get install python3-pip python3-venv"
            log_error "  macOS: python3 -m ensurepip"
            log_error "  その他: curl https://bootstrap.pypa.io/get-pip.py | python3"
            exit 1
        fi
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
    python3 -m pip install --upgrade pip
    
    # 必須パッケージのインストール
    log_info "必須パッケージをインストール中..."
    log_warning "⏱️  インストールには5-15分程度かかる場合があります（回線速度により異なります）"
    
    # ChromaDB（軽量・高速）
    log_info "[1/8] ChromaDB（ベクトルデータベース）をインストール中..."
    pip install --progress-bar on chromadb>=0.4.22
    log_success "✓ ChromaDBインストール完了"
    
    # sentence-transformers（最も時間がかかる）
    log_info "[2/8] sentence-transformers（埋め込みモデル）をインストール中..."
    log_warning "⚠️  このパッケージは大きいため5-10分かかる場合があります"
    pip install --progress-bar on sentence-transformers>=2.2.2
    log_success "✓ sentence-transformersインストール完了"
    
    # CLI関連（軽量）
    log_info "[3/8] Click（CLIフレームワーク）をインストール中..."
    pip install --progress-bar on click>=8.1.7
    log_success "✓ Clickインストール完了"
    
    log_info "[4/8] Rich（ターミナルUI）をインストール中..."
    pip install --progress-bar on rich>=13.7.0
    log_success "✓ Richインストール完了"
    
    # その他の依存関係
    log_info "[5/8] PyYAML（設定ファイル）をインストール中..."
    pip install --progress-bar on pyyaml>=6.0.1
    log_success "✓ PyYAMLインストール完了"
    
    log_info "[6/8] NumPy（数値計算）をインストール中..."
    pip install --progress-bar on numpy>=1.24.0
    log_success "✓ NumPyインストール完了"
    
    log_info "[7/8] python-dotenv（環境変数）をインストール中..."
    pip install --progress-bar on python-dotenv>=1.0.0
    log_success "✓ python-dotenvインストール完了"
    
    log_info "[8/8] Pydantic（データ検証）をインストール中..."
    pip install --progress-bar on pydantic>=2.5.0
    log_success "✓ Pydanticインストール完了"
    
    # オプショナルパッケージ
    log_info "オプショナルパッケージ（テストツール）をインストール中..."
    pip install --progress-bar on pytest>=7.4.3 pytest-asyncio>=0.21.1 pytest-cov>=4.1.0
    log_success "✓ テストツールインストール完了"
    
    log_success "依存関係のインストール完了"
}

# RAGシステムのセットアップ
setup_rag_system() {
    log_info "RAGシステムをセットアップ中..."
    
    # ソースコードの配置
    if [ ! -d "$RAG_HOME/src" ]; then
        # ローカルファイルが存在する場合はコピー、なければGitHubからクローン
        if [ -d "./rag" ] && [ -f "./mcp-server.js" ]; then
            log_info "ローカルファイルからソースコードをコピー中..."
            mkdir -p "$RAG_HOME/src"
            cp -r ./* "$RAG_HOME/src/" 2>/dev/null || true
        else
            log_info "ソースコードをGitHubからクローン中..."
            git clone https://github.com/YutaroOgura/rag-second-brain.git "$RAG_HOME/src"
        fi
        
        # 仮想環境でインストール
        log_info "RAGモジュールをインストール中..."
        cd "$RAG_HOME/src"
        source "$RAG_HOME/venv/bin/activate"
        
        # setup.pyを作成（README不要版）
        cat > setup.py << 'EOSETUP'
from setuptools import setup, find_packages

setup(
    name="rag-second-brain",
    version="1.0.0",
    packages=find_packages(),
    description="RAG Second Brain - Document Management System",
    install_requires=[
        "chromadb>=0.4.22",
        "sentence-transformers>=2.2.2",
        "click>=8.1.7",
        "rich>=13.7.0",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "rag=rag.cli.main:cli",
        ],
    },
    python_requires=">=3.8",
)
EOSETUP
        
        # モジュールをインストール
        pip install -e .
        log_success "✓ RAGモジュールインストール完了"
    else
        log_info "ソースコードは既に存在します: $RAG_HOME/src"
    fi
    
    # RAGパッケージのコピー（重要：新規追加）
    log_info "RAGパッケージをコピー中..."
    
    # ragディレクトリが存在する場合はコピー
    if [ -d "./rag" ]; then
        cp -r ./rag "$RAG_HOME/src/"
        log_success "✓ RAGパッケージコピー完了"
    else
        log_warning "⚠️ ragディレクトリが見つかりません。基本構造のみ作成します。"
        # 最小限のディレクトリ構造を作成
        mkdir -p "$RAG_HOME/src/rag/core"
        mkdir -p "$RAG_HOME/src/rag/cli"
        echo '"""RAG Second Brain System"""' > "$RAG_HOME/src/rag/__init__.py"
        echo '__version__ = "1.0.0"' >> "$RAG_HOME/src/rag/__init__.py"
    fi
    
    # Pythonモジュールのコピー
    log_info "Pythonモジュールをコピー中..."
    if [ -d "./src" ]; then
        cp -f ./src/*.py "$RAG_HOME/src/" 2>/dev/null || true
        log_success "✓ Pythonモジュールコピー完了"
    fi
    
    # MCPサーバーのコピー
    if [ -f "./mcp-server.js" ]; then
        cp -f ./mcp-server.js "$RAG_HOME/"
        log_success "✓ MCPサーバーコピー完了"
    fi
    
    # その他の重要ファイルのコピー
    if [ -f "./mcp-tools-implementation.js" ]; then
        cp -f ./mcp-tools-implementation.js "$RAG_HOME/" 2>/dev/null || true
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
  model: "intfloat/multilingual-e5-base"  # 日本語含む多言語対応
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
    
    # Node.jsのチェック
    if ! command -v node &> /dev/null; then
        log_warning "Node.jsが見つかりません。MCPサーバーにはNode.js 18以上が必要です"
        log_info "インストール方法:"
        log_info "  Ubuntu/Debian: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs"
        log_info "  macOS: brew install node"
    else
        log_info "Node.js version: $(node --version)"
        
        # Node.js版MCPサーバーのセットアップ
        log_info "Node.js版MCPサーバーをインストール中..."
        
        # MCPサーバーファイルをコピー
        if [ -f "$RAG_HOME/src/mcp-server.js" ]; then
            cp "$RAG_HOME/src/mcp-server.js" "$RAG_HOME/mcp-server.js"
            cp "$RAG_HOME/src/package.json" "$RAG_HOME/package.json"
        fi
        
        # npmパッケージをインストール
        if [ -f "$RAG_HOME/package.json" ]; then
            cd "$RAG_HOME"
            log_info "MCP SDKをインストール中..."
            npm install --silent 2>/dev/null || npm install
            log_success "✓ MCP SDKインストール完了"
            cd - > /dev/null
        fi
    fi
    
    # MCP設定ファイルの作成
    MCP_CONFIG="$HOME/.claude_code_mcp.json"
    if [ ! -f "$MCP_CONFIG" ]; then
        log_info "MCP設定ファイルを作成中..."
        cat > "$MCP_CONFIG" << EOF
{
  "mcpServers": {
    "rag-second-brain": {
      "command": "node",
      "args": ["$RAG_HOME/mcp-server.js"],
      "env": {
        "RAG_HOME": "$RAG_HOME"
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