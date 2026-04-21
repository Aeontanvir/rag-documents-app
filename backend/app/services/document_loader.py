from pathlib import Path

from langchain_core.documents import Document


def _build_loader(file_path: Path):
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        from langchain_community.document_loaders import PyPDFLoader

        return PyPDFLoader(str(file_path))

    if suffix == ".docx":
        from langchain_community.document_loaders import Docx2txtLoader

        return Docx2txtLoader(str(file_path))

    if suffix in {".md", ".markdown"}:
        from langchain_community.document_loaders import UnstructuredMarkdownLoader

        return UnstructuredMarkdownLoader(str(file_path))

    if suffix in {".html", ".htm"}:
        from langchain_community.document_loaders import UnstructuredHTMLLoader

        return UnstructuredHTMLLoader(str(file_path))

    if suffix in {".ppt", ".pptx"}:
        from langchain_community.document_loaders import UnstructuredPowerPointLoader

        return UnstructuredPowerPointLoader(str(file_path))

    if suffix in {".doc"}:
        from langchain_community.document_loaders import UnstructuredWordDocumentLoader

        return UnstructuredWordDocumentLoader(str(file_path))

    if suffix == ".csv":
        from langchain_community.document_loaders import CSVLoader

        return CSVLoader(str(file_path))

    if suffix == ".txt":
        from langchain_community.document_loaders import TextLoader

        return TextLoader(str(file_path), autodetect_encoding=True)

    from langchain_community.document_loaders import UnstructuredFileLoader

    return UnstructuredFileLoader(str(file_path))


def load_documents(file_path: Path) -> list[Document]:
    loader = _build_loader(file_path)
    documents = loader.load()

    for document in documents:
        document.metadata["filename"] = file_path.name
        document.metadata["file_type"] = file_path.suffix.lower().lstrip(".")
        document.metadata["source"] = str(file_path)

    return [doc for doc in documents if doc.page_content and doc.page_content.strip()]
