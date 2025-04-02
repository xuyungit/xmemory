from typing import Dict, Any, List, Optional
from app.core.config import settings
from enum import Enum

class MemoryType(str, Enum):
    RAW = "raw"  # 原始记忆
    INSIGHT = "insight"  # 洞察记忆
    PROJECT = "project"  # 项目记忆
    TASK = "task"  # 项目任务
    DIARY = "diary"  # 日记
    WEEKLY = "weekly"  # 周报
    MONTHLY = "monthly"  # 月报
    QUARTERLY = "quarterly"  # 季报
    YEARLY = "yearly"  # 年报
    ARCHIVED = "archived"  # 已归档的记忆

# Example document mapping
MEMORY_DOCUMENT_MAPPING: Dict[str, Any] = {
    "properties": {
        "title": {"type": "text"},  # 可选的标题，用于快速识别记忆
        "summary": {"type": "text"},  # 可选的摘要，用于快速预览内容
        "content": {"type": "text"},  # 主要内容
        "tags": {"type": "keyword"},
        "memory_type": {"type": "keyword"},
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
        "user_id": {"type": "keyword"},
        "parent_id": {"type": "keyword"},  # 关联到父记忆（如果有）
        "related_ids": {"type": "keyword"},  # 关联的其他记忆ID列表
        "embedding": {
            "type": "dense_vector",
            "dims": settings.EMBEDDING_DIMENSION,
            "index": True,
            "similarity": "cosine"
        },
    }
}

# Example document structure
class MemoryDocument:
    def __init__(
        self,
        content: str,
        memory_type: MemoryType,
        tags: list[str],
        user_id: str,
        title: Optional[str] = None,  # 可选的标题
        summary: Optional[str] = None,  # 可选的摘要
        parent_id: Optional[str] = None,
        related_ids: Optional[List[str]] = None,
        embedding: Optional[List[float]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        _score: Optional[float] = None,
        _id: Optional[str] = None,
    ):
        self.content = content
        self.memory_type = memory_type
        self.tags = tags
        self.user_id = user_id
        self.title = title
        self.summary = summary
        self.parent_id = parent_id
        self.related_ids = related_ids or []
        self.embedding = embedding
        self.created_at = created_at
        self.updated_at = updated_at
        self._score = _score
        self._id = _id

    def to_dict(self) -> Dict[str, Any]:
        doc_dict = {
            "content": self.content,
            "memory_type": self.memory_type,
            "tags": self.tags,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.title:
            doc_dict["title"] = self.title
        if self.summary:
            doc_dict["summary"] = self.summary
        if self.parent_id:
            doc_dict["parent_id"] = self.parent_id
        if self.related_ids:
            doc_dict["related_ids"] = self.related_ids
        if self.embedding is not None:
            doc_dict["embedding"] = self.embedding
        return doc_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryDocument':
        return cls(**data)

    def __str__(self) -> str:
        id_str = f"id={self._id}, " if self._id else ""
        return (
            f"MemoryDocument("
            f"{id_str}"
            f"type={self.memory_type}, "
            f"title={self.title or 'No title'}, "
            f"content={self.content[:50]}..., "
            f"tags={self.tags}, "
            f"created_at={self.created_at},"
            f"_score={self._score}"
            f")"
        )

    def __repr__(self) -> str:
        return self.__str__() 