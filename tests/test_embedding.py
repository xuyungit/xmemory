import pytest
from app.db.elasticsearch.memory_repository import embed_text

def test_embed_text():
    # Test text to embed
    test_text = "This is a test sentence for embedding."
    
    # Get embedding
    embedding = embed_text(test_text)
    
    # Basic assertions
    assert embedding is not None
    assert isinstance(embedding, list)
    assert len(embedding) > 0
    
    # Check that all elements are floats
    assert all(isinstance(x, float) for x in embedding)
    
    # Check that the embedding vector is normalized (cosine similarity)
    # The sum of squares should be approximately 1
    sum_squares = sum(x * x for x in embedding)
    assert 0.99 <= sum_squares <= 1.01  # Allow for small floating point differences
    
    # Test with empty string
    empty_embedding = embed_text("")
    assert empty_embedding is None
    
    # Test with longer text
    long_text = "This is a much longer text that should also be properly embedded. " * 5
    long_embedding = embed_text(long_text)
    assert long_embedding is not None
    assert len(long_embedding) > 0 