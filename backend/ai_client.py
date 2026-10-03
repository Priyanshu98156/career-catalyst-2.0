import os
from functools import lru_cache
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from backend.config import GEMINI_CHAT_MODEL, GEMINI_EMBEDDING_MODEL

# Standardize Gemini API key across SDKs and LangChain
_api_key = (
    os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
    or os.getenv("GEMINIAPIKEY")
)

if _api_key:
    os.environ.setdefault("GOOGLE_API_KEY", _api_key)
    os.environ.setdefault("GEMINI_API_KEY", _api_key)


def get_api_key() -> str:
    """Return the validated Google GenAI API key."""
    if not _api_key:
        raise ValueError(
            "Gemini API key is not configured. "
            "Please set GEMINI_API_KEY or GOOGLE_API_KEY in your .env file."
        )
    return _api_key


@lru_cache(maxsize=4)
def get_chat_model(
    model: str = GEMINI_CHAT_MODEL,
    temperature: float = 0.0,
) -> ChatGoogleGenerativeAI:
    """
    Factory for ChatGoogleGenerativeAI instances.
    Default model is loaded dynamically from backend.config (GEMINI_CHAT_MODEL).
    Cached to prevent duplicate client instantiations.
    """
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=get_api_key(),
    )


@lru_cache(maxsize=2)
def get_embeddings_model(
    model: str = GEMINI_EMBEDDING_MODEL,
) -> GoogleGenerativeAIEmbeddings:
    """
    Factory for GoogleGenerativeAIEmbeddings instances.
    Default model is loaded dynamically from backend.config (GEMINI_EMBEDDING_MODEL).
    Cached singleton embedding model for vector store indexing.
    """
    return GoogleGenerativeAIEmbeddings(
        model=model,
        google_api_key=get_api_key(),
    )
