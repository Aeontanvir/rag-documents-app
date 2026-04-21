from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

from app.config import get_settings


def build_embeddings() -> Embeddings:
    settings = get_settings()

    if settings.embedding_provider.lower() == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )

    from langchain_ollama import OllamaEmbeddings

    return OllamaEmbeddings(model=settings.embedding_model)


def build_chat_model() -> BaseChatModel:
    settings = get_settings()

    if settings.llm_provider.lower() == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.llm_model,
            temperature=0,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )

    from langchain_ollama import ChatOllama

    return ChatOllama(model=settings.llm_model, temperature=0)
