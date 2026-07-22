"""Gemini embeddings client — a single cached instance shared by ingestion
(embedding new chunks) and retrieval (embedding the user's question).
"""

from functools import lru_cache

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import get_settings


@lru_cache
def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    settings = get_settings()
    return GoogleGenerativeAIEmbeddings(
        model=settings.gemini_embedding_model,
        google_api_key=settings.gemini_api_key.get_secret_value(),
    )
