from typing import List, Optional
from app.db.elasticsearch.repository import ElasticsearchRepository
from app.db.elasticsearch.models import MemoryDocument, MEMORY_DOCUMENT_MAPPING

class MemoryRepository(ElasticsearchRepository[MemoryDocument]):
    def __init__(self):
        super().__init__(index_name="memories")
        self.mapping = MEMORY_DOCUMENT_MAPPING

    async def initialize(self):
        """Initialize the index with proper mapping."""
        await self.create_index(self.mapping)

    async def create_memory(self, memory: MemoryDocument) -> str:
        """Create a new memory document."""
        return await self.index_document(memory.to_dict())

    async def get_memory(self, id: str) -> Optional[MemoryDocument]:
        """Get a memory document by ID."""
        doc = await self.get_document(id)
        if doc:
            return MemoryDocument.from_dict(doc)
        return None

    async def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        size: int = 10
    ) -> List[MemoryDocument]:
        """Search memories with filters."""
        search_query = {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^2", "content"]
                        }
                    }
                ]
            }
        }

        if user_id:
            search_query["bool"]["must"].append({"term": {"user_id": user_id}})
        
        if tags:
            search_query["bool"]["must"].append({"terms": {"tags": tags}})

        results = await self.search(search_query, size=size)
        return [MemoryDocument.from_dict(doc) for doc in results]

    async def search_by_vector(
        self,
        vector: List[float],
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        size: int = 10
    ) -> List[MemoryDocument]:
        """Search memories using vector similarity."""
        search_query = {
            "script_score": {
                "query": {
                    "bool": {
                        "must": []
                    }
                },
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": vector}
                }
            }
        }

        if user_id:
            search_query["script_score"]["query"]["bool"]["must"].append(
                {"term": {"user_id": user_id}}
            )
        
        if tags:
            search_query["script_score"]["query"]["bool"]["must"].append(
                {"terms": {"tags": tags}}
            )

        results = await self.search(search_query, size=size)
        return [MemoryDocument.from_dict(doc) for doc in results]

    async def hybrid_search(
        self,
        query: str,
        vector: List[float],
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        size: int = 10,
        vector_weight: float = 0.7
    ) -> List[MemoryDocument]:
        """Perform hybrid search combining text and vector similarity."""
        search_query = {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^2", "content"]
                        }
                    }
                ],
                "should": [
                    {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                                "params": {"query_vector": vector}
                            }
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        }

        if user_id:
            search_query["bool"]["must"].append({"term": {"user_id": user_id}})
        
        if tags:
            search_query["bool"]["must"].append({"terms": {"tags": tags}})

        results = await self.search(search_query, size=size)
        return [MemoryDocument.from_dict(doc) for doc in results]

    async def update_memory(self, id: str, memory: MemoryDocument) -> bool:
        """Update a memory document."""
        return await self.update_document(id, memory.to_dict())

    async def delete_memory(self, id: str) -> bool:
        """Delete a memory document."""
        return await self.delete_document(id) 