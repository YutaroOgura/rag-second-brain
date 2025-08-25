"""Database manager for ChromaDB"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from pathlib import Path

class DatabaseManager:
    """ChromaDB管理クラス"""
    
    def __init__(self, db_path: str = "/home/ogura/.rag/chroma"):
        """データベースマネージャーの初期化"""
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(allow_reset=True)
        )
        
        # デフォルトコレクションを取得または作成
        self.collection = self.client.get_or_create_collection("documents")
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """ドキュメントを追加"""
        try:
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]
            
            self.collection.add(
                documents=documents,
                metadatas=metadatas or [{}] * len(documents),
                ids=ids
            )
            return True
        except Exception as e:
            print(f"Error adding documents: {e}")
            return False
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """ドキュメントを検索"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )
            
            # 結果を整形
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'text': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0
                    })
            
            return formatted_results
        except Exception as e:
            print(f"Error searching: {e}")
            return []
    
    def get_stats(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """統計情報を取得"""
        try:
            count = self.collection.count()
            
            if project_id:
                # プロジェクトフィルタ付きの場合
                results = self.collection.get(
                    where={"project": project_id} if project_id else None,
                    limit=10000
                )
                filtered_count = len(results['ids']) if results['ids'] else 0
                
                return {
                    'total_documents': filtered_count,
                    'project': project_id,
                    'collections': ['documents']
                }
            
            return {
                'total_documents': count,
                'collections': ['documents'],
                'db_path': str(self.db_path)
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {
                'total_documents': 0,
                'collections': [],
                'error': str(e)
            }
    
    def list_projects(self) -> List[str]:
        """プロジェクト一覧を取得"""
        try:
            # すべてのメタデータを取得
            results = self.collection.get(limit=10000)
            
            projects = set()
            if results['metadatas']:
                for metadata in results['metadatas']:
                    if metadata and 'project' in metadata:
                        projects.add(metadata['project'])
            
            return sorted(list(projects))
        except Exception as e:
            print(f"Error listing projects: {e}")
            return []