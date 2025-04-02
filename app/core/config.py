from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "XMemory"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    DATABASE_URL: Optional[str] = None

    # Elasticsearch settings
    ELASTICSEARCH_HOSTS: Optional[str] = None
    ELASTICSEARCH_USERNAME: Optional[str] = None
    ELASTICSEARCH_PASSWORD: Optional[str] = None
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Embedding settings
    EMBEDDING_DIMENSION: int = 1536  # Default to OpenAI's text-embedding-ada-002 dimension

    # Debug settings
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings() 