from elasticsearch import AsyncElasticsearch
from app.core.config import settings

async def get_elasticsearch_client() -> AsyncElasticsearch:
    """
    Create and return an AsyncElasticsearch client instance.
    """
    if not settings.ELASTICSEARCH_HOSTS:
        raise ValueError("ELASTICSEARCH_URL is not set in environment variables")
    
    client = AsyncElasticsearch(
        hosts=[settings.ELASTICSEARCH_HOSTS],
        http_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD) if settings.ELASTICSEARCH_USERNAME and settings.ELASTICSEARCH_PASSWORD else None,
        # Add any additional configuration here
        # For example:
        # verify_certs=False,
        # ssl_show_warn=False,
    )
    return client

# Create a singleton instance
es_client = None

async def get_es() -> AsyncElasticsearch:
    """
    Get or create the Elasticsearch client singleton.
    """
    global es_client
    if es_client is None:
        es_client = await get_elasticsearch_client()
    return es_client 