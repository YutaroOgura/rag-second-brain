"""
日本語複合語を認識し、検索可能な形式に変換するクエリ前処理モジュール
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class QueryPreprocessor:
    """
    日本語複合語を認識し、検索可能な形式に変換するクラス
    """
    
    def __init__(self, compound_terms_path: Optional[str] = None):
        """
        初期化
        
        Args:
            compound_terms_path: 複合語辞書ファイルのパス
        """
        self.compound_terms_path = compound_terms_path or Path(__file__).parent.parent / "data" / "compound_terms.json"
        self.compound_terms = self._load_compound_dictionary()
        self.expansion_rules = self._load_expansion_rules()
        
    def _load_compound_dictionary(self) -> Dict[str, Dict]:
        """
        複合語辞書を読み込む
        
        Returns:
            複合語辞書
        """
        if not Path(self.compound_terms_path).exists():
            logger.warning(f"複合語辞書ファイルが見つかりません: {self.compound_terms_path}")
            return {}
            
        try:
            with open(self.compound_terms_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('compound_terms', {})
        except Exception as e:
            logger.error(f"複合語辞書の読み込みエラー: {e}")
            return {}
    
    def _load_expansion_rules(self) -> Dict[str, List[str]]:
        """
        クエリ展開ルールを読み込む
        
        Returns:
            展開ルール辞書
        """
        # 基本的な展開ルール（将来的には外部ファイルから読み込み）
        return {
            "通知": ["notification", "alert", "アラート"],
            "環境変数": ["environment variable", "env var", "環境設定"],
            "バッチ処理": ["batch processing", "batch", "バッチ"],
            "認証": ["authentication", "auth", "認可", "authorization"],
            "設定": ["configuration", "config", "設定", "セットアップ", "setup"],
        }
    
    def preprocess(self, query: str) -> List[str]:
        """
        入力クエリを前処理し、検索用クエリリストを返す
        
        Args:
            query: 元の検索クエリ
        
        Returns:
            展開された検索クエリのリスト
        """
        queries = [query]  # 元のクエリは必ず含める
        
        # 1. 複合語の認識と展開
        for compound_term, info in self.compound_terms.items():
            if compound_term in query:
                # トークン分割版を追加
                if 'tokens' in info:
                    token_query = query.replace(compound_term, ' '.join(info['tokens']))
                    if token_query not in queries:
                        queries.append(token_query)
                
                # 同義語を追加
                if 'synonyms' in info:
                    for synonym in info['synonyms']:
                        synonym_query = query.replace(compound_term, synonym)
                        if synonym_query not in queries:
                            queries.append(synonym_query)
        
        # 2. 単語レベルの展開
        words = self._extract_words(query)
        for word in words:
            if word in self.expansion_rules:
                for expansion in self.expansion_rules[word]:
                    expanded_query = query.replace(word, expansion)
                    if expanded_query not in queries:
                        queries.append(expanded_query)
        
        # 3. 英語・日本語混在の処理
        queries.extend(self._handle_mixed_language(query))
        
        # 重複を削除して返す
        return list(dict.fromkeys(queries))
    
    def _extract_words(self, text: str) -> List[str]:
        """
        テキストから単語を抽出
        
        Args:
            text: 入力テキスト
        
        Returns:
            抽出された単語のリスト
        """
        # 簡易的な単語抽出（将来的にはMeCabを使用）
        # 日本語の単語境界を認識
        pattern = r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+|[a-zA-Z0-9]+'
        words = re.findall(pattern, text)
        return words
    
    def _handle_mixed_language(self, query: str) -> List[str]:
        """
        英語・日本語混在クエリの処理
        
        Args:
            query: 入力クエリ
        
        Returns:
            処理されたクエリのリスト
        """
        additional_queries = []
        
        # 英語と日本語の境界にスペースを挿入
        spaced_query = re.sub(r'([a-zA-Z]+)([\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+)', r'\1 \2', query)
        spaced_query = re.sub(r'([\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+)([a-zA-Z]+)', r'\1 \2', spaced_query)
        
        if spaced_query != query:
            additional_queries.append(spaced_query)
        
        return additional_queries
    
    def split_query(self, query: str) -> List[str]:
        """
        クエリを意味的な単位に分割（フォールバック用）
        
        Args:
            query: 入力クエリ
        
        Returns:
            分割されたクエリ部分のリスト
        """
        # 複合語として認識されているものは分割
        parts = []
        remaining = query
        
        for compound_term, info in self.compound_terms.items():
            if compound_term in remaining:
                if 'tokens' in info:
                    parts.extend(info['tokens'])
                    remaining = remaining.replace(compound_term, '')
        
        # 残りの部分も単語単位で分割
        if remaining.strip():
            parts.extend(self._extract_words(remaining))
        
        # 空要素を除去して返す
        return [p for p in parts if p.strip()]
    
    def get_query_variations(self, query: str, max_variations: int = 5) -> List[Dict[str, Any]]:
        """
        クエリのバリエーションを優先度付きで生成
        
        Args:
            query: 入力クエリ
            max_variations: 最大バリエーション数
        
        Returns:
            優先度付きクエリバリエーションのリスト
        """
        variations = []
        
        # 元のクエリ（最高優先度）
        variations.append({
            'query': query,
            'weight': 1.0,
            'type': 'original'
        })
        
        # 前処理されたクエリ
        preprocessed = self.preprocess(query)
        for i, q in enumerate(preprocessed[1:max_variations], 1):  # 元のクエリは除く
            variations.append({
                'query': q,
                'weight': 0.8 - (i * 0.1),  # 徐々に重みを減らす
                'type': 'preprocessed'
            })
        
        # 分割クエリ（最低優先度）
        if len(variations) < max_variations:
            parts = self.split_query(query)
            if parts:
                variations.append({
                    'query': ' '.join(parts),
                    'weight': 0.3,
                    'type': 'split'
                })
        
        return variations[:max_variations]