from elasticsearch import AsyncElasticsearch
from app.core.config import settings
import asyncio

async def get_elasticsearch_client() -> AsyncElasticsearch:
    """
    Create and return an AsyncElasticsearch client instance.
    """
    if not settings.ELASTICSEARCH_HOSTS:
        raise ValueError("ELASTICSEARCH_URL is not set in environment variables")
    
    client = AsyncElasticsearch(
        hosts=[settings.ELASTICSEARCH_HOSTS],
        basic_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD) if settings.ELASTICSEARCH_USERNAME and settings.ELASTICSEARCH_PASSWORD else None,
        # Add any additional configuration here
        # For example:
        # verify_certs=False,
        # ssl_show_warn=False,
    )
    return client

# Create a singleton instance
es_client = None
current_loop = None

async def get_es() -> AsyncElasticsearch:
    """
    Get or create the Elasticsearch client singleton.
    Recreates the client if the event loop has changed.
    """
    global es_client, current_loop
    current_loop_id = id(asyncio.get_running_loop())
    
    if es_client is None or current_loop != current_loop_id:
        # Close existing client if it exists
        if es_client is not None:
            await es_client.close()
        # Create new client
        es_client = await get_elasticsearch_client()
        current_loop = current_loop_id
    
    return es_client 