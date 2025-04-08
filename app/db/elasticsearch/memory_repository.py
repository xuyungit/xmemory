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
        logging.info(f"Initializing index with mapping: {self.mapping}")
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

    async def search_by_similarity(
        self,
        query: str,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        size: int = 10
    ) -> List[MemoryDocument]:
        vector = embed_text(query)
        if not vector:
            raise ValueError("Failed to generate embedding for query")
        return await self.search_by_vector(vector, user_id, tags, memory_type, size)

    async def search_by_vector(
        self,
        vector: List[float],
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
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

        if user_id or tags or memory_type:
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
            if memory_type:
                query["knn"]["filter"]["bool"]["must"].append(
                    {"term": {"memory_type": memory_type.value}}
                )

        # Exclude embedding field if return_vector is False
        if not return_vector:
            query["_source"] = {"excludes": ["embedding"]}

        results = await self.search(query, size=size)
        # logging.info(f"Search results: {results}")
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

    async def get_projects(self, user_id: Optional[str] = None) -> List[MemoryDocument]:
        """Get all projects."""
        docs, count = await self.list_memories(
            memory_type=MemoryType.PROJECT,
            user_id=user_id,
            page=1,
            page_size=1000
        )
        if len(docs) != count:
            docs, _ = await self.list_memories(
                memory_type=MemoryType.PROJECT,
                user_id=user_id,
                page=1,
                page_size=count
            )
        
        return docs

    async def get_tasks(self, user_id: str, project_id: str) -> List[MemoryDocument]:
        """Get all tasks for a specific project."""
        query = {
            "bool": {
                "must": [
                    {"term": {"parent_id": project_id}},
                    {"term": {"user_id": user_id}},
                    {"term": {"memory_type": MemoryType.TASK.value}}
                ]
            }
        }
        count = await self.count(query)
        if count == 0:
            return []

        results = await self.search(query, size=count, sort=[{"created_at": {"order": "asc"}}])
        if not results:
            return []
        return [MemoryDocument.from_dict(doc) for doc in results]

    async def list_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        user_id: Optional[str] = None,
        parent_id: Optional[str] = None,
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
            parent_id: Filter by parent memory ID
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
            
        if parent_id:
            query["bool"]["must"].append({"term": {"parent_id": parent_id}})
            
        # If no filters, match all documents
        if not query["bool"]["must"]:
            query = {"match_all": {}}
            
        # Calculate from/size for pagination
        from_ = (page - 1) * page_size
        
        # Build sort clause
        sort_clause = [{sort_by: {"order": sort_order}}]
        
        print(f"query: {query}")
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

    async def get_unprocessed_memories(
        self,
        batch_size: int = 10, 
        user_id: Optional[str] = None
    ) -> List[MemoryDocument]:
        """
        查询未处理的原始记忆
        
        Args:
            batch_size: 每次获取的记忆数量
            user_id: 可选的用户ID过滤
            
        Returns:
            List[MemoryDocument]: 未处理的记忆列表，按创建时间升序排序
        """
        try:
            # 构建查询，查找未处理的RAW类型记忆
            query = {
                "bool": {
                    "must": [
                        {"term": {"memory_type": MemoryType.RAW.value}},
                        {"term": {"processed": False}}
                    ]
                }
            }
            
            # 如果指定了用户ID，添加过滤条件
            if user_id:
                query["bool"]["must"].append({"term": {"user_id": user_id}})
            
            # 添加按创建时间升序排序，确保优先处理最旧的记忆
            sort_clause = [{"created_at": {"order": "asc"}}]
            
            # 执行查询
            results = await self.search(query, size=batch_size, sort=sort_clause)
            
            # 转换为MemoryDocument对象
            memory_docs = [MemoryDocument.from_dict(doc) for doc in results]
            
            return memory_docs
        
        except Exception as e:
            logging.error(f"获取未处理记忆时出错: {str(e)}")
            return []

    async def get_raw_memory_of_the_day(
        self,
        date_str: str,
        user_id: Optional[str] = None,
        size: int = 100
    ) -> List[MemoryDocument]:
        """
        获取指定日期的原始记忆
        
        Args:
            date_str: 日期字符串，支持多种格式，如YYYY-MM-DD, YYYY/MM/DD等
            user_id: 可选的用户ID过滤
            size: 返回的最大记录数
            
        Returns:
            List[MemoryDocument]: 指定日期的RAW类型记忆列表，按创建时间升序排序
        """
        try:
            # 使用dateutil.parser解析各种格式的日期
            from dateutil import parser
            date_obj = parser.parse(date_str)
            
            # 创建当天开始和结束的时间戳
            from datetime import datetime
            start_of_day = datetime.combine(date_obj.date(), datetime.min.time())
            end_of_day = datetime.combine(date_obj.date(), datetime.max.time())
            
            # 构建日期范围查询
            query = {
                "bool": {
                    "must": [
                        {"term": {"memory_type": MemoryType.RAW.value}},
                        {"range": {
                            "created_at": {
                                "gte": start_of_day.isoformat(),
                                "lte": end_of_day.isoformat()
                            }
                        }}
                    ]
                }
            }
            
            # 如果指定了用户ID，添加过滤条件
            if user_id:
                query["bool"]["must"].append({"term": {"user_id": user_id}})
            
            # 添加按创建时间升序排序
            sort_clause = [{"created_at": {"order": "asc"}}]
            
            # 执行查询
            results = await self.search(query, size=size, sort=sort_clause)
            
            # 转换为MemoryDocument对象
            memory_docs = [MemoryDocument.from_dict(doc) for doc in results]
            
            return memory_docs
            
        except Exception as e:
            logging.error(f"获取指定日期记忆时出错: {str(e)}")
            return []