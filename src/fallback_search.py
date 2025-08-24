"""
フォールバック機能付き検索モジュール
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import sys

# 親ディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.query_preprocessor import QueryPreprocessor
from rag.core.search_engine import SearchEngine
from rag.core.index_manager import IndexManager

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """検索結果を表すデータクラス"""
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    search_method: str  # 'direct', 'preprocessed', 'fallback', 'split'


class FallbackSearchEngine:
    """
    フォールバック機能付き検索エンジン
    """
    
    def __init__(
        self,
        index_path: Optional[str] = None,
        embedding_model: Optional[str] = None,
        compound_terms_path: Optional[str] = None
    ):
        """
        初期化
        
        Args:
            index_path: インデックスディレクトリのパス
            embedding_model: 埋め込みモデル名
            compound_terms_path: 複合語辞書のパス
        """
        self.preprocessor = QueryPreprocessor(compound_terms_path)
        
        # 既存の検索エンジンとインデックスマネージャーを初期化
        self.index_manager = IndexManager(
            index_path=index_path or str(Path.home() / ".rag" / "indices")
        )
        self.search_engine = SearchEngine(
            index_manager=self.index_manager,
            embedding_model=embedding_model or "intfloat/multilingual-e5-base"
        )
        
    async def search_with_fallback(
        self,
        query: str,
        search_type: str = "hybrid",
        top_k: int = 5,
        min_results: int = 1,
        project_id: Optional[str] = None
    ) -> List[SearchResult]:
        """
        フォールバック機能付き検索
        
        1. 通常検索を実行
        2. 結果が閾値未満の場合、クエリを前処理して再検索
        3. それでも結果が不十分な場合、クエリを分割して検索
        4. 結果をマージしてランキング
        
        Args:
            query: 検索クエリ
            search_type: 検索タイプ ('keyword', 'vector', 'hybrid')
            top_k: 返す結果の最大数
            min_results: 最小必要結果数（これ未満の場合フォールバック発動）
            project_id: プロジェクトID（フィルタリング用）
        
        Returns:
            検索結果のリスト
        """
        all_results = []
        seen_docs = set()
        
        # Step 1: 直接検索
        try:
            direct_results = await self._execute_search(
                query, search_type, top_k * 2, project_id
            )
            for result in direct_results:
                if result['document_id'] not in seen_docs:
                    all_results.append(self._create_search_result(result, 'direct'))
                    seen_docs.add(result['document_id'])
            
            if len(all_results) >= min_results:
                return self._rank_and_limit(all_results, top_k)
                
        except Exception as e:
            logger.warning(f"直接検索でエラー: {e}")
        
        # Step 2: 前処理されたクエリで検索
        preprocessed_queries = self.preprocessor.preprocess(query)
        for preprocessed_query in preprocessed_queries[1:3]:  # 最大2つの前処理クエリを試す
            if preprocessed_query == query:
                continue
                
            try:
                preprocessed_results = await self._execute_search(
                    preprocessed_query, search_type, top_k, project_id
                )
                for result in preprocessed_results:
                    if result['document_id'] not in seen_docs:
                        all_results.append(self._create_search_result(result, 'preprocessed'))
                        seen_docs.add(result['document_id'])
                
                if len(all_results) >= min_results:
                    return self._rank_and_limit(all_results, top_k)
                    
            except Exception as e:
                logger.warning(f"前処理クエリ '{preprocessed_query}' でエラー: {e}")
        
        # Step 3: クエリ分割によるフォールバック
        split_parts = self.preprocessor.split_query(query)
        if len(split_parts) > 1:
            # 各部分で検索
            for part in split_parts:
                try:
                    part_results = await self._execute_search(
                        part, search_type, top_k // len(split_parts) + 1, project_id
                    )
                    for result in part_results:
                        if result['document_id'] not in seen_docs:
                            all_results.append(self._create_search_result(result, 'split'))
                            seen_docs.add(result['document_id'])
                            
                except Exception as e:
                    logger.warning(f"分割クエリ '{part}' でエラー: {e}")
            
            # 複数の部分を組み合わせた検索も試す
            if len(split_parts) == 2:
                combined_query = f"{split_parts[0]} {split_parts[1]}"
                try:
                    combined_results = await self._execute_search(
                        combined_query, search_type, top_k, project_id
                    )
                    for result in combined_results:
                        if result['document_id'] not in seen_docs:
                            all_results.append(self._create_search_result(result, 'fallback'))
                            seen_docs.add(result['document_id'])
                            
                except Exception as e:
                    logger.warning(f"結合クエリ '{combined_query}' でエラー: {e}")
        
        return self._rank_and_limit(all_results, top_k)
    
    async def _execute_search(
        self,
        query: str,
        search_type: str,
        limit: int,
        project_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        実際の検索を実行（既存の検索エンジンを使用）
        
        Args:
            query: 検索クエリ
            search_type: 検索タイプ
            limit: 結果の最大数
            project_id: プロジェクトID
        
        Returns:
            検索結果のリスト
        """
        # 既存のSearchEngineのsearchメソッドを呼び出す
        results = self.search_engine.search(
            query=query,
            search_type=search_type,
            top_k=limit,
            project_id=project_id
        )
        
        # 結果を辞書形式に変換
        formatted_results = []
        for result in results:
            formatted_results.append({
                'document_id': result.get('id', ''),
                'content': result.get('content', ''),
                'score': result.get('score', 0.0),
                'metadata': result.get('metadata', {})
            })
        
        return formatted_results
    
    def _create_search_result(self, result_dict: Dict[str, Any], method: str) -> SearchResult:
        """
        辞書形式の結果をSearchResultオブジェクトに変換
        
        Args:
            result_dict: 結果の辞書
            method: 検索方法
        
        Returns:
            SearchResultオブジェクト
        """
        return SearchResult(
            document_id=result_dict.get('document_id', ''),
            content=result_dict.get('content', ''),
            score=result_dict.get('score', 0.0),
            metadata=result_dict.get('metadata', {}),
            search_method=method
        )
    
    def _rank_and_limit(self, results: List[SearchResult], top_k: int) -> List[SearchResult]:
        """
        結果をランキングして上位k件を返す
        
        Args:
            results: 全検索結果
            top_k: 返す結果の最大数
        
        Returns:
            ランキングされた上位k件の結果
        """
        # 検索方法による重み付け
        method_weights = {
            'direct': 1.0,
            'preprocessed': 0.8,
            'fallback': 0.6,
            'split': 0.4
        }
        
        # 重み付きスコアを計算
        for result in results:
            weight = method_weights.get(result.search_method, 0.5)
            result.score = result.score * weight
        
        # スコアでソート
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:top_k]
    
    async def search_with_variations(
        self,
        query: str,
        search_type: str = "hybrid",
        top_k: int = 5,
        project_id: Optional[str] = None
    ) -> List[SearchResult]:
        """
        クエリバリエーションを使った検索
        
        Args:
            query: 検索クエリ
            search_type: 検索タイプ
            top_k: 返す結果の最大数
            project_id: プロジェクトID
        
        Returns:
            検索結果のリスト
        """
        variations = self.preprocessor.get_query_variations(query, max_variations=3)
        all_results = []
        seen_docs = set()
        
        for variation in variations:
            try:
                results = await self._execute_search(
                    variation['query'],
                    search_type,
                    top_k,
                    project_id
                )
                
                for result in results:
                    if result['document_id'] not in seen_docs:
                        search_result = self._create_search_result(result, variation['type'])
                        # バリエーションの重みを適用
                        search_result.score *= variation['weight']
                        all_results.append(search_result)
                        seen_docs.add(result['document_id'])
                        
            except Exception as e:
                logger.warning(f"バリエーション '{variation['query']}' でエラー: {e}")
        
        return self._rank_and_limit(all_results, top_k)
    
    def search_sync(
        self,
        query: str,
        search_type: str = "hybrid",
        top_k: int = 5,
        min_results: int = 1,
        project_id: Optional[str] = None
    ) -> List[SearchResult]:
        """
        同期版の検索メソッド（既存コードとの互換性のため）
        
        Args:
            query: 検索クエリ
            search_type: 検索タイプ
            top_k: 返す結果の最大数
            min_results: 最小必要結果数
            project_id: プロジェクトID
        
        Returns:
            検索結果のリスト
        """
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            self.search_with_fallback(query, search_type, top_k, min_results, project_id)
        )