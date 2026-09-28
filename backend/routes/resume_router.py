from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import JobDescription, TailoredResume
from backend.schemas.job import JDAnalysis, JDAnalysisRequest
from backend.schemas.resume import (
    TailorRequest,
    TailoredResumeModelResponse,
    TailoredResumeResponse,
)
from backend.services.profile_service import get_user_profile
from backend.services.rag_service import (
    analyze_job_description,
    retrieve_candidate_bullets,
)
from backend.services.synthesis_service import synthesize_tailored_resume

router = APIRouter(prefix="/api/resume", tags=["Resume Tailoring & RAG"])


def get_tenant_and_user(
    x_tenant_id: Optional[str] = Header("default_tenant", alias="X-Tenant-ID"),
    x_user_id: Optional[str] = Header("default_user", alias="X-User-ID"),
) -> tuple[str, str]:
    """Extract tenant_id and user_id from headers for multi-tenant isolation."""
    return x_tenant_id or "default_tenant", x_user_id or "default_user"


@router.post(
    "/analyze-jd",
    response_model=JDAnalysis,
    summary="Analyze target Job Description",
)
def analyze_jd_endpoint(
    request: JDAnalysisRequest,
    save_jd: bool = Query(default=False, description="Persist target JD in database"),
    db: Session = Depends(get_db),
    auth_context: tuple[str, str] = Depends(get_tenant_and_user),
):
    """
    Extract key requirements, technical skills, core responsibilities,
    and ATS keywords from a raw Job Description.
    """
    tenant_id, user_id = auth_context

    analysis = analyze_job_description(
        job_description=request.job_description,
        job_title=request.job_title,
        company=request.company,
    )

    if save_jd:
        jd_record = JobDescription(
            tenant_id=tenant_id,
            user_id=user_id,
            title=analysis.job_title,
            company=analysis.company,
            raw_text=request.job_description,
            primary_skills=analysis.primary_skills,
            responsibilities=analysis.core_responsibilities,
            keywords=analysis.keywords_to_target,
        )
        db.add(jd_record)
        db.commit()

    return analysis


@router.post(
    "/tailor",
    response_model=TailoredResumeResponse,
    summary="Generate ATS-tailored resume via RAG pipeline",
)
def tailor_resume_endpoint(
    request: TailorRequest,
    save_to_db: bool = Query(default=True, description="Persist synthesized resume in DB"),
    db: Session = Depends(get_db),
    auth_context: tuple[str, str] = Depends(get_tenant_and_user),
):
    """
    Full end-to-end RAG Resume Tailoring Pipeline:
    1. Analyzes the target Job Description.
    2. Retrieves top-K matching candidate achievements via pgvector with multi-tenant isolation.
    3. Fetches candidate base profile.
    4. Synthesizes tailored resume in structured JSON and LaTeX using STAR format.
    5. Calculates objective ATS match score and keyword gap analysis.
    6. Persists the tailored resume record in the database.
    """
    tenant_id, user_id = auth_context

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
            top_k=request.top_k_bullets,
            db=db,
        )

    # 3. Base Profile Context
    user_profile = get_user_profile(db=db, tenant_id=tenant_id, user_id=user_id)

    # 4. Synthesize Tailored Resume via LangChain
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


@router.get(
    "/history",
    response_model=List[TailoredResumeModelResponse],
    summary="Retrieve candidate generated resumes history",
)
def get_resume_history(
    db: Session = Depends(get_db),
    auth_context: tuple[str, str] = Depends(get_tenant_and_user),
):
    """List all previously generated tailored resumes for the tenant and user."""
    tenant_id, user_id = auth_context
    return (
        db.query(TailoredResume)
        .filter(TailoredResume.tenant_id == tenant_id, TailoredResume.user_id == user_id)
        .order_by(TailoredResume.created_at.desc())
        .all()
    )


@router.get(
    "/{resume_id}",
    response_model=TailoredResumeModelResponse,
    summary="Retrieve a specific tailored resume",
)
def get_resume_by_id(
    resume_id: str,
    db: Session = Depends(get_db),
    auth_context: tuple[str, str] = Depends(get_tenant_and_user),
):
    """Fetch a specific tailored resume by ID with tenant verification."""
    tenant_id, user_id = auth_context
    resume = (
        db.query(TailoredResume)
        .filter(
            TailoredResume.id == resume_id,
            TailoredResume.tenant_id == tenant_id,
            TailoredResume.user_id == user_id,
        )
        .first()
    )
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tailored resume not found.",
        )
    return resume
