from typing import Any, Callable, List, Optional
from langchain_core.prompts import ChatPromptTemplate

from backend.ai_client import get_chat_model
from backend.models import MasterBullet, tenant_filter
from backend.schemas.job import JDAnalysis
from backend.services.vector_service import search_user_bullets

JD_ANALYSIS_PROMPT = """You are an elite technical recruiter and ATS parser.
Analyze the target Job Description below and extract the key requirements into the structured schema.

CRITICAL INSTRUCTIONS:
1. Extract the accurate standard Job Title and Seniority Level (e.g., Junior, Mid, Senior, Lead, Staff, Principal).
2. Identify the Primary Skills (core programming languages, frameworks, cloud platforms, and tools).
3. Identify the Core Responsibilities (top duties and operational expectations).
4. Identify High-Value Keywords to Target (specific methodologies, buzzwords, and acronyms that an ATS scanner looks for).
5. If the company name is identifiable, extract it; otherwise leave it null.

JOB DESCRIPTION:
----------------
{job_description}
----------------
"""


def analyze_job_description(
    job_description: str,
    job_title: Optional[str] = None,
    company: Optional[str] = None,
) -> JDAnalysis:
    """
    Analyze a Job Description using Gemini structured output to extract
    primary skills, core responsibilities, and target ATS keywords.
    """
    if not job_description or not job_description.strip():
        raise ValueError("Job description text cannot be empty.")

    llm = get_chat_model(temperature=0.0)
    structured_llm = llm.with_structured_output(JDAnalysis)

    prompt = ChatPromptTemplate.from_template(JD_ANALYSIS_PROMPT)
    chain = prompt | structured_llm

    result: JDAnalysis = chain.invoke({"job_description": job_description})

    # Apply manual overrides if provided
    if job_title and not result.job_title:
        result.job_title = job_title
    if company and not result.company:
        result.company = company

    return result


def retrieve_candidate_bullets(
    tenant_id: str,
    user_id: str,
    jd_analysis: JDAnalysis,
    top_k: int = 8,
    fallback_loader: Optional[Callable[[], List[str]]] = None,
    db: Optional[Any] = None,
) -> List[str]:
    """
    Retrieve candidate master bullets matching the target JD.
    
    Strategy:
    1. Construct a targeted semantic query from job title, primary skills, and keywords.
    2. Query pgvector store with strict tenant_id & user_id isolation.
    3. Resilience Fallback: If vector store returns no results or encounters an issue,
       invoke injected fallback_loader (decoupled) or relational DB query (backward compatibility).
    """
    # 1. Build composite search query
    query_terms = [jd_analysis.job_title] + jd_analysis.primary_skills[:6] + jd_analysis.keywords_to_target[:4]
    search_query = " ".join([term for term in query_terms if term]).strip()

    retrieved_bullets: List[str] = []

    # 2. Semantic retrieval via pgvector
    try:
        documents = search_user_bullets(
            tenant_id=tenant_id,
            user_id=user_id,
            query=search_query,
            top_k=top_k,
        )
        retrieved_bullets = [doc.page_content for doc in documents if doc.page_content]
    except Exception as e:
        print(f"Notice: Vector similarity search fallback to relational DB: {e}")

    # 3. Resilient Fallback
    if not retrieved_bullets:
        if fallback_loader is not None:
            try:
                retrieved_bullets = fallback_loader()[:top_k]
            except Exception as e:
                print(f"Notice: Injected fallback bullet loader failed: {e}")
        elif db is not None:
            db_bullets = (
                db.query(MasterBullet.bullet_text)
                .filter(*tenant_filter(MasterBullet, tenant_id, user_id))
                .limit(top_k)
                .all()
            )
            retrieved_bullets = [b[0] for b in db_bullets if b[0]]

    return retrieved_bullets
