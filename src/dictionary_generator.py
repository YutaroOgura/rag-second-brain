#!/usr/bin/env python3
"""
カスタム辞書自動生成器 - Phase 2実装
既存ドキュメントから専門用語を自動抽出してカスタム辞書を構築
"""

import json
import re
from typing import Dict, List, Set, Tuple
from pathlib import Path
import sqlite3
from collections import Counter, defaultdict

class DictionaryGenerator:
    """
    RAGインデックスから専門用語を抽出してカスタム辞書を自動生成
    """
    
    def __init__(self, rag_db_path: str = None, output_path: str = None):
        """
        辞書生成器の初期化
        
        Args:
            rag_db_path: RAGデータベースのパス
            output_path: 出力辞書ファイルのパス
        """
        self.rag_db_path = rag_db_path or "/home/ogura/.rag/vector_db.sqlite"
        self.output_path = output_path or "data/auto_generated_dictionary.json"
        
        # パターン定義
        self.tech_patterns = {
            # API・プロトコル関連
            'api_terms': re.compile(r'\b(?:API|REST|GraphQL|WebSocket|HTTP|HTTPS|SSL|TLS|OAuth|JWT|CORS)\b', re.IGNORECASE),
            
            # プログラミング言語・フレームワーク
            'frameworks': re.compile(r'\b(?:Laravel|Vue\.js|React|Node\.js|Docker|Kubernetes|AWS|Python|JavaScript|PHP|Kotlin|Swift)\b', re.IGNORECASE),
            
            # データベース・ストレージ
            'database': re.compile(r'\b(?:PostgreSQL|MySQL|Redis|MongoDB|S3|RDS|DynamoDB|SQLite)\b', re.IGNORECASE),
            
            # インフラ・運用
            'infrastructure': re.compile(r'\b(?:CI/CD|DevOps|Terraform|Ansible|Jenkins|GitHub|GitLab|Bitbucket)\b', re.IGNORECASE),
            
            # セキュリティ
            'security': re.compile(r'\b(?:認証|セキュリティ|暗号化|ハッシュ|HMAC|AES|RSA|証明書|トークン)\b'),
            
            # 業務・決済関連
            'business': re.compile(r'\b(?:プリペイドカード|決済|チャージ|残高|VISA|QRコード|ATM|銀行|セブン銀行|ウルトラペイ|PayBlend)\b'),
        }
        
        # 日本語複合語パターン
        self.japanese_patterns = {
            'compound_katakana': re.compile(r'[ァ-ヾ]{2,}'),  # カタカナ複合語
            'compound_kanji': re.compile(r'[一-龯]{2,}'),    # 漢字複合語
            'mixed_compound': re.compile(r'[a-zA-Z]+[ひ-ゞァ-ヾ一-龯]+|[ひ-ゞァ-ヾ一-龯]+[a-zA-Z]+'),  # 混在複合語
        }
        
        # 除外パターン
        self.exclude_patterns = [
            re.compile(r'^[0-9]+$'),  # 純粋な数字
            re.compile(r'^[a-z]{1,2}$'),  # 短い英字
            re.compile(r'^[ひ-ゞ]{1,2}$'),  # 短いひらがな
            re.compile(r'[^\w\s\-_]'),  # 特殊記号を含む
        ]
    
    def generate_dictionary(self) -> Dict:
        """
        RAGインデックスから辞書を自動生成
        
        Returns:
            生成された辞書データ
        """
        print("🔍 RAGデータベースから専門用語を抽出中...")
        
        # RAGデータベースから文書を取得
        documents = self._fetch_documents()
        print(f"📄 {len(documents)} 件のドキュメントを処理対象とします")
        
        # 専門用語を抽出
        extracted_terms = self._extract_technical_terms(documents)
        print(f"🔤 {len(extracted_terms)} 個の候補用語を抽出しました")
        
        # 用語をフィルタリング・クリーニング
        filtered_terms = self._filter_and_rank_terms(extracted_terms)
        print(f"✅ {len(filtered_terms)} 個の用語を選定しました")
        
        # 辞書形式に変換
        dictionary = self._build_dictionary(filtered_terms)
        print(f"📚 辞書に {len(dictionary['compound_terms'])} 個の専門用語を登録しました")
        
        # 既存辞書との統合
        final_dictionary = self._merge_with_existing_dictionary(dictionary)
        
        # 辞書をファイルに保存
        self._save_dictionary(final_dictionary)
        
        return final_dictionary
    
    def _fetch_documents(self) -> List[Dict[str, str]]:
        """
        RAGデータベースからドキュメントを取得
        
        Returns:
            ドキュメントのリスト
        """
        documents = []
        
        try:
            if not Path(self.rag_db_path).exists():
                print(f"⚠️  RAGデータベースが見つかりません: {self.rag_db_path}")
                return []
            
            conn = sqlite3.connect(self.rag_db_path)
            cursor = conn.cursor()
            
            # テーブル構造を確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"📊 利用可能なテーブル: {[t[0] for t in tables]}")
            
            # ドキュメントテーブルから取得（テーブル名は環境に依存）
            possible_queries = [
                "SELECT text, metadata FROM documents LIMIT 1000",
                "SELECT content, title FROM documents LIMIT 1000", 
                "SELECT text FROM chunks LIMIT 1000",
                "SELECT content FROM content LIMIT 1000"
            ]
            
            for query in possible_queries:
                try:
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        if len(row) >= 2:
                            documents.append({
                                'text': row[0] or '',
                                'metadata': row[1] or ''
                            })
                        else:
                            documents.append({
                                'text': row[0] or '',
                                'metadata': ''
                            })
                    
                    if documents:
                        print(f"✅ クエリ成功: {query}")
                        break
                        
                except sqlite3.Error:
                    continue
            
            conn.close()
            
        except Exception as e:
            print(f"❌ データベース接続エラー: {e}")
        
        # フォールバック: プロジェクトファイルから直接読み取り
        if not documents:
            print("🔄 フォールバック: プロジェクトファイルから用語抽出")
            documents = self._load_project_files()
        
        return documents
    
    def _load_project_files(self) -> List[Dict[str, str]]:
        """
        プロジェクトファイルから直接読み取り
        
        Returns:
            ファイル内容のリスト
        """
        documents = []
        project_root = Path("/home/ogura/work/ultra")
        
        # 主要なドキュメントファイル
        doc_patterns = ["**/*.md", "**/*.txt", "**/*.json", "**/*README*"]
        
        for pattern in doc_patterns:
            try:
                for file_path in project_root.glob(pattern):
                    if file_path.is_file() and file_path.stat().st_size < 1024 * 1024:  # 1MB未満
                        try:
                            content = file_path.read_text(encoding='utf-8', errors='ignore')
                            documents.append({
                                'text': content,
                                'metadata': str(file_path)
                            })
                        except Exception:
                            continue
            except Exception:
                continue
                
        return documents[:100]  # 最大100ファイル
    
    def _extract_technical_terms(self, documents: List[Dict[str, str]]) -> Counter:
        """
        ドキュメントから技術用語を抽出
        
        Args:
            documents: ドキュメントのリスト
            
        Returns:
            用語の出現頻度
        """
        term_counter = Counter()
        
        for doc in documents:
            text = doc['text'] + ' ' + doc['metadata']
            
            # 各パターンで用語を抽出
            for category, pattern in self.tech_patterns.items():
                matches = pattern.findall(text)
                for match in matches:
                    term_counter[match.strip()] += 1
            
            # 日本語複合語の抽出
            for category, pattern in self.japanese_patterns.items():
                matches = pattern.findall(text)
                for match in matches:
                    if len(match) >= 2 and not any(exc.search(match) for exc in self.exclude_patterns):
                        term_counter[match.strip()] += 1
        
        return term_counter
    
    def _filter_and_rank_terms(self, term_counter: Counter) -> List[Tuple[str, int]]:
        """
        用語をフィルタリングしてランク付け
        
        Args:
            term_counter: 用語の出現頻度
            
        Returns:
            フィルタリング後の用語リスト
        """
        filtered_terms = []
        
        for term, count in term_counter.most_common():
            # フィルタリング条件
            if (count >= 2 and  # 最低2回は出現
                len(term) >= 2 and  # 最低2文字
                len(term) <= 20 and  # 最大20文字
                not any(exc.search(term) for exc in self.exclude_patterns)):
                
                filtered_terms.append((term, count))
        
        return filtered_terms[:500]  # 上位500語まで
    
    def _build_dictionary(self, terms: List[Tuple[str, int]]) -> Dict:
        """
        用語リストから辞書を構築
        
        Args:
            terms: フィルタリング済み用語リスト
            
        Returns:
            辞書データ
        """
        compound_terms = {}
        
        for term, frequency in terms:
            # 重み算出（頻度ベース、最大1.0）
            weight = min(1.0, frequency / 10.0)
            
            # トークン分割の推定
            tokens = self._estimate_tokens(term)
            
            # 同義語の生成
            synonyms = self._generate_synonyms(term)
            
            compound_terms[term] = {
                'tokens': tokens,
                'synonyms': synonyms,
                'weight': weight,
                'frequency': frequency,
                'category': self._categorize_term(term)
            }
        
        return {
            'compound_terms': compound_terms,
            'meta': {
                'generated_at': '2025-01-24',
                'version': '2.0.0',
                'source': 'auto_generated',
                'total_terms': len(compound_terms)
            }
        }
    
    def _estimate_tokens(self, term: str) -> List[str]:
        """
        用語のトークン分割を推定
        
        Args:
            term: 対象用語
            
        Returns:
            推定されたトークンリスト
        """
        # 簡易的なトークン分割ロジック
        tokens = []
        
        # 英語+日本語の境界で分割
        parts = re.split(r'(?<=[a-zA-Z])(?=[ひ-ゞァ-ヾ一-龯])|(?<=[ひ-ゞァ-ヾ一-龯])(?=[a-zA-Z])', term)
        
        for part in parts:
            if part:
                tokens.append(part.strip())
        
        return tokens if len(tokens) > 1 else [term]
    
    def _generate_synonyms(self, term: str) -> List[str]:
        """
        同義語を生成
        
        Args:
            term: 対象用語
            
        Returns:
            同義語のリスト
        """
        synonyms = []
        
        # スペース区切り版
        if re.search(r'[a-zA-Z][ひ-ゞァ-ヾ一-龯]', term):
            spaced = re.sub(r'([a-zA-Z]+)([ひ-ゞァ-ヾ一-龯]+)', r'\\1 \\2', term)
            synonyms.append(spaced)
        
        # カタカナ/ひらがな変換（簡易）
        if re.search(r'[ァ-ヾ]', term):
            hiragana_variant = self._katakana_to_hiragana(term)
            if hiragana_variant != term:
                synonyms.append(hiragana_variant)
        
        # 英語翻訳（既知のもののみ）
        translations = {
            '通知': 'notification',
            '設定': 'settings', 
            '認証': 'authentication',
            '環境': 'environment',
            '変数': 'variable',
            'データベース': 'database',
            'サーバー': 'server'
        }
        
        for jp, en in translations.items():
            if jp in term:
                synonyms.append(term.replace(jp, en))
        
        return list(set(synonyms))  # 重複除去
    
    def _categorize_term(self, term: str) -> str:
        """
        用語をカテゴリ分類
        
        Args:
            term: 対象用語
            
        Returns:
            カテゴリ名
        """
        for category, pattern in self.tech_patterns.items():
            if pattern.search(term):
                return category
        
        if re.search(r'[ァ-ヾ]', term):
            return 'katakana'
        elif re.search(r'[一-龯]', term):
            return 'kanji'
        elif re.search(r'[a-zA-Z]', term):
            return 'english'
        else:
            return 'other'
    
    def _katakana_to_hiragana(self, text: str) -> str:
        """
        カタカナをひらがなに変換（簡易版）
        
        Args:
            text: 変換対象テキスト
            
        Returns:
            ひらがな変換されたテキスト
        """
        result = ""
        for char in text:
            if 'ァ' <= char <= 'ヾ':
                # カタカナをひらがなに変換
                hiragana_char = chr(ord(char) - ord('ァ') + ord('ぁ'))
                result += hiragana_char
            else:
                result += char
        return result
    
    def _merge_with_existing_dictionary(self, new_dict: Dict) -> Dict:
        """
        既存辞書とマージ
        
        Args:
            new_dict: 新しい辞書データ
            
        Returns:
            マージされた辞書
        """
        existing_path = "data/compound_terms.json"
        
        if not Path(existing_path).exists():
            return new_dict
        
        try:
            with open(existing_path, 'r', encoding='utf-8') as f:
                existing_dict = json.load(f)
            
            # 既存の用語を優先してマージ
            merged_terms = existing_dict.get('compound_terms', {}).copy()
            
            for term, data in new_dict['compound_terms'].items():
                if term not in merged_terms:
                    merged_terms[term] = data
                else:
                    # 既存用語の場合は頻度情報のみ更新
                    merged_terms[term]['auto_frequency'] = data.get('frequency', 0)
            
            return {
                'compound_terms': merged_terms,
                'meta': {
                    'updated_at': '2025-01-24',
                    'version': '2.0.0',
                    'total_terms': len(merged_terms),
                    'auto_generated_count': len(new_dict['compound_terms'])
                }
            }
            
        except Exception as e:
            print(f"⚠️  既存辞書の読み込みに失敗: {e}")
            return new_dict
    
    def _save_dictionary(self, dictionary: Dict):
        """
        辞書をファイルに保存
        
        Args:
            dictionary: 保存する辞書データ
        """
        output_path = Path(self.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dictionary, f, ensure_ascii=False, indent=2)
        
        print(f"💾 カスタム辞書を保存しました: {output_path}")


if __name__ == '__main__':
    # カスタム辞書の自動生成
    generator = DictionaryGenerator()
    
    print("🚀 カスタム辞書の自動生成を開始します...")
    dictionary = generator.generate_dictionary()
    
    print("\n📋 生成された辞書のサマリー:")
    print(f"  - 総用語数: {len(dictionary['compound_terms'])}")
    
    # カテゴリ別統計
    categories = {}
    for term, data in dictionary['compound_terms'].items():
        cat = data.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    print("  - カテゴリ別用語数:")
    for cat, count in sorted(categories.items()):
        print(f"    {cat}: {count}語")
    
    print("\n✅ カスタム辞書生成完了!")