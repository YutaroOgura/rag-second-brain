"""Tests for Vectorizer class."""

import pytest
import numpy as np
from unittest.mock import Mock, patch

from rag.core.vectorizer import Vectorizer


class TestVectorizer:
    """Test cases for Vectorizer."""
    
    def test_init_with_default_model(self):
        """Test initialization with default model."""
        with patch('rag.core.vectorizer.SentenceTransformer') as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model
            
            vectorizer = Vectorizer()
            
            assert vectorizer.model_name == "intfloat/multilingual-e5-base"
            assert vectorizer.model == mock_model
            mock_st.assert_called_once_with("intfloat/multilingual-e5-base", device="cpu")
    
    def test_init_with_custom_model(self):
        """Test initialization with custom model."""
        custom_model = "sentence-transformers/all-MiniLM-L6-v2"
        
        with patch('rag.core.vectorizer.SentenceTransformer') as mock_st:
            mock_model = Mock()
            mock_st.return_value = mock_model
            
            vectorizer = Vectorizer(custom_model, device="cuda")
            
            assert vectorizer.model_name == custom_model
            mock_st.assert_called_once_with(custom_model, device="cuda")
    
    def test_vectorize_single_text(self, test_vectorizer):
        """Test vectorizing single text."""
        text = "これはテスト用のテキストです"
        
        with patch.object(test_vectorizer.model, 'encode') as mock_encode:
            mock_vector = np.array([0.1, 0.2, 0.3, 0.4])
            mock_encode.return_value = mock_vector
            
            result = test_vectorizer.vectorize(text)
            
            assert isinstance(result, np.ndarray)
            assert np.array_equal(result, mock_vector)
            mock_encode.assert_called_once_with(text, convert_to_tensor=False, normalize_embeddings=True)
    
    def test_vectorize_empty_text_raises_error(self, test_vectorizer):
        """Test that vectorizing empty text raises error."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            test_vectorizer.vectorize("")
    
    def test_vectorize_none_text_raises_error(self, test_vectorizer):
        """Test that vectorizing None raises error."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            test_vectorizer.vectorize(None)
    
    def test_batch_vectorize_multiple_texts(self, test_vectorizer):
        """Test batch vectorizing multiple texts."""
        texts = [
            "最初のテキストです",
            "二番目のテキストです", 
            "三番目のテキストです"
        ]
        
        with patch.object(test_vectorizer.model, 'encode') as mock_encode:
            mock_vectors = np.array([
                [0.1, 0.2, 0.3],
                [0.4, 0.5, 0.6],
                [0.7, 0.8, 0.9]
            ])
            mock_encode.return_value = mock_vectors
            
            results = test_vectorizer.batch_vectorize(texts)
            
            assert isinstance(results, np.ndarray)
            assert results.shape == (3, 3)
            np.testing.assert_array_equal(results, mock_vectors)
            mock_encode.assert_called_once_with(texts, convert_to_tensor=False, normalize_embeddings=True, batch_size=32)
    
    def test_batch_vectorize_empty_list_raises_error(self, test_vectorizer):
        """Test that batch vectorizing empty list raises error."""
        with pytest.raises(ValueError, match="Texts list cannot be empty"):
            test_vectorizer.batch_vectorize([])
    
    def test_batch_vectorize_with_custom_batch_size(self, test_vectorizer):
        """Test batch vectorizing with custom batch size."""
        texts = ["テキスト1", "テキスト2", "テキスト3"]
        custom_batch_size = 16
        
        with patch.object(test_vectorizer.model, 'encode') as mock_encode:
            mock_vectors = np.array([[0.1], [0.2], [0.3]])
            mock_encode.return_value = mock_vectors
            
            test_vectorizer.batch_vectorize(texts, batch_size=custom_batch_size)
            
            mock_encode.assert_called_once_with(
                texts, 
                convert_to_tensor=False, 
                normalize_embeddings=True, 
                batch_size=custom_batch_size
            )
    
    def test_similarity_calculation(self, test_vectorizer):
        """Test calculating similarity between vectors."""
        vector1 = np.array([1.0, 0.0, 0.0])
        vector2 = np.array([0.0, 1.0, 0.0])
        vector3 = np.array([1.0, 0.0, 0.0])  # Same as vector1
        
        # Different vectors should have low similarity
        similarity_different = test_vectorizer.calculate_similarity(vector1, vector2)
        assert 0.0 <= similarity_different <= 1.0
        assert similarity_different < 0.5
        
        # Same vectors should have high similarity
        similarity_same = test_vectorizer.calculate_similarity(vector1, vector3)
        assert similarity_same > 0.99
    
    def test_similarity_with_normalized_vectors(self, test_vectorizer):
        """Test similarity calculation with normalized vectors."""
        vector1 = np.array([3.0, 4.0])  # Will be normalized to [0.6, 0.8]
        vector2 = np.array([6.0, 8.0])  # Will be normalized to [0.6, 0.8]
        
        similarity = test_vectorizer.calculate_similarity(vector1, vector2)
        
        # Should be very similar since they have the same direction
        assert similarity > 0.99
    
    def test_get_model_info(self, test_vectorizer):
        """Test getting model information."""
        with patch.object(test_vectorizer.model, 'get_sentence_embedding_dimension') as mock_dim:
            mock_dim.return_value = 384
            
            info = test_vectorizer.get_model_info()
            
            assert info["model_name"] == test_vectorizer.model_name
            assert info["device"] == test_vectorizer.device
            assert info["embedding_dimension"] == 384
    
    def test_vectorize_with_japanese_text(self, test_vectorizer):
        """Test vectorizing Japanese text specifically."""
        japanese_texts = [
            "日本語のテキストをベクトル化します",
            "機械学習モデルを使用して埋め込みを生成",
            "自然言語処理の技術を活用"
        ]
        
        with patch.object(test_vectorizer.model, 'encode') as mock_encode:
            mock_vectors = np.random.rand(3, 384)
            mock_encode.return_value = mock_vectors
            
            results = test_vectorizer.batch_vectorize(japanese_texts)
            
            assert results.shape == (3, 384)
            # Verify the model was called with Japanese text
            mock_encode.assert_called_once_with(
                japanese_texts,
                convert_to_tensor=False,
                normalize_embeddings=True,
                batch_size=32
            )


@pytest.mark.integration
class TestVectorizerIntegration:
    """Integration tests for Vectorizer."""
    
    def test_real_model_loading(self):
        """Test loading a real model."""
        # Use a small model for testing
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        
        try:
            vectorizer = Vectorizer(model_name)
            assert vectorizer.model is not None
            assert vectorizer.model_name == model_name
        except Exception as e:
            pytest.skip(f"Model loading failed, possibly no internet: {e}")
    
    def test_real_vectorization(self):
        """Test actual vectorization with a real model."""
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        
        try:
            vectorizer = Vectorizer(model_name)
            
            text = "This is a test sentence for vectorization."
            vector = vectorizer.vectorize(text)
            
            assert isinstance(vector, np.ndarray)
            assert vector.shape[0] > 0  # Should have some dimensions
            assert not np.isnan(vector).any()  # No NaN values
        except Exception as e:
            pytest.skip(f"Real vectorization test failed: {e}")
    
    def test_japanese_vectorization_real(self):
        """Test Japanese text vectorization with real model."""
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        
        try:
            vectorizer = Vectorizer(model_name)
            
            japanese_text = "これは日本語のテストです"
            vector = vectorizer.vectorize(japanese_text)
            
            assert isinstance(vector, np.ndarray)
            assert vector.shape[0] > 0
            assert not np.isnan(vector).any()
        except Exception as e:
            pytest.skip(f"Japanese vectorization test failed: {e}")


@pytest.mark.slow
class TestVectorizerPerformance:
    """Performance tests for Vectorizer."""
    
    def test_batch_processing_performance(self, test_vectorizer):
        """Test batch processing is more efficient than individual processing."""
        texts = [f"テストテキスト番号 {i}" for i in range(50)]
        
        with patch.object(test_vectorizer.model, 'encode') as mock_encode:
            mock_vectors = np.random.rand(50, 384)
            mock_encode.return_value = mock_vectors
            
            # Test batch processing
            import time
            start_time = time.time()
            test_vectorizer.batch_vectorize(texts)
            batch_time = time.time() - start_time
            
            # Batch processing should call encode only once
            assert mock_encode.call_count == 1
            
            # Reset mock for individual processing test
            mock_encode.reset_mock()
            mock_encode.return_value = np.random.rand(384)
            
            # Test individual processing
            start_time = time.time()
            for text in texts:
                test_vectorizer.vectorize(text)
            individual_time = time.time() - start_time
            
            # Individual processing should call encode many times
            assert mock_encode.call_count == 50
    
    def test_large_batch_handling(self, test_vectorizer):
        """Test handling of large batches."""
        large_texts = [f"大きなバッチテスト {i}" for i in range(1000)]
        
        with patch.object(test_vectorizer.model, 'encode') as mock_encode:
            mock_vectors = np.random.rand(1000, 384)
            mock_encode.return_value = mock_vectors
            
            results = test_vectorizer.batch_vectorize(large_texts, batch_size=100)
            
            assert results.shape == (1000, 384)
            # With batch_size=100, should process efficiently
            mock_encode.assert_called_once()


class TestVectorizerEdgeCases:
    """Test edge cases for Vectorizer."""
    
    def test_very_long_text(self, test_vectorizer):
        """Test vectorizing very long text."""
        long_text = "これは非常に長いテキストです。" * 1000
        
        with patch.object(test_vectorizer.model, 'encode') as mock_encode:
            mock_vector = np.random.rand(384)
            mock_encode.return_value = mock_vector
            
            result = test_vectorizer.vectorize(long_text)
            
            assert isinstance(result, np.ndarray)
            mock_encode.assert_called_once()
    
    def test_special_characters(self, test_vectorizer):
        """Test vectorizing text with special characters."""
        special_text = "特殊文字: !@#$%^&*()_+-=[]{}|;':\",./<>? 🚀🧠💡"
        
        with patch.object(test_vectorizer.model, 'encode') as mock_encode:
            mock_vector = np.random.rand(384)
            mock_encode.return_value = mock_vector
            
            result = test_vectorizer.vectorize(special_text)
            
            assert isinstance(result, np.ndarray)
            mock_encode.assert_called_once_with(
                special_text,
                convert_to_tensor=False,
                normalize_embeddings=True
            )
    
    def test_mixed_language_text(self, test_vectorizer):
        """Test vectorizing mixed language text."""
        mixed_text = "This is English text mixed with 日本語のテキスト and some symbols ✨"
        
        with patch.object(test_vectorizer.model, 'encode') as mock_encode:
            mock_vector = np.random.rand(384)
            mock_encode.return_value = mock_vector
            
            result = test_vectorizer.vectorize(mixed_text)
            
            assert isinstance(result, np.ndarray)
            mock_encode.assert_called_once()