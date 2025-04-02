from typing import Any, Dict, List, Optional, TypeVar, Generic
from elasticsearch import AsyncElasticsearch
from app.db.elasticsearch.client import get_es
import logging

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
        try:
            if not await es.indices.exists(index=self.index_name):
                print(f"Creating index {self.index_name} with mappings: {mappings}")
                await es.indices.create(index=self.index_name, mappings=mappings)
                print(f"Successfully created index {self.index_name}")
            else:
                print(f"Index {self.index_name} already exists")
        except Exception as e:
            print(f"Error creating index {self.index_name}: {str(e)}")
            raise

    async def index_document(self, document: Dict[str, Any], id: Optional[str] = None) -> str:
        """Index a document and return its ID."""
        es = await self.es
        try:
            print(f"Indexing document in {self.index_name}: {document}")
            result = await es.index(
                index=self.index_name,
                document=document,
                id=id,
                refresh=True  # This ensures the document is immediately available for search
            )
            print(f"Successfully indexed document with result: {result}")
            return result['_id']
        except Exception as e:
            print(f"Error indexing document: {str(e)}")
            raise

    async def get_document(self, id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document by ID."""
        es = await self.es
        try:
            print(f"Getting document with ID {id} from {self.index_name}")
            result = await es.get(index=self.index_name, id=id)
            print(f"Successfully retrieved document: {result}")
            return result['_source']
        except Exception as e:
            print(f"Error getting document {id}: {str(e)}")
            return None

    async def search(self, query: Dict[str, Any], size: int = 10) -> List[Dict[str, Any]]:
        """Search for documents using the specified query."""
        es = await self.es
        try:
            print(f"Searching in {self.index_name} with query: {query}")
            result = await es.search(index=self.index_name, query=query, size=size)
            print(f"Search results: {result}")
            return [hit['_source'] for hit in result['hits']['hits']]
        except Exception as e:
            print(f"Error searching documents: {str(e)}")
            raise

    async def update_document(self, id: str, document: Dict[str, Any]) -> bool:
        """Update a document by ID."""
        es = await self.es
        try:
            print(f"Updating document {id} in {self.index_name} with: {document}")
            result = await es.update(
                index=self.index_name,
                id=id,
                doc=document,
                refresh=True  # This ensures the update is immediately visible
            )
            print(f"Update result: {result}")
            return True
        except Exception as e:
            print(f"Error updating document {id}: {str(e)}")
            return False

    async def delete_document(self, id: str) -> bool:
        """Delete a document by ID."""
        es = await self.es
        try:
            print(f"Deleting document {id} from {self.index_name}")
            result = await es.delete(
                index=self.index_name,
                id=id,
                refresh=True  # This ensures the deletion is immediately visible
            )
            print(f"Delete result: {result}")
            return True
        except Exception as e:
            print(f"Error deleting document {id}: {str(e)}")
            return False 