from typing import List, Optional
from sqlalchemy.orm import Session

from backend.ai_client import get_chat_model
from backend.models import JobDescription, TailoredResume, tenant_filter
from backend.schemas.job import JDAnalysis, JDAnalysisRequest
from backend.schemas.resume import TailorRequest, TailoredResumeResponse
from backend.services.profile_service import get_user_master_bullets, get_user_profile
from backend.services.rag_service import (
    analyze_job_description,
    retrieve_candidate_bullets,
)
from backend.services.synthesis_service import synthesize_tailored_resume


def save_job_description_record(
    db: Session,
    tenant_id: str,
    user_id: str,
    raw_text: str,
    analysis: JDAnalysis,
) -> JobDescription:
    """Persist an analyzed Job Description record to the relational database."""
    jd_record = JobDescription(
        tenant_id=tenant_id,
        user_id=user_id,
        title=analysis.job_title,
        company=analysis.company,
        raw_text=raw_text,
        primary_skills=analysis.primary_skills,
        responsibilities=analysis.core_responsibilities,
        keywords=analysis.keywords_to_target,
    )
    db.add(jd_record)
    db.commit()
    db.refresh(jd_record)
    return jd_record


def tailor_and_persist_resume(
    db: Session,
    tenant_id: str,
    user_id: str,
    request: TailorRequest,
    save_to_db: bool = True,
) -> TailoredResumeResponse:
    """
    End-to-end RAG Resume Tailoring Pipeline:
    1. Analyzes the target Job Description.
    2. Retrieves top-K matching candidate achievements via pgvector with multi-tenant isolation.
    3. Fetches candidate base profile.
    4. Synthesizes tailored resume in structured JSON and LaTeX using STAR format.
    5. Calculates objective ATS match score and keyword gap analysis.
    6. Persists the tailored resume record in the database if requested.
    """
    # 1. Analyze Job Description
    jd_analysis = analyze_job_description(
        job_description=request.job_description,
        job_title=request.target_job_title,
    )

    # 2. Candidate Bullets (Manual override or RAG semantic retrieval)
    if request.master_bullets and len(request.master_bullets) > 0:
        candidate_bullets = request.master_bullets
    else:
        candidate_bullets = retrieve_candidate_bullets(
            tenant_id=tenant_id,
            user_id=user_id,
            jd_analysis=jd_analysis,
            top_k=request.top_k_bullets or 8,
            fallback_loader=lambda: [b.bullet_text for b in get_user_master_bullets(db, tenant_id, user_id)],
        )

    # 3. Base Profile Context
    user_profile = get_user_profile(db=db, tenant_id=tenant_id, user_id=user_id)

    # 4. Synthesize Tailored Resume via synthesis service
    tailored_response = synthesize_tailored_resume(
        job_description=request.job_description,
        jd_analysis=jd_analysis,
        retrieved_bullets=candidate_bullets,
        user_profile=user_profile,
    )

    # 5. Persist to Relational DB if requested
    if save_to_db:
        resume_record = TailoredResume(
            tenant_id=tenant_id,
            user_id=user_id,
            title=f"{jd_analysis.job_title} Tailored Resume",
            structured_content=tailored_response.structured_resume.model_dump(),
            raw_latex=tailored_response.latex_source,
            match_score=tailored_response.match_score,
        )
        db.add(resume_record)
        db.commit()
        db.refresh(resume_record)
        tailored_response.id = resume_record.id

    return tailored_response


def get_resume_history(
    db: Session,
    tenant_id: str,
    user_id: str,
) -> List[TailoredResume]:
    """Retrieve all candidate generated resumes ordered by creation date."""
    return (
        db.query(TailoredResume)
        .filter(*tenant_filter(TailoredResume, tenant_id, user_id))
        .order_by(TailoredResume.created_at.desc())
        .all()
    )


def get_resume_by_id(
    db: Session,
    tenant_id: str,
    user_id: str,
    resume_id: str,
) -> Optional[TailoredResume]:
    """Retrieve a single tailored resume by ID with tenant verification."""
    return (
        db.query(TailoredResume)
        .filter(
            TailoredResume.id == resume_id,
            *tenant_filter(TailoredResume, tenant_id, user_id),
        )
        .first()
    )


def generate_tailored_resume(request: TailorRequest, chat_model=None) -> TailoredResumeResponse:
    """
    Direct synthesis helper using the centralized LLM factory (DIP-1 compliant).
    Allows dependency injection for unit testing.
    """
    model = chat_model or get_chat_model(temperature=0.0)
    prompt = f"""
    You are an expert technical recruiter. 
    Analyze this Job Description: {request.job_description}
    Filter and rewrite the following master bullets to perfectly match the JD keywords.
    Master Bullets: {request.master_bullets}
    Generate the raw LaTeX string for the final output.
    """
    structured_llm = model.with_structured_output(TailoredResumeResponse)
    return structured_llm.invoke(prompt)