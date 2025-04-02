from typing import List
from openai import OpenAI
from app.core.config import settings

def embed_text(text: str) -> List[float]:
    if not text:
        return None
    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_API_BASE
    )    
    response = client.embeddings.create(
        input=text,
        model=settings.EMBEDDING_MODEL,
        dimensions=settings.EMBEDDING_DIMENSION,
        encoding_format="float"
    )
    return response.data[0].embedding 