import asyncio
import pytest
from datetime import datetime
from app.db.elasticsearch.memory_repository import MemoryRepository
from app.db.elasticsearch.models import MemoryDocument, MemoryType
from elasticsearch import ConnectionError

async def wait_for_consistency(seconds: int = 1):
    """Add a small delay to allow Elasticsearch to process operations."""
    await asyncio.sleep(seconds)

@pytest.mark.asyncio
async def test_memory_repository_smoke():
    try:
        # 1. 初始化 MemoryRepository
        print("Initializing MemoryRepository...")
        repo = MemoryRepository()
        await repo.initialize()
        print("MemoryRepository initialized successfully")

        # 2. 创建测试数据
        print("Creating test memories...")
        test_memories = [
            MemoryDocument(
                title="测试记忆1",
                content="这是一个测试记忆的内容",
                memory_type=MemoryType.RAW,
                tags=["测试", "记忆"],
                user_id="test_user_1",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            MemoryDocument(
                title="测试记忆2",
                content="这是另一个测试记忆的内容",
                memory_type=MemoryType.INSIGHT,
                tags=["测试", "洞察"],
                user_id="test_user_1",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
        ]

        # 3. 插入测试数据
        memory_ids = []
        for memory in test_memories:
            try:
                memory_id = await repo.create_memory(memory)
                memory_ids.append(memory_id)
                print(f"Created memory with ID: {memory_id}")
                # Wait for Elasticsearch to process the operation
            except Exception as e:
                print(f"Error creating memory: {str(e)}")
                raise

        # 4. 测试获取单个记忆
        await wait_for_consistency(2)
        for memory_id in memory_ids:
            try:
                print(f"Attempting to retrieve memory with ID: {memory_id}")
                memory = await repo.get_memory(memory_id)
                if memory is None:
                    print(f"Failed to retrieve memory with ID: {memory_id}")
                    raise ValueError(f"Memory with ID {memory_id} not found")
                print(f"Successfully retrieved memory: {memory.title}")
            except Exception as e:
                print(f"Error retrieving memory {memory_id}: {str(e)}")
                raise

        # 5. 测试搜索功能
        print("Testing search functionality...")
        # Wait for Elasticsearch to process all operations
        await wait_for_consistency()
        search_results = await repo.search_memories(
            query="测试记忆",
            user_id="test_user_1",
            tags=["测试"]
        )
        print(f"Found {len(search_results)} memories matching search criteria")
        assert len(search_results) > 0

        # 6. 测试更新功能
        if memory_ids:
            print(f"Testing update functionality for memory {memory_ids[0]}...")
            memory = await repo.get_memory(memory_ids[0])
            if memory is None:
                raise ValueError(f"Memory with ID {memory_ids[0]} not found before update")
            memory.title = "更新后的标题"
            success = await repo.update_memory(memory_ids[0], memory)
            if not success:
                raise ValueError(f"Failed to update memory with ID {memory_ids[0]}")
            print("Update successful")
            
            # Wait for Elasticsearch to process the update
            await wait_for_consistency(2)
            
            # Verify the update
            updated_memory = await repo.get_memory(memory_ids[0])
            if updated_memory is None:
                raise ValueError(f"Memory with ID {memory_ids[0]} not found after update")
            if updated_memory.title != "更新后的标题":
                raise ValueError(f"Memory title was not updated correctly. Expected '更新后的标题', got '{updated_memory.title}'")

        # 7. 测试删除功能
        for memory_id in memory_ids:
            print(f"Testing delete functionality for memory {memory_id}...")
            success = await repo.delete_memory(memory_id)
            if not success:
                raise ValueError(f"Failed to delete memory with ID {memory_id}")
            print("Delete successful")
            
            # Wait for Elasticsearch to process the deletion
            await wait_for_consistency()
            
            # Verify the deletion
            deleted_memory = await repo.get_memory(memory_id)
            if deleted_memory is not None:
                raise ValueError(f"Memory with ID {memory_id} still exists after deletion")

    except ConnectionError as e:
        print(f"Failed to connect to Elasticsearch: {str(e)}")
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_memory_repository_smoke()) 