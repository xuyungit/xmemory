import asyncio
from datetime import datetime
# import contextvars

from agents import Agent, Runner, RunConfig
from agents.models.openai_provider import OpenAIProvider
from app.core.config import settings
from app.db.elasticsearch.models import MemoryDocument, MemoryType
from app.llm.project_memory_agent import get_project_memory_agent, clear_context as clear_project_context
from app.llm.insight_memory_agent import get_insight_memory_agent, clear_context as clear_insight_context

async def process_raw_memory(raw_memory: MemoryDocument):
    print(f"Processing raw memory for user: {raw_memory.user_id}, content: {raw_memory.content}")
    insight_memory_agent = get_insight_memory_agent(raw_memory=raw_memory)
    project_memory_agent = get_project_memory_agent(raw_memory=raw_memory)
    triage_agent = Agent(
        name="Triage Agent",
        instructions="You are a triage agent, you will decide which agent to use. Try to use the most appropriate agent to handle the memory. Choose just one agent to handle the memory.",
        handoff_description="You are a triage agent, you will decide which agent to use. Try to use the most appropriate agent to handle the memory.",
        handoffs=[project_memory_agent, insight_memory_agent],
    )
    # insight_memory_agent.handoffs = [triage_agent]
    # project_memory_agent.handoffs = [triage_agent]

    my_model_provider = OpenAIProvider(
        api_key=settings.OPENAI_API_KEY_FOR_LLM,
        base_url=settings.OPENAI_API_BASE_FOR_LLM,
    )
    my_run_config = RunConfig(model_provider=my_model_provider)

    try:
        result = await Runner.run(triage_agent, raw_memory.content, run_config=my_run_config)
        print(result.final_output)
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
