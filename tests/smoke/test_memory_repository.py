import asyncio
import pytest
from datetime import datetime
from app.db.elasticsearch.memory_repository import MemoryRepository
from app.db.elasticsearch.models import MemoryDocument, MemoryType

@pytest.mark.asyncio
async def test_memory_repository_smoke():
    # 1. 初始化 MemoryRepository
    repo = MemoryRepository()
    await repo.initialize()

    # 2. 创建测试数据
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
        memory_id = await repo.create_memory(memory)
        memory_ids.append(memory_id)
        print(f"Created memory with ID: {memory_id}")

    # 4. 测试获取单个记忆
    for memory_id in memory_ids:
        memory = await repo.get_memory(memory_id)
        assert memory is not None
        print(f"Retrieved memory: {memory.title}")

    # 5. 测试搜索功能
    search_results = await repo.search_memories(
        query="测试记忆",
        user_id="test_user_1",
        tags=["测试"]
    )
    assert len(search_results) > 0
    print(f"Found {len(search_results)} memories matching search criteria")

    # 6. 测试更新功能
    if memory_ids:
        memory = await repo.get_memory(memory_ids[0])
        memory.title = "更新后的标题"
        success = await repo.update_memory(memory_ids[0], memory)
        assert success
        print(f"Updated memory {memory_ids[0]}")

    # 7. 测试删除功能
    for memory_id in memory_ids:
        success = await repo.delete_memory(memory_id)
        assert success
        print(f"Deleted memory {memory_id}")

if __name__ == "__main__":
    asyncio.run(test_memory_repository_smoke()) 