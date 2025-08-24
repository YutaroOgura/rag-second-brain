#!/bin/bash

# MeCab環境セットアップスクリプト
# Phase 2用の準備

set -e  # エラーが発生したら即座に停止

echo "========================================="
echo "MeCab環境セットアップスクリプト"
echo "========================================="

# OSの確認
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    echo "サポートされていないOS: $OSTYPE"
    exit 1
fi

echo "検出されたOS: $OS"

# Linuxの場合
if [ "$OS" == "linux" ]; then
    echo ""
    echo "1. システムパッケージの更新..."
    sudo apt-get update
    
    echo ""
    echo "2. MeCabと辞書のインストール..."
    sudo apt-get install -y mecab mecab-ipadic-utf8 libmecab-dev
    
    echo ""
    echo "3. MeCab設定ファイルの確認..."
    mecab-config --version
fi

# macOSの場合
if [ "$OS" == "macos" ]; then
    echo ""
    echo "1. Homebrewの確認..."
    if ! command -v brew &> /dev/null; then
        echo "Homebrewがインストールされていません。"
        echo "https://brew.sh からインストールしてください。"
        exit 1
    fi
    
    echo ""
    echo "2. MeCabと辞書のインストール..."
    brew install mecab mecab-ipadic
fi

echo ""
echo "4. Pythonライブラリのインストール..."
pip install mecab-python3 unidic-lite fugashi ipadic

echo ""
echo "5. カスタム辞書ディレクトリの作成..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DICT_DIR="$PROJECT_ROOT/data/mecab_dict"

mkdir -p "$DICT_DIR"

echo ""
echo "6. カスタム辞書CSVファイルの作成..."
cat > "$DICT_DIR/ultra_terms.csv" << 'EOF'
Slack通知,1285,1285,1000,名詞,固有名詞,組織,*,*,*,スラックツウチ,スラックツウチ,スラック通知
環境変数,1285,1285,1000,名詞,一般,*,*,*,*,カンキョウヘンスウ,カンキョウヘンスー,環境変数
PayBlend,1285,1285,500,名詞,固有名詞,組織,*,*,*,ペイブレンド,ペイブレンド,PayBlend
UltraPay,1285,1285,500,名詞,固有名詞,組織,*,*,*,ウルトラペイ,ウルトラペイ,UltraPay
バッチ処理,1285,1285,1000,名詞,一般,*,*,*,*,バッチショリ,バッチショリ,バッチ処理
API認証,1285,1285,1000,名詞,一般,*,*,*,*,エーピーアイニンショウ,エーピーアイニンショウ,API認証
Docker環境,1285,1285,1000,名詞,一般,*,*,*,*,ドッカーカンキョウ,ドッカーカンキョウ,Docker環境
JWT認証,1285,1285,1000,名詞,一般,*,*,*,*,ジェイダブリューティーニンショウ,ジェイダブリューティーニンショウ,JWT認証
Redis接続,1285,1285,1000,名詞,一般,*,*,*,*,レディスセツゾク,レディスセツゾク,Redis接続
Laravel設定,1285,1285,1000,名詞,一般,*,*,*,*,ララベルセッテイ,ララベルセッテイ,Laravel設定
プリペイドカード,1285,1285,800,名詞,一般,*,*,*,*,プリペイドカード,プリペイドカード,プリペイドカード
GMO決済,1285,1285,800,名詞,固有名詞,組織,*,*,*,ジーエムオーケッサイ,ジーエムオーケッサイ,GMO決済
セブン銀行,1285,1285,800,名詞,固有名詞,組織,*,*,*,セブンギンコウ,セブンギンコウ,セブン銀行
TIS連携,1285,1285,1000,名詞,一般,*,*,*,*,ティーアイエスレンケイ,ティーアイエスレンケイ,TIS連携
Webhook設定,1285,1285,1000,名詞,一般,*,*,*,*,ウェブフックセッテイ,ウェブフックセッテイ,Webhook設定
EOF

echo ""
echo "7. カスタム辞書のコンパイル..."
if [ "$OS" == "linux" ]; then
    # システム辞書のパスを取得
    SYSDIC=$(mecab-config --dicdir)/ipadic
    
    if [ -d "$SYSDIC" ]; then
        echo "システム辞書: $SYSDIC"
        
        # カスタム辞書をコンパイル
        /usr/lib/mecab/mecab-dict-index \
            -d "$SYSDIC" \
            -u "$DICT_DIR/ultra_custom.dic" \
            -f utf-8 -t utf-8 \
            "$DICT_DIR/ultra_terms.csv"
        
        echo "カスタム辞書作成完了: $DICT_DIR/ultra_custom.dic"
    else
        echo "警告: システム辞書が見つかりません。カスタム辞書のコンパイルをスキップします。"
    fi
elif [ "$OS" == "macos" ]; then
    # macOSでのパス
    SYSDIC="/usr/local/lib/mecab/dic/ipadic"
    
    if [ -d "$SYSDIC" ]; then
        echo "システム辞書: $SYSDIC"
        
        # カスタム辞書をコンパイル
        /usr/local/libexec/mecab/mecab-dict-index \
            -d "$SYSDIC" \
            -u "$DICT_DIR/ultra_custom.dic" \
            -f utf-8 -t utf-8 \
            "$DICT_DIR/ultra_terms.csv"
        
        echo "カスタム辞書作成完了: $DICT_DIR/ultra_custom.dic"
    else
        echo "警告: システム辞書が見つかりません。カスタム辞書のコンパイルをスキップします。"
    fi
fi

echo ""
echo "8. MeCabの動作確認..."
echo "Slack通知を設定する" | mecab

echo ""
echo "9. Pythonバインディングの確認..."
python3 -c "
import MeCab
tagger = MeCab.Tagger()
print('MeCab Python バインディング: OK')
text = 'Slack通知とDocker環境'
print(f'テスト解析: {text}')
print(tagger.parse(text))
"

echo ""
echo "========================================="
echo "MeCab環境のセットアップが完了しました！"
echo "========================================="
echo ""
echo "カスタム辞書の場所: $DICT_DIR/ultra_custom.dic"
echo ""
echo "使用方法:"
echo "  Python:"
echo "    import MeCab"
echo "    tagger = MeCab.Tagger(f'-u {DICT_DIR}/ultra_custom.dic')"
echo ""