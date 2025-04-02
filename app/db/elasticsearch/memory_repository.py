import logging
import os
from typing import List, Optional
from openai import OpenAI
from app.core.config import settings
from app.db.elasticsearch.repository import ElasticsearchRepository
from app.db.elasticsearch.models import MemoryDocument, MEMORY_DOCUMENT_MAPPING, MemoryType
from app.llm.embeddings import embed_text

class MemoryRepository(ElasticsearchRepository[MemoryDocument]):
    def __init__(self, index_name: str = "memories"):
        super().__init__(index_name)
        self.mapping = MEMORY_DOCUMENT_MAPPING

    async def initialize(self):
        """Initialize the index with proper mapping."""
        await self.create_index(self.mapping)

    async def create_memory(self, memory: MemoryDocument) -> str:
        """Create a new memory document."""
        content = memory.content
        embedding = embed_text(content)
        if embedding:
            memory.embedding = embedding
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
        size: int = 10,
        return_vector: bool = False
    ) -> List[MemoryDocument]:
        """Search memories using vector similarity with KNN."""
        query = {
            "knn": {
                "field": "embedding",
                "query_vector": vector,
                "k": size,
                "num_candidates": size * 10
            }
        }

        if user_id or tags:
            query["knn"]["filter"] = {
                "bool": {
                    "must": []
                }
            }
            if user_id:
                query["knn"]["filter"]["bool"]["must"].append(
                    {"term": {"user_id": user_id}}
                )
            if tags:
                query["knn"]["filter"]["bool"]["must"].append(
                    {"terms": {"tags": tags}}
                )

        # Exclude embedding field if return_vector is False
        if not return_vector:
            query["_source"] = {"excludes": ["embedding"]}

        results = await self.search(query, size=size)
        logging.info(f"Search results: {results}")
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

    async def list_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[MemoryDocument], int]:
        """
        List memories with pagination and sorting.
        
        Args:
            memory_type: Filter by memory type
            user_id: Filter by user ID
            page: Page number (1-based)
            page_size: Number of items per page
            sort_by: Field to sort by (default: created_at)
            sort_order: Sort order (asc or desc)
            
        Returns:
            Tuple of (list of memories, total count)
        """
        query = {"bool": {"must": []}}
        
        if memory_type:
            query["bool"]["must"].append({"term": {"memory_type": memory_type}})
            
        if user_id:
            query["bool"]["must"].append({"term": {"user_id": user_id}})
            
        # If no filters, match all documents
        if not query["bool"]["must"]:
            query = {"match_all": {}}
            
        # Calculate from/size for pagination
        from_ = (page - 1) * page_size
        
        # Build sort clause
        sort_clause = [{sort_by: {"order": sort_order}}]
        
        # Execute search
        results = await self.search(
            query=query,
            from_=from_,
            size=page_size,
            sort=sort_clause
        )
        
        # Get total count
        count = await self.count(query)
        
        return [MemoryDocument.from_dict(doc) for doc in results], count 