"""Vectorizer for text embedding using sentence-transformers."""

import logging
import numpy as np
from typing import List, Dict, Any, Union
import sentence_transformers
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class Vectorizer:
    """Handles text vectorization using sentence-transformers models."""
    
    def __init__(
        self, 
        model_name: str = "intfloat/multilingual-e5-base",
        device: str = "cpu"
    ):
        """Initialize vectorizer with specified model.
        
        Args:
            model_name: Name of the sentence-transformers model
            device: Device to run the model on ("cpu" or "cuda")
        """
        self.model_name = model_name
        self.device = device
        
        try:
            logger.info(f"Loading model: {model_name} on device: {device}")
            self.model = SentenceTransformer(model_name, device=device)
            logger.info(f"Model loaded successfully: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
    
    def vectorize(self, text: str) -> np.ndarray:
        """Vectorize a single text string.
        
        Args:
            text: Text to vectorize
            
        Returns:
            Numpy array representing the text embedding
            
        Raises:
            ValueError: If text is empty or None
        """
        if not text or text is None:
            raise ValueError("Text cannot be empty")
        
        if isinstance(text, str) and not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            # Generate embedding with normalization
            embedding = self.model.encode(
                text,
                convert_to_tensor=False,
                normalize_embeddings=True
            )
            
            # Ensure return type is numpy array
            if not isinstance(embedding, np.ndarray):
                embedding = np.array(embedding)
            
            logger.debug(f"Vectorized text with shape: {embedding.shape}")
            return embedding
        except Exception as e:
            logger.error(f"Failed to vectorize text: {e}")
            raise
    
    def batch_vectorize(
        self, 
        texts: List[str], 
        batch_size: int = 32
    ) -> np.ndarray:
        """Vectorize a batch of text strings.
        
        Args:
            texts: List of texts to vectorize
            batch_size: Batch size for processing
            
        Returns:
            Numpy array of shape (len(texts), embedding_dim)
            
        Raises:
            ValueError: If texts list is empty
        """
        if not texts or len(texts) == 0:
            raise ValueError("Texts list cannot be empty")
        
        # Filter out empty strings
        valid_texts = [text for text in texts if text and text.strip()]
        if len(valid_texts) != len(texts):
            logger.warning(f"Filtered out {len(texts) - len(valid_texts)} empty texts")
        
        if not valid_texts:
            raise ValueError("No valid texts to vectorize")
        
        try:
            # Generate embeddings in batch with normalization
            embeddings = self.model.encode(
                valid_texts,
                convert_to_tensor=False,
                normalize_embeddings=True,
                batch_size=batch_size
            )
            
            # Ensure return type is numpy array
            if not isinstance(embeddings, np.ndarray):
                embeddings = np.array(embeddings)
            
            logger.debug(f"Batch vectorized {len(valid_texts)} texts with shape: {embeddings.shape}")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to batch vectorize texts: {e}")
            raise
    
    def calculate_similarity(
        self, 
        vector1: np.ndarray, 
        vector2: np.ndarray
    ) -> float:
        """Calculate cosine similarity between two vectors.
        
        Args:
            vector1: First vector
            vector2: Second vector
            
        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        try:
            # Normalize vectors
            vector1_norm = vector1 / (np.linalg.norm(vector1) + 1e-8)
            vector2_norm = vector2 / (np.linalg.norm(vector2) + 1e-8)
            
            # Calculate cosine similarity
            similarity = np.dot(vector1_norm, vector2_norm)
            
            # Ensure similarity is in [0, 1] range (convert from [-1, 1])
            similarity = (similarity + 1) / 2
            
            # Clamp to valid range
            similarity = np.clip(similarity, 0.0, 1.0)
            
            return float(similarity)
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        try:
            embedding_dim = self.model.get_sentence_embedding_dimension()
            
            return {
                "model_name": self.model_name,
                "device": self.device,
                "embedding_dimension": embedding_dim
            }
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {
                "model_name": self.model_name,
                "device": self.device,
                "embedding_dimension": None,
                "error": str(e)
            }
    
    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension of the model.
        
        Returns:
            Embedding dimension size
        """
        try:
            return self.model.get_sentence_embedding_dimension()
        except Exception as e:
            logger.error(f"Failed to get embedding dimension: {e}")
            raise
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text before vectorization.
        
        Args:
            text: Raw text to preprocess
            
        Returns:
            Preprocessed text
        """
        if not text:
            return ""
        
        # Basic preprocessing
        text = text.strip()
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        return text
    
    def vectorize_with_preprocessing(self, text: str) -> np.ndarray:
        """Vectorize text with preprocessing.
        
        Args:
            text: Text to vectorize
            
        Returns:
            Numpy array representing the text embedding
        """
        preprocessed_text = self.preprocess_text(text)
        return self.vectorize(preprocessed_text)
    
    def batch_vectorize_with_preprocessing(
        self, 
        texts: List[str], 
        batch_size: int = 32
    ) -> np.ndarray:
        """Batch vectorize texts with preprocessing.
        
        Args:
            texts: List of texts to vectorize
            batch_size: Batch size for processing
            
        Returns:
            Numpy array of embeddings
        """
        preprocessed_texts = [self.preprocess_text(text) for text in texts]
        return self.batch_vectorize(preprocessed_texts, batch_size)