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
 7. 如果旧记忆中有相关的记忆，并且和现在的信息不一致，请使用update_insight_memory工具来更新旧的记忆。
 8. 如果旧记忆中有相关的记忆，并且和现在的信息一致，请不做任何处理。
注意：
记忆是有时间属性的，比如我说今天心情不好，指的是记录的当天。如果再收到另外一条记忆：“今天心情很好”，但是发生的时间不同的时候，这时候就应该再创建一条新的记忆。
如果再同一个时间段收到更新，那么就应该更新之前的记忆。
你再决定更新或者新建整理后的记忆的时候，要考虑之前的记忆的时间。

 例子1：
 用户输入：我今天吃了两个苹果。我爱吃苹果。我今天学习了python
 你的输出：
1. call search_memory("我今天吃了两个苹果") to find related memories
2. call search_memory("我爱吃苹果") to find related memories
3. call search_memory("我今天学习了python") to find related memories
4. call create_memory("我今天吃了两个苹果") to create a new memory
5. call create_memory("我爱吃苹果") to create a new memory
6. call create_memory("我今天学习了python") to create a new memory

例子2：
假如之前的记忆说明用户对跑步不感兴趣。
现在收到输入：我开始喜欢跑步了。
你的输出：
1. call search_memory("跑步") to find related memories
2. call update_insight_memory("id_of_old_memory", "我开始喜欢跑步了") to update the memory
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
    memory_docs = await repo.search_by_similarity(query, raw_memory.user_id, raw_memory.tags, size=10, memory_type=MemoryType.INSIGHT)
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

async def update_memory(memory_id: str, new_content: str) -> str:
    """
    更新insight记忆的工具
    当你发现用户的偏好和之前的记忆发生变化时，或者用户请求更新某些内容时，主动调用此工具。
    Args:
        memory_id (str): 需要更新的记忆的ID
        new_content (str): 旧的记忆将会被更新为新的内容
    Returns:
        str: 更新的结果
    注意：
    不要把时间信息记录到new_content中，我们有时间戳来记录记忆的创建和更新时间。
    """

    repo = MemoryRepository()
    memory = await repo.get_memory(memory_id)
    
    if not memory:
        return f"Memory with ID {memory_id} not found."

    memory.content = new_content
    repo.update_memory(memory)

    return f"Memory with ID {memory_id} updated successfully."

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
            tools=[function_tool(create_memory), function_tool(search_memory), function_tool(update_memory)],
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
    instructions = f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n" + insight_agent_instructions 

    return Agent(
        name="Insight Memory Agent",
        instructions=instructions,
        # handoff_description="Special Agent for process general purpose memory, such as insights, preference, profiles and facts.",
        handoff_description="洞察个人记忆的Agent，处理包含个人的喜好、见解、想法、反思、生活或领悟的内容，把原始的记忆处理成更有价值的洞察。"
        "下面的例子应该使用insight_memory_agent来处理："
        "- 刚刚完成了一次力量训练（个人生活记录）；"
        "- 我不喜欢吃海鲜（个人喜好）；"
        "- 我今天学习了python（个人学习记录）；"
        "- 我今天吃了两个苹果（个人饮食记录）；"
        "- 我发现关税政策对经济的影响很大（个人见解）；"
        "注意重要：本代理不处理关于计划、任务、行动项的记忆，应该使用项目记忆代理来处理。",
        tools=[
            function_tool(search_memory),
            function_tool(create_memory),
            function_tool(update_memory)
        ],
    )

def clear_context():
    """
    清除上下文变量
    :return: None
    """
    raw_memory_context.set(None)
    print("Context cleared")
