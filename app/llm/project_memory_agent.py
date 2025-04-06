import asyncio
from enum import Enum
import pytz
from datetime import datetime
import contextvars
from pydantic import BaseModel
from agents import Agent, Runner, RunConfig
from agents import function_tool
from agents.models.openai_provider import OpenAIProvider
from app.core.config import settings
from app.db.elasticsearch.memory_repository import MemoryRepository
from app.db.elasticsearch.models import MemoryDocument, MemoryType
from app.storage.file_storage import FileStorage

# 创建一个上下文变量来存储 raw_memory
# 与全局变量不同，contextvars 为每个异步任务提供独立的上下文
# 这意味着不同用户的请求不会相互干扰
raw_memory_context = contextvars.ContextVar('raw_memory', default=None)

instructions = """
 你是一个专业的项目信息管理的助手，你将收到段用户的原始文本信息，你需要判断这段原始的信息是否属于一个项目，为此，你可能需要使用list_projects工具来查找相关的项目。
 如果原始信息属于一个项目，你需要判断这个项目是否已经存在，如果存在，你需要更新这个项目的信息，否则你需要创建一个新的项目。
 在创建项目的时候，应该使用project_create工具来创建一个新的项目。
 在更新项目的时候，应该使用project_update工具来更新这个项目的信息。
 在创建项目的时候，需要提供的三个参数是：
 1. Project Name: 项目名称(注意要使用原始信息中的语言，项目名称不要进行语言之间的翻译)
 2. Project Description: 项目描述，用一段清晰的话来描述这个项目，描述不超过300个字符
 在更新项目的时候，需要提供的两个参数是：
 1. Project ID: 项目ID，这个ID是项目的唯一标识
 2. Project Description: 项目描述，如果你认为需要更新项目的描述，可以使用这个参数，用一段清晰的话来描述这个项目，描述不超过300个字符。如果不需要更新参数，那么这个参数可以为空。

用户的信息中可能会包含项目的任务（Tasaks），你可以使用project_list_tasks工具来查找相关的项目任务。
你可以使用project_create_task工具来创建一个新的项目任务。
你可以使用project_update_task工具来更新一个项目任务的状态。
"""

class Project(BaseModel):
    project_id: str
    project_name: str
    project_description: str

class TaskStatus(str, Enum):
    TO_DO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    DELETED = "Deleted"

class Task(BaseModel):
    task_id: str
    task_description: str
    task_status: TaskStatus

async def list_projects() -> list[Project]:
    """
    A tool to list all projects of current user.
    Args:
        None
    Returns:
        list, a list of projects
    """

    print("list_projects is called")

    raw_memory = raw_memory_context.get()
    user_id = raw_memory.user_id
    print(f"list_projects is called with user_id: {user_id}")
    repo = MemoryRepository()
    projects = await repo.get_projects(user_id)
    projects = [Project(project_id=project._id, project_name=project.title, project_description=project.content) for project in projects]
    return projects if projects else "No Projecte Created"

async def create_project(project_name: str, project_description: str) -> str:
    """
    A tool to create a new project.
    Args:
        project_name: str, the name of the project
        project_description: str, the description of the project
    Returns:
        str, the id of the created project
    """

    print(f"create_project is called, project_name: {project_name}, project_description: {project_description}")
    raw_memory = raw_memory_context.get()
    doc = MemoryDocument(
        user_id=raw_memory.user_id,
        title=project_name,
        content=project_description,
        memory_type=MemoryType.PROJECT,
        tags=raw_memory.tags,
        created_at=raw_memory.created_at,
        updated_at=raw_memory.updated_at,
        processed=True
    )
    if not doc.created_at:
        doc.created_at = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%dT%H:%M:%S%z')
    if not doc.updated_at:
        doc.updated_at = doc.created_at

    repo = MemoryRepository()
    memory_id = await repo.create_memory(doc)
    return memory_id

async def update_project(project_id: str, project_description: str) -> bool:
    """
    A tool to update a project.
    Args:
        project_id: str, the id of the project
        project_description: str, the description of the project
    Returns:
        bool, True if the project is updated successfully, False otherwise
    """

    print(f"update_project is called, project_id: {project_id}, project_description: {project_description}")
    repo = MemoryRepository()
    project = await repo.get_memory(project_id)
    if not project:
        print(f"project_id: {project_id} not found")
        return False
    if project_description:
        project.content = project_description
    project.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await repo.update_memory(project_id, project)

    return True

async def list_tasks(project_id: str) -> list[Task]:
    """
    A tool to list all tasks of a project.
    Args:
        project_id: str, the id of the project
    Returns:
        list, a list of tasks
    """

    print(f"list_tasks is called, project_id: {project_id}")
    task1 = Task(task_id="1", task_description="Task 1", task_status="To Do")
    task2 = Task(task_id="2", task_description="Task 2", task_status="In Progress")
    return [task1, task2]

async def create_task(project_id: str, task_description: str) -> str:
    """
    A tool to create a new task.
    Args:
        project_id: str, the id of the project
        task_description: str, the description of the task
    Returns:
        str, the id of the created task
    """

    print(f"create_task is called, project_id: {project_id}, task_description: {task_description}")

    return "1234567890"

async def update_task(task_id: str, task_status: str) -> bool:
    """
    A tool to update a task.
    Args:
        task_id: str, the id of the task
        task_status: str, the status of the task
    Returns:
        bool, True if the task is updated successfully, False otherwise
    """

    print(f"update_task is called, task_id: {task_id}, task_status: {task_status}")

    return True

def get_project_memory_agent(raw_memory: MemoryDocument) -> Agent:
    """
    获取项目记忆代理
    :return: Agent
    """
    raw_memory_context.set(raw_memory)
    return Agent(
        name="Project Memory Agent",
        instructions=instructions,
        handoff_description="Special Agent for project memory management, such as creating, updating, and listing projects and tasks.",
        tools=[
            function_tool(list_projects),
            function_tool(create_project),
            function_tool(update_project),
            function_tool(list_tasks),
            function_tool(create_task),
            function_tool(update_task)
        ],
    )

def clear_context():
    """
    清除上下文变量
    :return: None
    """
    raw_memory_context.set(None)
    print("Context cleared")

async def update_project_memory(raw_memory: MemoryDocument):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    global instructions
    instructions = f"当前时间：{now}\n" + instructions

    # 设置上下文变量
    # 在异步多用户场景中，每个用户的请求都有自己的上下文
    # 因此，这里设置的 user_id 只会影响当前处理的请求
    token = raw_memory_context.set(raw_memory)
    
    try:
        memory_agent = Agent(
            name="Project Memory Agent",
            instructions=instructions,
            tools=[
                function_tool(list_projects),
                function_tool(create_project),
                function_tool(update_project),
                function_tool(list_tasks),
                function_tool(create_task),
                function_tool(update_task)
            ],
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
        raw_memory_context.reset(token)

if __name__ == "__main__":
    raw_memory = MemoryDocument(
        user_id="xuyun",
        content="我正在开发一个项目，项目名称是xmemory，项目主要解决的问题是：用户可以方便地管理自己的项目信息。",
        tags=[],
        memory_type=MemoryType.RAW
    )
    asyncio.run(update_project_memory(raw_memory))