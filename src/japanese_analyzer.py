#!/usr/bin/env python3
"""
日本語形態素解析器 - Phase 2実装
MeCab代替として軽量な日本語解析機能を提供
"""

import re
from typing import List, Dict, Tuple, Optional
import json
from pathlib import Path

class JapaneseAnalyzer:
    """
    日本語テキストの形態素解析・分析を行うクラス
    MeCabの代替として基本的な日本語処理機能を提供
    """
    
    def __init__(self, custom_dict_path: Optional[str] = None):
        """
        日本語解析器の初期化
        
        Args:
            custom_dict_path: カスタム辞書ファイルのパス
        """
        self.hiragana_pattern = re.compile(r'[ひ-ゞ]+')
        self.katakana_pattern = re.compile(r'[ァ-ヾ]+')
        self.kanji_pattern = re.compile(r'[一-龯]+')
        self.ascii_pattern = re.compile(r'[a-zA-Z0-9]+')
        
        # 基本的な助詞・助動詞・接続詞
        self.particles = {
            'は', 'が', 'を', 'に', 'で', 'と', 'の', 'や', 'か', 'も', 'から', 'まで',
            'より', 'へ', 'ば', 'て', 'で', 'た', 'だ', 'である', 'です', 'ます',
            'した', 'します', 'される', 'する', 'できる', 'なる', 'いる', 'ある'
        }
        
        # Ultra Pay関連の専門用語辞書
        self.technical_terms = {
            # プリペイドカード関連
            'プリペイドカード', 'プリペイド', 'UltraPay', 'PayBlend', 'VISA',
            'セブン銀行', 'ATM', 'QRコード', 'チャージ', '残高', '決済',
            
            # 技術用語
            'API', 'JWT', 'OAuth', 'SSL', 'TLS', 'JSON', 'XML', 'HTTP', 'HTTPS',
            'データベース', 'インデックス', 'トークン', 'ログイン', '認証', 'セッション',
            
            # 開発用語
            'Laravel', 'Vue.js', 'Docker', 'Kubernetes', 'AWS', 'S3', 'Lambda',
            'フロントエンド', 'バックエンド', 'マイクロサービス', 'CI/CD',
            
            # 業務用語
            'ユーザー', 'アカウント', 'パスワード', 'セキュリティ', 'トランザクション',
            'エラー', 'ログ', 'メンテナンス', 'バックアップ', 'リストア'
        }
        
        # カスタム辞書の読み込み
        if custom_dict_path and Path(custom_dict_path).exists():
            self.load_custom_dictionary(custom_dict_path)
    
    def load_custom_dictionary(self, dict_path: str):
        """
        カスタム辞書を読み込む
        
        Args:
            dict_path: 辞書ファイルのパス
        """
        try:
            with open(dict_path, 'r', encoding='utf-8') as f:
                custom_dict = json.load(f)
                
            # compound_termsから専門用語を追加
            if 'compound_terms' in custom_dict:
                for term, data in custom_dict['compound_terms'].items():
                    self.technical_terms.add(term)
                    # 同義語も追加
                    if 'synonyms' in data:
                        for synonym in data['synonyms']:
                            if self._is_japanese(synonym):
                                self.technical_terms.add(synonym)
                                
        except Exception as e:
            print(f"カスタム辞書の読み込みに失敗: {e}")
    
    def analyze(self, text: str) -> List[Dict[str, str]]:
        """
        テキストを形態素解析する
        
        Args:
            text: 解析対象テキスト
            
        Returns:
            形態素情報のリスト
        """
        morphemes = []
        tokens = self.tokenize(text)
        
        for token in tokens:
            if not token.strip():
                continue
                
            morpheme = {
                'surface': token,
                'pos': self._get_part_of_speech(token),
                'base_form': self._get_base_form(token),
                'reading': self._get_reading(token)
            }
            morphemes.append(morpheme)
            
        return morphemes
    
    def tokenize(self, text: str) -> List[str]:
        """
        テキストをトークンに分割する
        
        Args:
            text: 分割対象テキスト
            
        Returns:
            トークンのリスト
        """
        tokens = []
        i = 0
        
        while i < len(text):
            # 専門用語の最長一致
            longest_match = self._find_longest_technical_term(text, i)
            if longest_match:
                tokens.append(longest_match)
                i += len(longest_match)
                continue
            
            # 英数字の処理
            if text[i].isascii() and text[i].isalnum():
                match = self.ascii_pattern.match(text, i)
                if match:
                    tokens.append(match.group())
                    i = match.end()
                    continue
            
            # 漢字の処理
            if self.kanji_pattern.match(text[i]):
                kanji_token = self._extract_kanji_compound(text, i)
                tokens.append(kanji_token)
                i += len(kanji_token)
                continue
            
            # カタカナの処理
            if self.katakana_pattern.match(text[i]):
                katakana_match = self.katakana_pattern.match(text, i)
                if katakana_match:
                    tokens.append(katakana_match.group())
                    i = katakana_match.end()
                    continue
            
            # ひらがなの処理
            if self.hiragana_pattern.match(text[i]):
                hiragana_token = self._extract_hiragana_token(text, i)
                tokens.append(hiragana_token)
                i += len(hiragana_token)
                continue
            
            # その他の文字（記号等）
            if text[i] not in ' \t\n\r':
                tokens.append(text[i])
            i += 1
        
        return tokens
    
    def extract_compound_words(self, text: str) -> List[str]:
        """
        複合語を抽出する
        
        Args:
            text: 抽出対象テキスト
            
        Returns:
            複合語のリスト
        """
        compounds = []
        tokens = self.tokenize(text)
        
        # 連続する名詞・形容詞を複合語として抽出
        i = 0
        while i < len(tokens):
            if self._is_noun_like(tokens[i]):
                compound = [tokens[i]]
                j = i + 1
                
                while j < len(tokens) and self._is_noun_like(tokens[j]):
                    compound.append(tokens[j])
                    j += 1
                
                if len(compound) >= 2:
                    compounds.append(''.join(compound))
                i = j
            else:
                i += 1
        
        return compounds
    
    def _find_longest_technical_term(self, text: str, start: int) -> Optional[str]:
        """
        指定位置から始まる最長の専門用語を検索
        
        Args:
            text: 検索対象テキスト
            start: 検索開始位置
            
        Returns:
            見つかった専門用語（なければNone）
        """
        longest_match = None
        max_length = 0
        
        for term in self.technical_terms:
            if text[start:start + len(term)] == term:
                if len(term) > max_length:
                    longest_match = term
                    max_length = len(term)
        
        return longest_match
    
    def _extract_kanji_compound(self, text: str, start: int) -> str:
        """
        漢字複合語を抽出
        
        Args:
            text: 対象テキスト
            start: 開始位置
            
        Returns:
            抽出された漢字複合語
        """
        end = start
        while end < len(text) and self.kanji_pattern.match(text[end]):
            end += 1
        
        return text[start:end] if end > start else text[start]
    
    def _extract_hiragana_token(self, text: str, start: int) -> str:
        """
        ひらがなトークンを抽出
        
        Args:
            text: 対象テキスト  
            start: 開始位置
            
        Returns:
            抽出されたひらがなトークン
        """
        end = start
        
        # 助詞・助動詞の判定
        for particle in sorted(self.particles, key=len, reverse=True):
            if text[start:start + len(particle)] == particle:
                return particle
        
        # 一般的なひらがな連続
        while end < len(text) and self.hiragana_pattern.match(text[end]):
            end += 1
            
        return text[start:end] if end > start else text[start]
    
    def _get_part_of_speech(self, token: str) -> str:
        """
        品詞を推定
        
        Args:
            token: トークン
            
        Returns:
            品詞名
        """
        if token in self.particles:
            return '助詞'
        elif token in self.technical_terms:
            return '名詞-固有名詞'
        elif self.kanji_pattern.fullmatch(token):
            return '名詞'
        elif self.katakana_pattern.fullmatch(token):
            return '名詞-外来語'
        elif self.ascii_pattern.fullmatch(token):
            return '名詞-英語'
        elif self.hiragana_pattern.fullmatch(token):
            return '動詞' if len(token) > 1 else '助詞'
        else:
            return '記号'
    
    def _get_base_form(self, token: str) -> str:
        """
        基本形を取得（簡易版）
        
        Args:
            token: トークン
            
        Returns:
            基本形
        """
        # 簡易的な活用処理
        if token.endswith('します'):
            return token[:-3] + 'する'
        elif token.endswith('した'):
            return token[:-2] + 'する'
        elif token.endswith('である'):
            return 'だ'
        else:
            return token
    
    def _get_reading(self, token: str) -> str:
        """
        読みを取得（簡易版）
        
        Args:
            token: トークン
            
        Returns:
            読み
        """
        # カタカナはそのまま、その他は省略
        if self.katakana_pattern.fullmatch(token):
            return token
        else:
            return ''
    
    def _is_japanese(self, text: str) -> bool:
        """
        日本語文字列かどうか判定
        
        Args:
            text: 判定対象テキスト
            
        Returns:
            日本語文字列の場合True
        """
        return bool(
            self.hiragana_pattern.search(text) or
            self.katakana_pattern.search(text) or
            self.kanji_pattern.search(text)
        )
    
    def _is_noun_like(self, token: str) -> bool:
        """
        名詞的なトークンかどうか判定
        
        Args:
            token: トークン
            
        Returns:
            名詞的な場合True
        """
        pos = self._get_part_of_speech(token)
        return pos.startswith('名詞') and token not in self.particles


if __name__ == '__main__':
    # 使用例
    analyzer = JapaneseAnalyzer()
    
    test_texts = [
        "Slack通知の設定を確認してください",
        "プリペイドカードのチャージ機能",
        "Docker環境でのAPI認証システム",
        "データベースのインデックス設定"
    ]
    
    for text in test_texts:
        print(f"\n📝 テキスト: {text}")
        
        # トークン化
        tokens = analyzer.tokenize(text)
        print(f"🔤 トークン: {tokens}")
        
        # 形態素解析
        morphemes = analyzer.analyze(text)
        print("🔍 形態素解析:")
        for m in morphemes:
            print(f"  {m['surface']} ({m['pos']})")
        
        # 複合語抽出
        compounds = analyzer.extract_compound_words(text)
        if compounds:
            print(f"🔗 複合語: {compounds}")