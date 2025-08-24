"""
Phase 1の統合テストスイート
"""

import pytest
import asyncio
import time
import json
from pathlib import Path
import sys

# テスト対象モジュールをインポート
sys.path.append(str(Path(__file__).parent.parent))

from src.query_preprocessor import QueryPreprocessor
from src.fallback_search import FallbackSearchEngine, SearchResult


class TestQueryPreprocessor:
    """QueryPreprocessorのテスト"""
    
    @pytest.fixture
    def preprocessor(self):
        """テスト用のプリプロセッサーインスタンス"""
        return QueryPreprocessor()
    
    def test_compound_word_recognition(self, preprocessor):
        """複合語の認識テスト"""
        query = "Slack通知の設定方法"
        results = preprocessor.preprocess(query)
        
        # 元のクエリが含まれていることを確認
        assert query in results
        
        # トークン分割版が含まれていることを確認
        assert any("Slack 通知" in r for r in results)
        
        # 同義語版が含まれていることを確認
        assert any("Slack notification" in r for r in results)
    
    def test_mixed_language_handling(self, preprocessor):
        """英語・日本語混在の処理テスト"""
        query = "Docker環境でのAPI認証"
        results = preprocessor.preprocess(query)
        
        # スペース挿入版が含まれていることを確認
        assert any("Docker 環境" in r for r in results)
        assert any("API 認証" in r for r in results)
    
    def test_query_splitting(self, preprocessor):
        """クエリ分割のテスト"""
        query = "Slack通知とRedis接続"
        parts = preprocessor.split_query(query)
        
        # 期待される部分が含まれていることを確認
        assert "Slack" in parts
        assert "通知" in parts
        assert "Redis" in parts
        assert "接続" in parts
    
    def test_query_variations(self, preprocessor):
        """クエリバリエーション生成のテスト"""
        query = "環境変数の設定"
        variations = preprocessor.get_query_variations(query, max_variations=5)
        
        # 元のクエリが最高優先度であることを確認
        assert variations[0]['query'] == query
        assert variations[0]['weight'] == 1.0
        assert variations[0]['type'] == 'original'
        
        # バリエーションが生成されていることを確認
        assert len(variations) > 1
        assert all(v['weight'] <= 1.0 for v in variations)


class TestPhase1Integration:
    """Phase 1の統合テスト"""
    
    @pytest.fixture
    def test_queries(self):
        """テストクエリのリスト"""
        return [
            ("Slack通知", 21),  # 期待される結果数
            ("環境変数", 15),
            ("バッチ処理", 10),
            ("API認証", 8),
            ("Docker環境", 12),
            ("PostgreSQL設定", 7),
            ("エラーハンドリング", 9),
            ("JWT認証", 6),
            ("Redis接続", 5),
            ("Laravel設定", 11),
            ("Vue.js", 8),
            ("マイグレーション", 14),
            ("Ultra Pay", 4),
            ("PayBlend", 3),
            ("プリペイドカード", 10),
            ("AWS S3", 6),
            ("GMO決済", 5),
            ("セブン銀行", 4),
            ("Multi-tenant", 3),
            ("決済処理", 8),
        ]
    
    @pytest.fixture
    def fallback_engine(self):
        """テスト用のフォールバック検索エンジン"""
        return FallbackSearchEngine()
    
    @pytest.mark.asyncio
    async def test_compound_word_search_accuracy(self, fallback_engine, test_queries):
        """複合語検索の精度テスト"""
        successful_searches = 0
        total_searches = len(test_queries)
        
        for query, expected_min_results in test_queries[:5]:  # 最初の5つでテスト
            try:
                results = await fallback_engine.search_with_fallback(
                    query=query,
                    search_type="hybrid",
                    top_k=10,
                    min_results=1
                )
                
                if len(results) > 0:
                    successful_searches += 1
                    print(f"✓ '{query}': {len(results)}件の結果")
                else:
                    print(f"✗ '{query}': 結果なし")
                    
            except Exception as e:
                print(f"✗ '{query}': エラー - {e}")
        
        # 60%以上の成功率を確認
        success_rate = successful_searches / 5
        assert success_rate >= 0.6, f"検索成功率が60%未満: {success_rate * 100:.1f}%"
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, fallback_engine):
        """フォールバックメカニズムのテスト"""
        # 意図的に難しいクエリでフォールバックをトリガー
        query = "存在しない複合語クエリ"
        
        results = await fallback_engine.search_with_fallback(
            query=query,
            search_type="hybrid",
            top_k=5,
            min_results=1
        )
        
        # フォールバックが動作して何らかの結果を返すことを確認
        assert isinstance(results, list)
        
        # 結果がSearchResultオブジェクトであることを確認
        if results:
            assert all(isinstance(r, SearchResult) for r in results)
    
    @pytest.mark.asyncio
    async def test_response_time(self, fallback_engine):
        """レスポンスタイム測定（目標: <500ms）"""
        query = "Slack通知"
        
        start_time = time.time()
        results = await fallback_engine.search_with_fallback(
            query=query,
            search_type="hybrid",
            top_k=5
        )
        elapsed_time = (time.time() - start_time) * 1000  # ミリ秒に変換
        
        print(f"検索時間: {elapsed_time:.2f}ms")
        
        # 初回は遅い可能性があるので、2回目を測定
        start_time = time.time()
        results = await fallback_engine.search_with_fallback(
            query=query,
            search_type="hybrid",
            top_k=5
        )
        elapsed_time = (time.time() - start_time) * 1000
        
        print(f"2回目の検索時間: {elapsed_time:.2f}ms")
        
        # 500ms以内であることを確認（初回読み込みを除く）
        assert elapsed_time < 500, f"レスポンスタイムが500msを超過: {elapsed_time:.2f}ms"
    
    @pytest.mark.asyncio
    async def test_search_with_variations(self, fallback_engine):
        """バリエーション検索のテスト"""
        query = "Docker環境"
        
        results = await fallback_engine.search_with_variations(
            query=query,
            search_type="hybrid",
            top_k=5
        )
        
        # 結果が返されることを確認
        assert isinstance(results, list)
        
        # 結果がランキングされていることを確認（スコア降順）
        if len(results) > 1:
            scores = [r.score for r in results]
            assert scores == sorted(scores, reverse=True)
    
    def test_sync_search_compatibility(self, fallback_engine):
        """同期版検索メソッドの互換性テスト"""
        query = "API認証"
        
        results = fallback_engine.search_sync(
            query=query,
            search_type="hybrid",
            top_k=5
        )
        
        # 結果が返されることを確認
        assert isinstance(results, list)
        
        # SearchResultオブジェクトであることを確認
        if results:
            assert all(isinstance(r, SearchResult) for r in results)
            assert all(hasattr(r, 'search_method') for r in results)


class TestCompoundTermsDictionary:
    """複合語辞書のテスト"""
    
    def test_dictionary_structure(self):
        """辞書構造の妥当性テスト"""
        dict_path = Path(__file__).parent.parent / "data" / "compound_terms.json"
        
        assert dict_path.exists(), "複合語辞書ファイルが存在しない"
        
        with open(dict_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'compound_terms' in data
        compound_terms = data['compound_terms']
        
        # 必須の複合語が含まれていることを確認
        required_terms = ["Slack通知", "環境変数", "Docker環境", "API認証"]
        for term in required_terms:
            assert term in compound_terms, f"必須複合語 '{term}' が辞書に存在しない"
        
        # 各エントリの構造を確認
        for term, info in compound_terms.items():
            assert 'weight' in info, f"'{term}' に weight がない"
            assert 0.0 <= info['weight'] <= 1.0, f"'{term}' の weight が範囲外"
            
            if 'tokens' in info:
                assert isinstance(info['tokens'], list), f"'{term}' の tokens がリストでない"
            
            if 'synonyms' in info:
                assert isinstance(info['synonyms'], list), f"'{term}' の synonyms がリストでない"


if __name__ == "__main__":
    # テスト実行
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])