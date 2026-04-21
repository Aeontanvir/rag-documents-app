import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from langchain_core.prompts import ChatPromptTemplate

from app.config import get_settings
from app.schemas import DocumentRecord, QueryRequest, QueryResponse, SourceChunk, UploadResult
from app.services.chunking import ContextAwareChunker
from app.services.document_loader import load_documents
from app.services.llm_factory import build_chat_model
from app.services.manifest import ManifestStore
from app.services.vector_store import VectorStoreService


ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You answer questions using only the provided document context. "
            "If the answer is not grounded in the context, say that the documents do not contain enough information.",
        ),
        (
            "human",
            "Question:\n{question}\n\nContext:\n{context}\n\n"
            "Provide a concise answer and cite the supporting document names in prose.",
        ),
    ]
)


class RagService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.manifest = ManifestStore()
        self.chunker = ContextAwareChunker()
        self.vector_store = VectorStoreService()
        self.chat_model = build_chat_model()

    async def ingest_upload(self, upload: UploadFile) -> UploadResult:
        document_id = str(uuid4())
        target_path = self._persist_upload(document_id=document_id, upload=upload)
        await upload.close()

        try:
            documents = load_documents(target_path)
        except Exception as exc:
            target_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not parse '{upload.filename}': {exc}",
            ) from exc

        chunks = self.chunker.chunk(
            documents,
            document_id=document_id,
            filename=upload.filename or target_path.name,
        )
        if not chunks:
            target_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No readable content found in '{upload.filename}'.",
            )

        try:
            self.vector_store.add_documents(chunks)
        except ConnectionError as exc:
            target_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Embedding service is unavailable. "
                    "If you are using Ollama, install it, start it, and pull the configured embedding model."
                ),
            ) from exc

        stat = target_path.stat()
        record = DocumentRecord(
            document_id=document_id,
            filename=upload.filename or target_path.name,
            file_path=str(target_path),
            file_type=target_path.suffix.lower().lstrip("."),
            uploaded_at=datetime.now(timezone.utc),
            chunk_count=len(chunks),
            source_count=len(documents),
            size_bytes=stat.st_size,
        )
        self.manifest.upsert(record)

        return UploadResult(
            document=record,
            message=f"Ingested {record.filename} into {record.chunk_count} chunks.",
        )

    def list_documents(self) -> list[DocumentRecord]:
        return self.manifest.list_documents()

    def delete_document(self, document_id: str) -> DocumentRecord:
        record = self.manifest.remove(document_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        self.vector_store.delete_document(document_id)
        Path(record.file_path).unlink(missing_ok=True)
        return record

    def answer(self, request: QueryRequest) -> QueryResponse:
        try:
            matches = self.vector_store.similarity_search(
                request.question,
                limit=self.settings.retrieval_k,
                document_ids=request.document_ids,
            )
        except ConnectionError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Embedding service is unavailable. "
                    "If you are using Ollama, install it, start it, and pull the configured embedding model."
                ),
            ) from exc
        if not matches:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No relevant context found. Upload documents before querying.",
            )

        context_blocks: list[str] = []
        sources: list[SourceChunk] = []
        for document, score in matches:
            context_blocks.append(document.page_content)
            sources.append(
                SourceChunk(
                    document_id=document.metadata["document_id"],
                    filename=document.metadata.get("filename", "Unknown file"),
                    chunk_id=document.metadata["chunk_id"],
                    content=document.page_content[:500],
                    score=score,
                    page=(document.metadata.get("page") + 1)
                    if isinstance(document.metadata.get("page"), int)
                    else None,
                )
            )

        prompt = ANSWER_PROMPT.invoke(
            {
                "question": request.question,
                "context": "\n\n---\n\n".join(context_blocks),
            }
        )
        try:
            response = self.chat_model.invoke(prompt)
        except ConnectionError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "LLM service is unavailable. "
                    "If you are using Ollama, install it, start it, and pull the configured chat model."
                ),
            ) from exc
        response_text = self._stringify_response(response.content)

        return QueryResponse(answer=response_text, sources=sources)

    def _persist_upload(self, *, document_id: str, upload: UploadFile) -> Path:
        original_name = upload.filename or f"{document_id}.bin"
        suffix = Path(original_name).suffix
        safe_stem = Path(original_name).stem.replace(" ", "_")
        target_path = self.settings.uploads_dir / f"{document_id}_{safe_stem}{suffix}"

        with target_path.open("wb") as output_stream:
            shutil.copyfileobj(upload.file, output_stream)

        return target_path

    @staticmethod
    def _stringify_response(content: object) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    parts.append(str(item["text"]))
                else:
                    parts.append(str(item))
            return "\n".join(part for part in parts if part).strip()
        return str(content)
