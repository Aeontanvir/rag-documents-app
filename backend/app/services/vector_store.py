from langchain_chroma import Chroma
from langchain_core.documents import Document
from typing import Optional

from app.config import get_settings
from app.services.llm_factory import build_embeddings


class VectorStoreService:
    def __init__(self) -> None:
        settings = get_settings()
        self.store = Chroma(
            collection_name=settings.chroma_collection_name,
            persist_directory=str(settings.chroma_dir),
            embedding_function=build_embeddings(),
        )

    def add_documents(self, documents: list[Document]) -> None:
        ids = [document.metadata["chunk_id"] for document in documents]
        self.store.add_documents(documents=documents, ids=ids)

    def similarity_search(
        self,
        query: str,
        *,
        limit: int,
        document_ids: Optional[list[str]] = None,
    ) -> list[tuple[Document, float]]:
        where = None
        if document_ids:
            if len(document_ids) == 1:
                where = {"document_id": document_ids[0]}
            else:
                where = {"document_id": {"$in": document_ids}}

        return self.store.similarity_search_with_relevance_scores(
            query=query,
            k=limit,
            filter=where,
        )

    def delete_document(self, document_id: str) -> None:
        self.store.delete(where={"document_id": document_id})
