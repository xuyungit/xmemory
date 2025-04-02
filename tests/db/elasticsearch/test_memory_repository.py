import pytest
import pytest_asyncio
from typing import List
from app.db.elasticsearch.memory_repository import MemoryRepository
from app.db.elasticsearch.models import MemoryDocument, MemoryType
from app.llm.embeddings import embed_text
from app.db.elasticsearch.client import get_es, es_client
import logging

@pytest_asyncio.fixture(scope="function")
async def memory_repository():
    # Create a new repository instance
    repo = MemoryRepository(index_name="test_memories")
    # Initialize the repository
    await repo.initialize()
    yield repo
    # Cleanup after test
    try:
        await repo.delete_index(are_you_sure=True)
    except Exception as e:
        logging.error(f"Error deleting index: {e}")

@pytest_asyncio.fixture(scope="function")
async def setup_test_memories(memory_repository):
    """Setup test memories for all tests."""
    memories = [
        MemoryDocument(
            content="I love programming in Python",
            user_id="test_user",
            tags=["programming", "python"],
            memory_type=MemoryType.RAW
        ),
        MemoryDocument(
            content="Python is a great language for data science",
            user_id="test_user",
            tags=["programming", "data-science"],
            memory_type=MemoryType.RAW
        ),
        MemoryDocument(
            content="I enjoy hiking in the mountains",
            user_id="test_user",
            tags=["hobbies", "outdoor"],
            memory_type=MemoryType.RAW
        ),
        MemoryDocument(
            content="The mountains are beautiful in summer",
            user_id="test_user",
            tags=["hobbies", "outdoor"],
            memory_type=MemoryType.RAW
        ),
        MemoryDocument(
            content="我爱吃鸡蛋西红柿",
            user_id="test_user",
            tags=["hobbies", "outdoor"],
            memory_type=MemoryType.RAW
        )
    ]
    
    # Create memories in the repository
    for memory in memories:
        await memory_repository.create_memory(memory)
    
    return memories

@pytest.mark.asyncio
async def test_search_by_vector(memory_repository, setup_test_memories):
    # Test vector search with a query about programming
    query = "programming language"
    query_vector = embed_text(query)
    
    # Search with vector similarity
    results = await memory_repository.search_by_vector(
        vector=query_vector,
        user_id="test_user",
        size=2
    )
    
    logging.info(f"Search results: {results}")
    logging.info("Test completed successfully")
    # Verify results
    assert len(results) == 2
    # The first result should be about programming
    assert "programming" in results[0].content.lower()
    assert "python" in results[0].content.lower()

    query_vector = embed_text("番茄")
    results = await memory_repository.search_by_vector(
        vector=query_vector,
        user_id="test_user",
        size=2
    )
    logging.info(f"Search results: {results}")
    

@pytest.mark.asyncio
async def test_hybrid_search(memory_repository, setup_test_memories):
    # Test hybrid search combining text and vector similarity
    query = "python programming"
    query_vector = embed_text(query)
    
    # Perform hybrid search
    results = await memory_repository.hybrid_search(
        query=query,
        vector=query_vector,
        user_id="test_user",
        size=2
    )
    
    # Verify results
    assert len(results) == 2
    # Results should be related to Python programming
    assert any("python" in result.content.lower() for result in results)
    assert any("programming" in result.content.lower() for result in results)

@pytest.mark.asyncio
async def test_search_with_tags(memory_repository, setup_test_memories):
    # Test vector search with tag filtering
    query = "outdoor activities"
    query_vector = embed_text(query)
    
    # Search with tag filter
    results = await memory_repository.search_by_vector(
        vector=query_vector,
        user_id="test_user",
        tags=["hobbies"],
        size=2
    )
    
    # Verify results
    assert len(results) == 2
    # Results should be about outdoor activities
    assert all("hiking" in result.content.lower() or "mountains" in result.content.lower() for result in results)
    assert all("hobbies" in result.tags for result in results) 