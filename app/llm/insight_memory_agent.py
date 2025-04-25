import asyncio
from typing import List
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
 9. 如果记忆没有带主语，请使用“用户”作为主语，使得记忆的含义更清晰。如果主语是“我”，也请将其替换为“用户”，使用第三人称。
 
注意：
记忆是有时间属性的，比如我说今天心情不好，指的是记录的当天。如果再收到另外一条记忆：“今天心情很好”，但是发生的时间不同的时候，这时候就应该再创建一条新的记忆。
如果再同一个时间段收到更新，那么就应该更新之前的记忆。
你再决定更新或者新建整理后的记忆的时候，要考虑之前的记忆的时间。

"""
insight_agent_instructions = '''
## Role and Objective

You are User-Memory Management Assistant. Your goal is to transform each raw user-supplied memory into concise, well-structured memories, decide whether to create, update, or ignore entries in the long-term store, and invoke the correct memory-management tool for that action.

---

## Instructions

1.	Preserve Language
1.1 Record each memory in the same language the user used. Do not translate or paraphrase beyond necessary clarifications.

2.	Clarify the Subject
2.1 If the memory lacks an explicit subject, prepend "用户…" (the user) as the subject.
2.2 If the subject is "我/I", replace it with "用户". Use third-person throughout the stored memory.

3.	Separate Unrelated Memories
3.1 If a single input contains multiple unrelated memories, split them into independent entries and handle each one individually.

4.	Classify by Nature
4.1 Label each memory as either Factual (objective facts, dates, places, numbers, achievements, etc.) or Preferential (likes, dislikes, opinions, feelings, habits).
4.2 Store factual and preferential memories in separate tool calls even when extracted from the same input.

5.	Extraction & Query Process
5.1 Extract the key information from the raw input (entities, actions, dates, sentiments).
5.2 Immediately call search_memory with that key information to find potentially related existing memories.

6.	Decision Logic
6.1 No matching memory found → use create_memory to store the new memory.
6.2 Matching memory found, content conflicts → use update_insight_memory to overwrite or merge, keeping the newer information.
6.3 Matching memory found, content identical → do nothing.

7.	Handle Time Sensitively
7.1 Treat each memory as time-stamped with the moment of user input.
7.2 If the same topic recurs but pertains to a different time period (e.g., “今天心情不好” vs. a later “今天心情很好”), treat them as distinct and create a new memory.
7.3 If an update clearly refers to the same time period, update the prior entry instead of creating a new one.

8.	Tool Invocation Format
8.1 After reasoning, output exactly one tool call each time or the string no_action to end the process.

---

Sub-categories for more detailed instructions

A. Language & Subject Handling
- Make memories concise and clear, make it easy to search in the future.
- Never switch language unless the user does.

B. Memory Categorization
- Factual examples: 出生年份、工作职位、孩子出生日期、今日心情。
- Preferential examples: 喜欢的音乐、常去的健身房。

C. Conflict Resolution
- "冲突" = any difference in fact or preference value (e.g., old: "喜欢咖啡", new: "不喜欢咖啡"), update memory to use the newer information.
- Merge only when both memories can coexist logically (e.g., different time periods).

---

Reasoning Steps (internal, not output)
1. Parse input → extract key entities, actions, dates.
2. Query memory store with search_memory.
3. Compare results → determine consistency, conflict, or absence.
4. Choose action: create / update / no_action.
5. Compose tool call.
6. Check the tool call Output
7. Loopback to step 2 if needed or end the process.

---

Output Format (external)
One of the following:
- A single tool-call JSON block
    - The literal string no_action.
	- Do not output the extracted key information or any extra commentary.

---

Examples

Example 1

Raw input:

我今天迟到了，心情不好，喝的咖啡太苦了。

1.	Extracted keys → "心情", “咖啡”.
2.	search_memory returns no related entries.
3.	Decision → create two new preferential memories.
4.	Output:

{
  "tool": "create_memory",
  "arguments": {
    "memories": [
      "用户今天心情不好。"
      "用户今天迟到了。"
    ],
    "type": "Factual"
  }
}

{
  "tool": "create_memory",
  "arguments": {
    "memories": [
      "用户不喜欢喝太苦的咖啡。"
    ],
    "type": "Preferential"
  }
}

---

Final instructions and prompt to think step by step

When processing each user input, pause and silently run the Reasoning Steps above. Only after that internal deliberation should you emit either a tool call or no_action. Think step by step before you answer.
'''

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

async def create_memory(memory_to_record: List[str], memory_category: str) -> str:
    """
    A tool to create a new memory.
    Attention:
    - Do not record date and time in memory_to_record parameter of this tool
    Args:
        memory_to_record (List[str]): memory or memories to record
        memory_category (str): could be any of "Factual", "Preferential"
    Returns:
        str: success message
    """
    # """
    # A tool to create a new memory.
    # Proactively call this tool when you:
    # 1. Identify a new USER preference.
    # 2. Receive an explicit USER request to remember something or otherwise alter your behavior.
    # 3. Are working and want to record important context.
    # 4. Got new information that might be useful to remember.
    # 5. Record what user did and what user learned.
    # IMPORTANT:
    # 1. don't record date and time in parameter of this tool
    # """

    # 从上下文变量获取 user_id
    # 在异步多用户场景中，每个用户的请求都有自己的上下文
    # 因此，这里获取的 user_id 总是与当前处理的请求对应的用户 ID
    raw_memory = raw_memory_context.get()
    print(f"create_memory is called with raw_memory: {raw_memory.user_id}, memory: {memory_to_record}")

    repo = MemoryRepository()
    memory_ids = []
    for memory in memory_to_record:
        new_memory = MemoryDocument(
            user_id=raw_memory.user_id,
            title=memory_category,
            content=memory,
            memory_type=MemoryType.INSIGHT,
            tags=raw_memory.tags,
            created_at=raw_memory.created_at,
            updated_at=raw_memory.updated_at,
            processed=True
        )
        memory_id = await repo.create_memory(new_memory)
        # Save to local file storage
        memory_data = new_memory.to_dict()
        memory_data["_id"] = memory_id  # Add the ID to the data
        file_storage = FileStorage()

        file_storage.save_memory(memory_id, memory_data)
        memory_ids.append(memory_id)
    print(f"Memory created with IDs: {', '.join(memory_ids)}")
    return f"success to create memory, ids are {', '.join(memory_ids)}"

async def update_memory(memory_id: str, new_content: str) -> str:
    # """
    # 更新insight记忆的工具
    # 当你发现用户的偏好和之前的记忆发生变化时，或者用户请求更新某些内容时，主动调用此工具。
    # Args:
    #     memory_id (str): 需要更新的记忆的ID
    #     new_content (str): 旧的记忆将会被更新为新的内容
    # Returns:
    #     str: 更新的结果
    # 注意：
    # 不要把时间信息记录到new_content中，我们有时间戳来记录记忆的创建和更新时间。
    # """

    """
    A tool to update an existing memory.
    Args:
        memory_id (str): The ID of the memory to update
        new_content (str): The new content to update the memory with
    Returns:
        str: Success message
    """
    repo = MemoryRepository()
    memory = await repo.get_memory(memory_id)
    
    if not memory:
        return f"Memory with ID {memory_id} not found."

    memory.content = new_content
    await repo.update_memory(memory)

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

    agent = Agent(
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
    tool = agent.as_tool(
        tool_name="insight_memory_agent",
        tool_description="A tool to handle insight memory.",
    )
    return tool
    # return agent

def clear_context():
    """
    清除上下文变量
    :return: None
    """
    raw_memory_context.set(None)
    print("Context cleared")
