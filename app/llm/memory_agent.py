import asyncio
from datetime import datetime
from openai import AsyncOpenAI
from pydantic import BaseModel
# from rich.pretty import pprint
from agents import Agent, Runner, RunConfig, Model, ModelProvider
from agents.models.openai_provider import OpenAIProvider
from app.core.config import settings
from app.db.elasticsearch.models import MemoryDocument, MemoryType
from app.llm.project_memory_agent import get_project_memory_agent, clear_context as clear_project_context
from app.llm.insight_memory_agent import get_insight_memory_agent, clear_context as clear_insight_context
from app.db.elasticsearch.memory_repository import MemoryRepository
from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled
# from app.storage.file_storage import FileStorage
# from app.llm.agno_memory import AgnoMemory

triage_agent_instructions = """
You are a triage agent to handle a user input message, which is a raw memory from recorded by user, you will decide which agent to use to handle the memory.
You should analyze the user input message and decide which agent(s) to use.

Here are the agents you can choose from:
- Insight Memory Agent
- Project Memory Agent

If the memory contains both project and insight information, you should use split the original memory into two parts and handle them with different agents.
You should use only one agent to handle the memory one time and call another agent to handle the other part.
"""

triage_agent_instructions_cn = """
你是一个专业的记忆分类代理，负责分析和分配用户记录的原始记忆内容。你的核心任务是确定每条记忆应由哪个专门代理处理，并且调用function call切换到相应的代理。

可用的专门代理包括：
1. 洞察记忆代理Insight Memory Agent - 处理包含个人的喜好、见解、想法、反思、生活或领悟的内容
2. 项目记忆代理Project Memory Agent - 处理与具体项目、任务、计划或行动项相关的内容

你会获知用户当前的项目信息，你可以使用这些信息来帮助你判断信息是否属于某个项目。

分类指南：
- 仔细分析记忆的主要内容和目的
- 明确识别记忆是属于洞察类型、项目类型，还是两者兼有
- 对于单一类型的记忆，直接分配给相应的专门代理
- 对于混合类型的记忆：
  * 将记忆清晰地分割成不同部分
  * 首先处理一个部分（选择最主要或最重要的部分）
  * 然后将另一部分分配给另一个适当的代理

请确保你的分类决策准确、高效，且能最大化每个专门代理的处理效果。
"""

triage_agent_instructions = '''
Role and Objective

You are a Memory-Routing Agent. Your sole objective is to analyse each incoming raw memory provided by the user and decide which specialised downstream agent must handle it. After deciding, you must trigger the correct agent by issuing the required function call.

# Instructions

1.	Analyse Content
Examine the main topic, intent, and purpose of every memory snippet you receive.
2.	Classify Precisely
Decide whether the memory is:
    1.	Insight Memory—personal preferences, reflections, ideas, feelings, life events, or lessons learned.
	2.	Project Memory—concrete information about a project, task, plan, milestone, or action item.
	3.	Mixed Memory—contains clearly separable Insight and Project elements.
3.	Route the Memory
	- Single-type memory: Immediately route to the matching specialised agent.
	- Mixed memory:
		1.	Split the snippet into distinct Insight and Project segments.
		2.	Handle the segment that is most important first.
		3.	Issue an additional routing call for the remaining segment.

4.	Invoke the Agent
Use the system-defined function_call mechanism, supplying the target agent’s name and the relevant memory segment as arguments.

# Sub-categories for more detailed instructions
	- Evaluating project relevance – Compare entities, timelines, or keywords inside the memory against the current project list provided by the user.
	- Ambiguity resolution – If a memory could plausibly fit both categories, prefer the category that best matches the user’s explicit wording or context clues.
	- Efficiency requirements – Minimise redundant calls; one memory fragment must never be sent to the same agent twice.

# Reasoning Steps
1.	Read the memory in full.
2.	Identify key nouns and verbs that reveal intent (e.g., plan, idea, task, reflection).
3.	Map those cues to the Insight or Project definitions.
4.	Decide whether splitting is necessary.
5.	Formulate the routing decision.
6.	Construct the function_call payload.
7.	Output strictly in the required format 
8.  If more than one memory fragment is identified, call the Agent for each fragment.

If route is Split, return an array of two routing objects—one per segment—in the order processed.

Examples

Example 1

Input memory

"我突然想到一个点子，想把我们正在做的‘铁路边缘云’项目的日志收集机制改成事件驱动，同时也想记录下我对团队协作的一些反思：加强沟通。"

Expected output
The following function_call should be returned:
{
    "tool": "project_memory_agent",
    "arguments": {
        "input": "改进“铁路边缘云”项目日志收集机制为事件驱动的想法"
    }
}

{
    "tool": "insight_memory_agent",
    "arguments": {
        "input": "对团队协作的个人反思：加强沟通"
    }
}



Current project list is provided separately by the system and may be referenced during classification.

Final instructions and prompt to think step by step

When you receive a memory snippet, think step by step using the Reasoning Steps above before producing your JSON‑formatted output.
'''

class Project(BaseModel):
    project_id: str
    project_name: str
    project_description: str

async def get_project_information(user_id: str) -> str:
    repo = MemoryRepository()
    projects = await repo.get_projects(user_id)
    projects = [Project(project_id=project._id, project_name=project.title, project_description=project.content) for project in projects]
    
    projects = [f"<project>\n<project_name>{project.project_name}</project_name>\n<project_description>{project.project_description}</project_description>\n</project>" for project in projects]
    return "```<projects>\n" + "\n".join(projects) + "\n</projects>```" if projects else "No Projects Created"
class CustomModelProvider(ModelProvider):
    def get_model(self, model_name: str | None) -> Model:
        client = AsyncOpenAI(base_url=settings.OPENAI_API_BASE_FOR_LLM, api_key=settings.OPENAI_API_KEY_FOR_LLM)
        return OpenAIChatCompletionsModel(model=model_name or settings.LLM_MODEL, openai_client=client)
    
async def process_raw_memory(raw_memory: MemoryDocument):
    print(f"Processing raw memory for user: {raw_memory.user_id}, content: {raw_memory.content}")
        
    insight_memory_agent = get_insight_memory_agent(raw_memory=raw_memory)
    project_memory_agent = get_project_memory_agent(raw_memory=raw_memory)
    triage_agent = Agent(
        name="Triage Agent",
        instructions=triage_agent_instructions + "\n" + await get_project_information(raw_memory.user_id),
        tools=[insight_memory_agent, project_memory_agent],
        # handoff_description="You are a triage agent, you will decide which agent to use. Try to use the most appropriate agent to handle the memory.",
        # handoffs=[project_memory_agent, insight_memory_agent],
    )

    if not settings.OPENAI_RESPONSE_API:
        set_tracing_disabled(disabled=True)
        my_model_provider = CustomModelProvider()

    else:
        my_model_provider = OpenAIProvider(
            api_key=settings.OPENAI_API_KEY_FOR_LLM,
            base_url=settings.OPENAI_API_BASE_FOR_LLM,
        )
    my_run_config = RunConfig(model=settings.LLM_MODEL, model_provider=my_model_provider)

    try:
        result = await Runner.run(triage_agent, raw_memory.content, run_config=my_run_config)
        print(result.final_output)
        # agno_agent = AgnoMemory.get_instance(raw_memory.user_id)
        # result_agno = await agno_agent.process_user_message(raw_memory.content)
        # pprint(f"AgnoMemory response: {result_agno.to_dict()}")
        # pprint(f"memories: {agno_agent.get_memories()}")
        return result.final_output
    finally:
        # 清除上下文变量
        # 在异步多用户场景中，这确保了一个用户的上下文不会影响其他用户
        clear_insight_context()
        clear_project_context()

if __name__ == "__main__":
    raw_memory = MemoryDocument(
        user_id="xuyun",
        content="今天天气极其恶劣。",
        memory_type=MemoryType.RAW,
        tags=["weather"],
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        processed=False
    )
    result = asyncio.run(process_raw_memory(raw_memory))
    print(result)
