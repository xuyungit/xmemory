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

# 创建一个上下文变量来存储 raw_memory
# 与全局变量不同，contextvars 为每个异步任务提供独立的上下文
# 这意味着不同用户的请求不会相互干扰
raw_memory_context = contextvars.ContextVar('raw_memory', default=None)

project_memory_agent_instructions_cn = """
你是一个专业的项目信息管理的助手，你将收到一段用户的原始文本信息，你需要分析这段信息，并使用工具对这个信息进行进一步的处理。
处理方法：
1. 你需要判断这段原始的信息是否属于一个项目，为此，你可能需要使用list_projects工具来查找相关的项目。
2. 如果原始信息属于一个既有的项目，你需要判断是否需要根据原始信息来更新这个项目的描述，还是更新项目的任务项，为此，你需要使用list_tasks工具来查找相关的任务。
3. 如果确实需要更新项目的描述，那么你需要使用update_project工具来更新项目的描述。项目的描述，主要描述的是项目是的目标、范围等，不包括任务项和和任务的状态。
   注意：当你更新项目的Description的时候，你需要结合既有的项目描述的内容以及当前你新了解到的项目的内容来更新。更新后的内容应同时包含旧的描述中的关键信息（除非新的信息删除或者修改了旧的信息），且包含新的信息，应该比较完整、流畅和清晰，并且不丢失重要信息。类似一个追加并改写的过程。
   在更新项目的时候，需要提供的两个参数是：
    1. Project ID: 项目ID，这个ID是项目的唯一标识
    2. Project Description: 项目描述，如果你认为需要更新项目的描述，可以使用这个参数，用一段清晰的话来描述这个项目，描述不超过300个字符。如果不需要更新参数，那么这个参数可以为空。
4. 你收到的原始信息中中可能会包含项目的任务（Tasks）相关的描述，你要根据这些描述，使用工具来管理该项目是的任务：
    - 你可以使用list_tasks工具来查找项目相关的任务。
    - 你可以使用create_task工具为项目来创建一个新的任务。
    - 你可以使用update_task工具为项目更新一个现有任务的状态。
5. 如果用户明确要求创建一个项目，那就创建一个新的项目。在创建项目的时候，应该使用project_create工具来创建一个新的项目。
   在更新项目的时候，应该使用project_update工具来更新这个项目的信息。
   在创建项目的时候，需要提供的三个参数是：
     1. Project Name: 项目名称(注意要使用原始信息中的语言，项目名称不要进行语言之间的翻译)
     2. Project Description: 项目描述，用一段清晰的话来描述这个项目，描述不超过300个字符


重要：
- 你要区分需要修改项目的描述还是项目的任务项，项目的描述主要指项目的目标、范围等，不包括任务项和和任务的状态。
- 如果涉及任务项的更新，请使用update_task工具来更新任务项的状态，或者创建新的任务。
- 如果涉及项目的描述的更新，请使用update_project工具来更新项目的描述。
- 除非用户明确要求创建一个新的项目，否则不要直接创建项目。有一些不太明确的项目归属的任务，例如一些待办项，todo list等，分类到“日常工作”项目中
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
    task_status: str

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
    return projects if projects else "No Projects Created"

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
    project.updated_at = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%dT%H:%M:%S%z')
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
    repo = MemoryRepository()
    docs = await repo.get_tasks(user_id=raw_memory_context.get().user_id, project_id=project_id)
    if not docs:
        print(f"project_id: {project_id} not found")
        return "No Tasks Found"
    tasks = [Task(task_id=doc._id, task_description=doc.content, task_status=doc.summary) for doc in docs]
    tasks = [f"- {task.task_id}: {task.task_description}, status: {task.task_status}" for task in tasks]
    ret = "\n".join(tasks)
    print(f"list_tasks result: {ret}")
    return ret

async def create_task(project_id: str, task_description: str) -> str:
    """
    A tool to create a new task. The status of the task is "To Do" by default.
    Args:
        project_id: str, the id of the project
        task_description: str, the description of the task
    Returns:
        str, the id of the created task
    """

    print(f"create_task is called, project_id: {project_id}, task_description: {task_description}")
    doc = MemoryDocument(
        user_id=raw_memory_context.get().user_id,
        title=task_description,
        content=task_description,
        memory_type=MemoryType.TASK,
        summary=TaskStatus.TO_DO,
        parent_id=project_id,
        tags=[],
        created_at=datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%dT%H:%M:%S%z'),
        updated_at=datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%dT%H:%M:%S%z'),
        processed=True
    )
    repo = MemoryRepository()
    task_id = await repo.create_memory(doc)
    if not task_id:
        print(f"Failed to create task: {task_description}")
        return "Failed to create task"
    print(f"Task created with ID: {task_id}")
    return "task created successfully, task_id: " + task_id

async def update_task(task_id: str, task_status: str) -> str:
    """
    此工具用于更新任务的状态。

    Args:
        task_id: str, 任务的唯一标识符
        task_status: 任务的新状态，可以是 "To Do"、"In Progress"、"Done" 或 "Deleted"

    Returns:
        bool, 如果任务更新成功则返回True，否则返回False

    """

    print(f"update_task is called, task_id: {task_id}, task_status: {task_status}")
    repo = MemoryRepository()
    task = await repo.get_memory(task_id)
    if not task:
        print(f"task_id: {task_id} not found")
        return "Task not found" 
    if task_status not in [status.value for status in TaskStatus]:
        print(f"Invalid task status: {task_status}")
        return (f"Invalid task status: {task_status}, valid values are: {[status.value for status in TaskStatus]}")
    task.summary = task_status
    task.updated_at = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%dT%H:%M:%S%z')
    await repo.update_memory(task_id, task)

    return "Task updated successfully"

def get_project_memory_agent(raw_memory: MemoryDocument) -> Agent:
    """
    获取项目记忆代理
    :return: Agent
    """
    raw_memory_context.set(raw_memory)
    
    instructions = f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n" + project_memory_agent_instructions_cn 
    return Agent(
        name="Project Memory Agent",
        instructions=instructions,
        # handoff_description="Special Agent for project memory management, such as creating, updating, and listing projects and tasks.",
        handoff_description="处理与具体项目、任务、计划或行动项相关的内容"
        "例子：为项目xmemory增加一个任务：实现项目的任务管理功能（）"
        "下面的例子应该使用project_memory_agent来处理："
        "为项目xmemory增加一个任务：实现项目的任务管理功能；"
        "我今天完成了一体机项目的需求分析文档编写"
        "完成了周报的编写",
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