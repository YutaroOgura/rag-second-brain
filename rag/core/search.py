"""Search engine for RAG system"""
from typing import List, Dict, Any, Optional
from .database import DatabaseManager

class SearchEngine:
    """検索エンジンクラス"""
    
    def __init__(self, db_manager: DatabaseManager):
        """検索エンジンの初期化"""
        self.db_manager = db_manager
    
    def search(
        self,
        query: str,
        search_type: str = "hybrid",
        top_k: int = 5,
        project_id: Optional[str] = None,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """ドキュメントを検索"""
        
        # フィルタの構築
        where = {}
        if project_id:
            where['project'] = project_id
        if filters:
            where.update(filters)
        
        # 検索実行
        results = self.db_manager.search(
            query=query,
            n_results=top_k,
            where=where if where else None
        )
        
        return results
    
    def vector_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """ベクトル検索"""
        return self.search(query, search_type="vector", top_k=top_k)
    
    def keyword_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """キーワード検索"""
        return self.search(query, search_type="keyword", top_k=top_k)
    
    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """ハイブリッド検索"""
        return self.search(query, search_type="hybrid", top_k=top_k)