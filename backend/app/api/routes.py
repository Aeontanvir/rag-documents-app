from fastapi import APIRouter, Depends, File, UploadFile

from app.dependencies import get_rag_service
from app.schemas import (
    DeleteResponse,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    UploadResponse,
)
from app.services.rag import RagService


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse()


@router.get("/documents")
def list_documents(rag_service: RagService = Depends(get_rag_service)):
    return rag_service.list_documents()


@router.post("/documents/upload", response_model=UploadResponse)
async def upload_documents(
    files: list[UploadFile] = File(...),
    rag_service: RagService = Depends(get_rag_service),
) -> UploadResponse:
    results = []
    for upload in files:
        results.append(await rag_service.ingest_upload(upload))
    return UploadResponse(items=results)


@router.delete("/documents/{document_id}", response_model=DeleteResponse)
def delete_document(
    document_id: str,
    rag_service: RagService = Depends(get_rag_service),
) -> DeleteResponse:
    deleted = rag_service.delete_document(document_id)
    return DeleteResponse(deleted=True, document_id=deleted.document_id)


@router.post("/chat/query", response_model=QueryResponse)
def query_documents(
    payload: QueryRequest,
    rag_service: RagService = Depends(get_rag_service),
) -> QueryResponse:
    return rag_service.answer(payload)
