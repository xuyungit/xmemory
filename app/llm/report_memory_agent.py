import asyncio
# from enum import Enum
import pytz
from datetime import datetime
import contextvars
# from pydantic import BaseModel
from agents import Agent, Runner, RunConfig
from agents import function_tool
from agents.models.openai_provider import OpenAIProvider
from app.core.config import settings
from app.db.elasticsearch.memory_repository import MemoryRepository
from app.db.elasticsearch.models import MemoryDocument, MemoryType
from app.storage.file_storage import FileStorage

instructions = """
你是一个日报生成器，负责生成流畅、清晰和调理清晰的日报。
你有两类的信息：
- 当天用户记录的各种记忆碎片信息
- 用户可能参与的项目的信息
同时，你还可以可以使用以下的工具来帮助你理解用户的记忆碎片的信息：
- search_memory: 从用户既往的记忆中搜索与当前记忆相关的记忆

你需要对以上三种信息进行梳理和分析，生成月报的内容，并使用下面的工具来保存月报：
- save_report: 保存月报，传入的参数是月报的正文，不需要有标题。

注意：你可以看到过去的记忆，过去的记忆只是为了协助你理解用户记录的信息。但是你的日报里不应该把过去的记忆当成是今天做的事写进去。
"""

user_id_context = contextvars.ContextVar('user_id', default=None)
request_date_context = contextvars.ContextVar('request_date', default=None)

async def generate_report_by(user_id: str, date_str: str, content: str) -> str:
    from dateutil import parser
    date_obj = parser.parse(date_str)
    date = date_obj.date()
    created_at = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%dT%H:%M:%S%z')
    updated_at = created_at
    doc = MemoryDocument(
        user_id=user_id,
        content=content,
        title=f"日报-{date}",
        tags=[],
        memory_type=MemoryType.DIARY,
        created_at=created_at,
        updated_at=updated_at
    )
    repo = MemoryRepository()
    memory_id = await repo.create_memory(doc)
    print(f"success to create memory, id is {memory_id}")
    return f"success to create memory, id is {memory_id}"

async def save_report(report_content: str) -> str:
    """
    保存生成的日报，传入的参数是报告的正文，不需要有标题。
    Args:
        report_content: 日报的正文
    Returns:
        str, 生成日报成功信息
    """
    user_id = user_id_context.get()
    request_date = request_date_context.get()
    print(f"save_report is called: {user_id}, date: {request_date}, report: {report_content}")
    return await generate_report_by(user_id, request_date, report_content)


async def search_memory(query: str) -> str:
    """
    从用户既往的记忆中搜索与当前记忆相关的记忆。当你需要了解用户偏好、过去做了什么，学到了什么，或者需要了解用户对某些事情的看法时，可以调用此工具。
    Args:
        query: 查询的文字
    Returns:
        str, 与查询文字相关的记忆列表
    """

    user_id = user_id_context.get()
    print(f"search_memory is called with user_id: {user_id}, query: {query}")
    repo = MemoryRepository()
    memory_docs = await repo.search_by_similarity(query, user_id, memory_type=MemoryType.RAW, size=15)
    memory_list = [f"@{memory.created_at}: {memory.content}" for memory in memory_docs  ]
    # make list of <memory>
    memory_list = [f"<memory>\n{memory}\n</memory>" for memory in memory_list]
    ret = "\n".join(memory_list)
    if not memory_list:
        ret = "No related memories found."
    print(ret)
    return ret

async def get_projects_summary() -> str:
    """
    获取当前用户所有项目名称以及项目的信息
    Args:
        None
    Returns:
        str, 项目名称以及项目的信息的列表
    """
    repo = MemoryRepository()
    user_id = user_id_context.get()
    projects = await repo.get_projects(user_id)
    projects = [f"- {p.summary}: {p.content}" for p in projects]
    return "\n".join(projects) if projects else "No projects found"

async def generate_report(user_id: str, request_date: str):
    repo = MemoryRepository()
    user_id_token = user_id_context.set(user_id)
    request_date_token = request_date_context.set(request_date)

    try:
        report_agent = Agent(
            name="Diary Report Agent",
            instructions=instructions,
            tools=[function_tool(save_report), function_tool(search_memory)],
        )
        my_model_provider = OpenAIProvider(
            api_key=settings.OPENAI_API_KEY_FOR_LLM,
            base_url=settings.OPENAI_API_BASE_FOR_LLM,
        )
        my_run_config = RunConfig(model_provider=my_model_provider)
        
        raw_memory = await repo.get_raw_memory_of_the_day(request_date, user_id)
        raw_memory_list = [f"@{memory.created_at}: {memory.content}" for memory in raw_memory]
        raw_memory_list = [f"<memory>\n{memory}\n</memory>" for memory in raw_memory_list]
        raw_memory_content = "\n".join(raw_memory_list)
        raw_memory_content = f"<memories_of_the_day>\n{raw_memory_content}\n</memories_of_the_day>\n"
        projects_summary = await get_projects_summary()
        projects_summary = f"<projects_summary>\n{projects_summary}\n</projects_summary>\n"
        input_content = f"{raw_memory_content}\n{projects_summary}\n"

        result = await Runner.run(report_agent, input_content, run_config=my_run_config)
        print(result.final_output)
        return result.final_output
    finally:
        user_id_context.reset(user_id_token)
        request_date_context.reset(request_date_token)


async def test_it():
    repo = MemoryRepository()

    ret = await repo.get_raw_memory_of_the_day("2025-04-07", user_id="xuyun")
    print(ret)
    
if __name__ == "__main__":
    # asyncio.run(generate_report_by("xuyun", "2025-04-07", "我今天吃了两个苹果。我爱吃苹果。我今天学习了python"))
    asyncio.run(generate_report("xuyun", "2025-04-07"))