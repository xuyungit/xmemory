import asyncio
from datetime import datetime
import contextvars

from agents import Agent, Runner, RunConfig
from agents import function_tool
from agents.models.openai_provider import OpenAIProvider
from app.core.config import settings
from app.db.elasticsearch.memory_repository import MemoryRepository
from app.db.elasticsearch.models import MemoryDocument, MemoryType
from app.storage.file_storage import FileStorage

raw_memory_context = contextvars.ContextVar('raw_memory', default=None)

insight_agent_instructions = """
 你是一个专业的用户记忆管理的助手，你将收到用户输入的一条原始的记忆，你要提炼出关键信息，形成更清晰和有条理的记忆，必要的时候可以使用下面记忆管理工具来查找旧记忆、更新记忆、删除记忆和增加记忆。
 注意：
 1. 使用用户的原始语言来记录记忆，尽量不要翻译。
 2. 如果用户的原始记忆包含多个不相关的记忆，请将它们分开记录。
 3. 事实性的记忆和偏好性的记忆分开记录。
 4. 在决定如何处理记忆之前，你应该先提取原始记忆中的关键信息，然后根据这些关键信息来使用search_memory工具来查找相关的旧记忆。
 5. 根据旧记忆来决定如何处理新的记忆。
 6. 如果旧记忆中没有相关的记忆，请使用create_memory工具来创建新的记忆。

 例子1：
 用户输入：我今天吃了两个苹果。我爱吃苹果。我今天学习了python
 你的输出：
1. call search_memory("我今天吃了两个苹果") to find related memories
2. call search_memory("我爱吃苹果") to find related memories
3. call search_memory("我今天学习了python") to find related memories
4. call create_memory("我今天吃了两个苹果") to create a new memory
5. call create_memory("我爱吃苹果") to create a new memory
6. call create_memory("我今天学习了python") to create a new memory
"""

async def search_memory(query: str):
    """
    A tool to search for memories.
    Proactively call this tool when you:
    1. search for old memories.
    2. want to know what user did and what user learned.
    """

    # 从上下文变量获取 user_id
    # 在异步多用户场景中，每个用户的请求都有自己的上下文
    # 因此，这里获取的 user_id 总是与当前处理的请求对应的用户 ID
    raw_memory = raw_memory_context.get()
    print(f"search_memory is called with raw_memory: {raw_memory.user_id}, query: {query}")
    repo = MemoryRepository()
    memory_docs = await repo.search_by_similarity(query, raw_memory.user_id, raw_memory.tags, size=10)
    memory_list = [f"@{memory.created_at}: {memory.content}" for memory in memory_docs if memory.memory_type == MemoryType.INSIGHT]
    # make list of <memory>
    memory_list = [f"<memory>\n{memory}\n</memory>" for memory in memory_list]
    ret = "\n".join(memory_list)
    if not memory_list:
        ret = "No related memories found."
    print(ret)
    return ret

async def create_memory(memory_to_record: str):
    """
    A tool to create a new memory.
    Proactively call this tool when you:
    1. Identify a new USER preference.
    2. Receive an explicit USER request to remember something or otherwise alter your behavior.
    3. Are working and want to record important context.
    4. Got new information that might be useful to remember.
    5. Record what user did and what user learned.
    IMPORTANT:
    1. don't record date and time in parameter of this tool
    """

    # 从上下文变量获取 user_id
    # 在异步多用户场景中，每个用户的请求都有自己的上下文
    # 因此，这里获取的 user_id 总是与当前处理的请求对应的用户 ID
    raw_memory = raw_memory_context.get()
    print(f"create_memory is called with raw_memory: {raw_memory.user_id}, memory: {memory_to_record}")

    new_memory = MemoryDocument(
        user_id=raw_memory.user_id,
        content=memory_to_record,
        memory_type=MemoryType.INSIGHT,
        tags=raw_memory.tags,
        created_at=raw_memory.created_at,
        updated_at=raw_memory.updated_at,
        processed=True
    )
    repo = MemoryRepository()
    memory_id = await repo.create_memory(new_memory)

    # Save to local file storage
    memory_data = new_memory.to_dict()
    memory_data["_id"] = memory_id  # Add the ID to the data
    file_storage = FileStorage()

    file_storage.save_memory(memory_id, memory_data)

    return f"success to create memory, id is {memory_id}"


async def update_insight_memory(raw_memory: MemoryDocument):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    global instructions
    instructions = f"当前时间：{now}\n" + instructions

    # 设置上下文变量
    # 在异步多用户场景中，每个用户的请求都有自己的上下文
    # 因此，这里设置的 user_id 只会影响当前处理的请求
    token = raw_memory_context.set(raw_memory)
    
    try:
        memory_agent = Agent(
            name="Memory Agent",
            instructions=instructions,
            tools=[function_tool(create_memory), function_tool(search_memory)],
        )
        my_model_provider = OpenAIProvider(
            api_key=settings.OPENAI_API_KEY_FOR_LLM,
            base_url=settings.OPENAI_API_BASE_FOR_LLM,
        )
        my_run_config = RunConfig(model_provider=my_model_provider)
        
        result = await Runner.run(memory_agent, raw_memory.content, run_config=my_run_config)
        print(result.final_output)
        return result.final_output
    finally:
        # 重置上下文变量
        # 确保在函数完成后清理上下文，防止内存泄漏
        # 在异步多用户场景中，这确保了一个用户的上下文不会影响其他用户
        raw_memory_context.reset(token)

def get_insight_memory_agent(raw_memory: MemoryDocument) -> Agent:
    """
    获取用户记忆代理
    :return: Agent
    """
    raw_memory_context.set(raw_memory)

    return Agent(
        name="Insight Memory Agent",
        instructions=insight_agent_instructions,
        handoff_description="Special Agent for process general purpose memory, such as insights, preference, profiles and facts.",
        tools=[
            function_tool(search_memory),
            function_tool(create_memory)
        ],
    )

def clear_context():
    """
    清除上下文变量
    :return: None
    """
    raw_memory_context.set(None)
    print("Context cleared")
