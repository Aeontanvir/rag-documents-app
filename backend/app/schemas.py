from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class DocumentRecord(BaseModel):
    document_id: str
    filename: str
    file_path: str
    file_type: str
    uploaded_at: datetime
    chunk_count: int
    source_count: int
    size_bytes: int


class UploadResult(BaseModel):
    document: DocumentRecord
    message: str


class UploadResponse(BaseModel):
    items: list[UploadResult]


class SourceChunk(BaseModel):
    document_id: str
    filename: str
    chunk_id: str
    content: str
    score: Optional[float] = None
    page: Optional[int] = None


class QueryRequest(BaseModel):
    question: str = Field(min_length=3)
    document_ids: Optional[list[str]] = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


class DeleteResponse(BaseModel):
    deleted: bool
    document_id: str
