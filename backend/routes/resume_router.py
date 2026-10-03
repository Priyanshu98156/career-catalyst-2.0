from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.dependencies import get_db, get_tenant_and_user
from backend.schemas.job import JDAnalysis, JDAnalysisRequest
from backend.schemas.resume import (
    TailorRequest,
    TailoredResumeModelResponse,
    TailoredResumeResponse,
)
from backend.services.rag_service import analyze_job_description
from backend.services.resume_service import (
    get_resume_by_id as fetch_resume_by_id,
    get_resume_history as fetch_resume_history,
    save_job_description_record,
    tailor_and_persist_resume,
)

router = APIRouter(prefix="/api/resume", tags=["Resume Tailoring & RAG"])


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
        save_job_description_record(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            raw_text=request.job_description,
            analysis=analysis,
        )

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
    Full end-to-end RAG Resume Tailoring Pipeline delegated to resume_service:
    1. Analyzes the target Job Description.
    2. Retrieves top-K matching candidate achievements via pgvector with multi-tenant isolation.
    3. Fetches candidate base profile.
    4. Synthesizes tailored resume in structured JSON and LaTeX using STAR format.
    5. Calculates objective ATS match score and keyword gap analysis.
    6. Persists the tailored resume record in the database.
    """
    tenant_id, user_id = auth_context
    return tailor_and_persist_resume(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        request=request,
        save_to_db=save_to_db,
    )


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
    return fetch_resume_history(db=db, tenant_id=tenant_id, user_id=user_id)


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
    resume = fetch_resume_by_id(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        resume_id=resume_id,
    )
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tailored resume not found.",
        )
    return resume
