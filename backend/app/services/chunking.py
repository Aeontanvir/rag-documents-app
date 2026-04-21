import re
from typing import Iterable

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings


def _clean_text(value: str) -> str:
    value = value.replace("\x00", " ")
    value = re.sub(r"\n{3,}", "\n\n", value)
    value = re.sub(r"[ \t]{2,}", " ", value)
    return value.strip()


class ContextAwareChunker:
    def __init__(self) -> None:
        settings = get_settings()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=[
                "\n# ",
                "\n## ",
                "\n### ",
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
            length_function=len,
            add_start_index=True,
        )

    def chunk(
        self,
        documents: Iterable[Document],
        *,
        document_id: str,
        filename: str,
    ) -> list[Document]:
        normalized: list[Document] = []

        for source_index, document in enumerate(documents):
            page_content = _clean_text(document.page_content)
            if not page_content:
                continue

            page_number = document.metadata.get("page")
            page_label = f"Page {page_number + 1}" if isinstance(page_number, int) else None
            header_parts = [filename]
            if page_label:
                header_parts.append(page_label)

            contextualized = " | ".join(header_parts) + "\n\n" + page_content
            metadata = dict(document.metadata)
            metadata["document_id"] = document_id
            metadata["source_index"] = source_index

            normalized.append(Document(page_content=contextualized, metadata=metadata))

        chunks = self.splitter.split_documents(normalized)
        for index, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = index
            chunk.metadata["chunk_id"] = f"{document_id}-chunk-{index:04d}"
        return chunks
