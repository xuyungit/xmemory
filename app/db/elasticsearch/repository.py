from typing import Any, Dict, List, Optional, TypeVar, Generic
from elasticsearch import AsyncElasticsearch
from app.db.elasticsearch.client import get_es

T = TypeVar('T')

class ElasticsearchRepository(Generic[T]):
    def __init__(self, index_name: str):
        self.index_name = index_name
        self._es: Optional[AsyncElasticsearch] = None

    @property
    async def es(self) -> AsyncElasticsearch:
        if self._es is None:
            self._es = await get_es()
        return self._es

    async def create_index(self, mappings: Dict[str, Any]) -> None:
        """Create an index with the specified mappings if it doesn't exist."""
        es = await self.es
        if not await es.indices.exists(index=self.index_name):
            await es.indices.create(index=self.index_name, mappings=mappings)

    async def index_document(self, document: Dict[str, Any], id: Optional[str] = None) -> str:
        """Index a document and return its ID."""
        es = await self.es
        result = await es.index(index=self.index_name, document=document, id=id)
        return result['_id']

    async def get_document(self, id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document by ID."""
        es = await self.es
        try:
            result = await es.get(index=self.index_name, id=id)
            return result['_source']
        except:
            return None

    async def search(self, query: Dict[str, Any], size: int = 10) -> List[Dict[str, Any]]:
        """Search for documents using the specified query."""
        es = await self.es
        result = await es.search(index=self.index_name, query=query, size=size)
        return [hit['_source'] for hit in result['hits']['hits']]

    async def update_document(self, id: str, document: Dict[str, Any]) -> bool:
        """Update a document by ID."""
        es = await self.es
        try:
            await es.update(index=self.index_name, id=id, doc=document)
            return True
        except:
            return False

    async def delete_document(self, id: str) -> bool:
        """Delete a document by ID."""
        es = await self.es
        try:
            await es.delete(index=self.index_name, id=id)
            return True
        except:
            return False 