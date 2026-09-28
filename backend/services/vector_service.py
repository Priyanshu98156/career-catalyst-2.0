from typing import Any, Dict, List, Optional
from langchain_core.documents import Document
from langchain_postgres import PGVector
from backend.ai_client import get_embeddings_model
from backend.database import DATABASE_URL, engine

COLLECTION_NAME = "user_experiences"

_vector_store_instance: Optional[PGVector] = None


def get_vector_store() -> PGVector:
    """
    Lazy singleton initializer for the PGVector store.
    Uses centralized embeddings model and database connection engine.
    """
    global _vector_store_instance
    if _vector_store_instance is None:
        embeddings = get_embeddings_model()
        _vector_store_instance = PGVector(
            embeddings=embeddings,
            collection_name=COLLECTION_NAME,
            connection=engine,
            use_jsonb=True,
            create_extension=False,  # Already handled in database.init_db
        )
    return _vector_store_instance


def ingest_user_bullets(
    tenant_id: str,
    user_id: str,
    bullets: List[Dict[str, Any]],
) -> List[str]:
    """
    Ingest a list of candidate achievement / project bullet points into pgvector.
    
    Each item in `bullets` is expected to have:
      - 'text' or 'bullet_text' (str)
      - 'skills' or 'skills_used' (List[str], optional)
      - 'category' (str, optional)
      - 'project_name' (str, optional)
    
    Enforces multi-tenant data isolation by stamping tenant_id & user_id onto metadata.
    """
    if not bullets:
        return []

    docs: List[Document] = []
    for item in bullets:
        text = item.get("bullet_text") or item.get("text")
        if not text:
            continue

        skills = item.get("skills_used") or item.get("skills") or []
        category = item.get("category", "Work Experience")
        project_name = item.get("project_name")
        experience_id = item.get("experience_id")

        metadata = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "skills": skills,
            "category": category,
            "project_name": project_name,
            "experience_id": experience_id,
            "type": "master_bullet",
        }

        docs.append(Document(page_content=text, metadata=metadata))

    if not docs:
        return []

    store = get_vector_store()
    return store.add_documents(docs)


def search_user_bullets(
    tenant_id: str,
    user_id: str,
    query: str,
    top_k: int = 8,
) -> List[Document]:
    """
    Perform semantic similarity search on candidate bullet points.
    Strictly filters by tenant_id and user_id to prevent multi-tenant data leakage.
    """
    store = get_vector_store()
    
    filter_criteria = {
        "tenant_id": tenant_id,
        "user_id": user_id,
    }

    return store.similarity_search(
        query=query,
        k=top_k,
        filter=filter_criteria,
    )
