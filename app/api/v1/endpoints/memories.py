from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from enum import Enum

from app.db.elasticsearch.memory_repository import MemoryRepository
from app.db.elasticsearch.models import MemoryDocument, MemoryType

router = APIRouter()

class MemoryCreate(BaseModel):
    content: str
    user_id: str
    tags: List[str] = []
    title: Optional[str] = None
    summary: Optional[str] = None
    parent_id: Optional[str] = None
    related_ids: Optional[List[str]] = None

class MemoryIdResponse(BaseModel):
    id: str


class APIMemoryDocument(BaseModel):
    id: Optional[str] = None
    content: str
    memory_type: MemoryType
    tags: List[str] = Field(default_factory=list)
    user_id: str
    title: Optional[str] = None
    summary: Optional[str] = None
    parent_id: Optional[str] = None
    related_ids: Optional[List[str]] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class MemoryListResponse(BaseModel):
    memories: List[APIMemoryDocument]  # Changed from MemoryDocument to APIMemoryDocument
    total: int
    page: int
    page_size: int
    total_pages: int

@router.post("/", response_model=MemoryIdResponse)
async def create_raw_memory(memory: MemoryCreate):
    """
    Create a new raw memory.
    """
    try:
        # Create memory document
        memory_doc = MemoryDocument(
            content=memory.content,
            memory_type=MemoryType.RAW,
            tags=memory.tags,
            user_id=memory.user_id,
            title=memory.title,
            summary=memory.summary,
            parent_id=memory.parent_id,
            related_ids=memory.related_ids,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        # Store in repository
        repo = MemoryRepository()
        memory_id = await repo.create_memory(memory_doc)

        return MemoryIdResponse(id=memory_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=MemoryListResponse)
async def list_memories(
    memory_type: Optional[MemoryType] = None,
    user_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(created_at|updated_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$")
):
    """
    List memories with pagination and sorting.
    
    Args:
        memory_type: Filter by memory type
        user_id: Filter by user ID
        page: Page number (1-based)
        page_size: Number of items per page (1-100)
        sort_by: Field to sort by (created_at or updated_at)
        sort_order: Sort order (asc or desc)
    """
    try:
        repo = MemoryRepository()
        memory_docs, total = await repo.list_memories(
            memory_type=memory_type,
            user_id=user_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Convert MemoryDocument to APIMemoryDocument
        memories = [
            APIMemoryDocument(
                id=doc._id,
                content=doc.content,
                memory_type=doc.memory_type,
                tags=doc.tags,
                user_id=doc.user_id,
                title=doc.title,
                summary=doc.summary,
                parent_id=doc.parent_id,
                related_ids=doc.related_ids,
                created_at=doc.created_at,
                updated_at=doc.updated_at
            )
            for doc in memory_docs
        ]
        
        total_pages = (total + page_size - 1) // page_size
        
        return MemoryListResponse(
            memories=memories,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=MemoryListResponse)
async def vector_search(
    query: str,
    size: int = Query(10, ge=1, le=100),
    user_id: Optional[str] = None
):
    """
    Search memories using vector similarity.
    
    Args:
        query: The text query to search for
        size: Number of results to return (1-100)
        user_id: Optional user ID to filter results
        tags: Optional list of tags to filter results
    """
    try:
        # Generate embedding for the query
        from app.llm.embeddings import embed_text
        query_vector = embed_text(query)
        if not query_vector:
            raise HTTPException(status_code=400, detail="Failed to generate embedding for query")

        # Search using vector similarity
        repo = MemoryRepository()
        memory_docs = await repo.search_by_vector(
            vector=query_vector,
            user_id=user_id,
            size=size
        )
        
        # Convert MemoryDocument to APIMemoryDocument
        memories = [
            APIMemoryDocument(
                id=doc._id,
                content=doc.content,
                memory_type=doc.memory_type,
                tags=doc.tags,
                user_id=doc.user_id,
                title=doc.title,
                summary=doc.summary,
                parent_id=doc.parent_id,
                related_ids=doc.related_ids,
                created_at=doc.created_at,
                updated_at=doc.updated_at
            )
            for doc in memory_docs
        ]
        
        return MemoryListResponse(
            memories=memories,
            total=len(memories),
            page=1,
            page_size=size,
            total_pages=1
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))