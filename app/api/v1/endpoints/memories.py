from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from enum import Enum
import pytz
from dateutil import parser
import logging

from app.db.elasticsearch.memory_repository import MemoryRepository
from app.db.elasticsearch.models import MemoryDocument, MemoryType
from app.storage.file_storage import FileStorage

from app.llm.memory_agent import update_insight_memory

router = APIRouter()
file_storage = FileStorage()

class MemoryCreate(BaseModel):
    content: str
    user_id: str
    tags: List[str] = []
    title: Optional[str] = None
    summary: Optional[str] = None
    parent_id: Optional[str] = None
    related_ids: Optional[List[str]] = None
    created_at: Optional[str] = None  # 支持多种格式，如：2024-03-20, 2024-03-20 14:30, 2024-03-20T14:30:00+08:00

class MemoryIdResponse(BaseModel):
    id: str

class DeleteMemoryResponse(BaseModel):
    success: bool
    message: str

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
async def create_memory(memory: MemoryCreate):
    """
    Create a new memory and save it to both Elasticsearch and local file storage.
    """
    try:
        # Create memory document
        if memory.created_at:
            try:
                # 使用 dateutil.parser 解析各种格式的日期时间
                created_at = parser.parse(memory.created_at)
                # 确保时区为 UTC+8
                if created_at.tzinfo is None:
                    created_at = pytz.timezone('Asia/Shanghai').localize(created_at)
                else:
                    created_at = created_at.astimezone(pytz.timezone('Asia/Shanghai'))
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")
        else:
            created_at = datetime.now(pytz.timezone('Asia/Shanghai'))
            
        # 统一使用 ISO 格式，包含时区信息
        created_at_str = created_at.strftime('%Y-%m-%dT%H:%M:%S%z')
        updated_at = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%dT%H:%M:%S%z')
            
        memory_doc = MemoryDocument(
            content=memory.content,
            memory_type=MemoryType.RAW,
            tags=memory.tags,
            user_id=memory.user_id,
            title=memory.title,
            summary=memory.summary,
            parent_id=memory.parent_id,
            related_ids=memory.related_ids,
            created_at=created_at_str,
            updated_at=updated_at,
            processed=False
        )

        # Store in repository
        repo = MemoryRepository()
        memory_id = await repo.create_memory(memory_doc)

        # Save to local file storage
        memory_data = memory_doc.to_dict()
        memory_data["_id"] = memory_id  # Add the ID to the data
        file_storage.save_memory(memory_id, memory_data)

        # update insight memory
        await update_insight_memory(memory_doc)
        return MemoryIdResponse(id=memory_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{memory_id}", response_model=DeleteMemoryResponse)
async def delete_memory(memory_id: str, user_id: Optional[str] = None):
    """
    删除指定ID的记忆数据
    
    Args:
        memory_id: 要删除的记忆ID
        user_id: 可选的用户ID，用于验证记忆所有权
    """
    try:
        repo = MemoryRepository()
        
        # 如果提供了user_id，先检查记忆是否属于该用户
        if user_id:
            memory = await repo.get_memory(memory_id)
            if not memory:
                raise HTTPException(status_code=404, detail=f"记忆ID '{memory_id}' 不存在")
                
            if memory.user_id != user_id:
                raise HTTPException(status_code=403, detail="没有权限删除此记忆")
            
            # 删除本地文件存储
            try:
                file_storage.delete_memory(memory_id, user_id)
            except FileNotFoundError:
                # 如果文件不存在，只记录日志，不影响整体删除流程
                logging.warning(f"本地文件不存在: {memory_id} for user {user_id}")
        
        # 从 Elasticsearch 中删除记忆
        success = await repo.delete_memory(memory_id)
        if not success:
            raise HTTPException(status_code=500, detail=f"删除记忆失败: {memory_id}")
        
        return DeleteMemoryResponse(
            success=True, 
            message=f"记忆 '{memory_id}' 已成功删除"
        )
        
    except HTTPException:
        raise
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
        repo = MemoryRepository()
        memory_docs = await repo.search_by_similarity(
            query=query,
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