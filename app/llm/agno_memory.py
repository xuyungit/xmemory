import os
from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.openai import OpenAIChat

class AgnoMemory:
    # 使用字典存储为每个用户创建的实例
    _instances = {}
    
    def __new__(cls, user_id: str):
        # 如果该用户的实例不存在，则创建新实例
        if user_id not in cls._instances:
            cls._instances[user_id] = super(AgnoMemory, cls).__new__(cls)
        # 返回该用户对应的实例
        return cls._instances[user_id]
    
    def __init__(self, user_id: str):
        # 防止重复初始化
        if not hasattr(self, 'initialized') or not self.initialized:
            self.user_id = user_id
            db_name = f"memory{user_id}.db"
            self.memory = Memory(
                db=SqliteMemoryDb(table_name="memory", db_file=db_name),
                model=OpenAIChat(
                    id=os.environ.get("LLM_MODEL", "gpt-4.1"),
                    api_key=os.environ.get("OPENAI_API_KEY_FOR_LLM"),
                    base_url=os.environ.get("OPENAI_API_BASE_FOR_LLM"),
                    ),
            )
            self.agent = Agent(
                model=OpenAIChat(
                    id=os.environ.get("LLM_MODEL", "gpt-4.1"),
                    api_key=os.environ.get("OPENAI_API_KEY_FOR_LLM"),
                    base_url=os.environ.get("OPENAI_API_BASE_FOR_LLM"),
                ),
                user_id=user_id,
                memory=self.memory,
                # Enable the Agent to dynamically create and manage user memories
                enable_agentic_memory=True,
                add_datetime_to_instructions=True,
                markdown=True,
            )
            self.initialized = True

    async def process_user_message(self, message: str):
        return await self.agent.arun(
            message,
        )
    
    def get_memories(self):
        """
        获取当前用户的记忆
        """
        return self.memory.get_user_memories(self.user_id)
    
    @classmethod
    def get_instance(cls, user_id: str):
        """
        获取指定用户ID的AgnoMemory实例
        如果不存在则创建新实例
        """
        return cls(user_id)
        
    @classmethod
    def clear_instance(cls, user_id: str):
        """
        清除指定用户ID的AgnoMemory实例
        """
        if user_id in cls._instances:
            del cls._instances[user_id]
            
    @classmethod
    def clear_all_instances(cls):
        """
        清除所有AgnoMemory实例
        """
        cls._instances.clear()
