"""Vectorizer for text embedding"""
import numpy as np
from typing import List, Union

class Vectorizer:
    """テキストのベクトル化クラス"""
    
    def __init__(self, model_name: str = "sentence-transformers/multilingual-e5-base"):
        """ベクトライザーの初期化"""
        self.model_name = model_name
        # 実際のモデルロードは省略（ChromaDBが内部で処理）
    
    def vectorize(self, text: Union[str, List[str]]) -> np.ndarray:
        """テキストをベクトル化"""
        # ChromaDBが内部でベクトル化を処理するため、ダミー実装
        if isinstance(text, str):
            text = [text]
        
        # ダミーベクトル（実際はChromaDBが処理）
        return np.random.rand(len(text), 768)
    
    def batch_vectorize(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """バッチでテキストをベクトル化"""
        return self.vectorize(texts)