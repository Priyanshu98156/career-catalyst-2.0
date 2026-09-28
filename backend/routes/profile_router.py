from typing import List, Optional
from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas.experience import MasterBulletCreate, MasterBulletResponse
from backend.schemas.profile import ParsedProfile, ProfileCreate, ProfileResponse
from backend.services.parser_service import parse_resume_document
from backend.services.profile_service import (
    add_user_master_bullets,
    create_or_update_profile,
    get_user_master_bullets,
    get_user_profile,
    save_parsed_profile_to_db,
)

router = APIRouter(prefix="/api/profile", tags=["Profile & Ingestion"])


def get_tenant_and_user(
    x_tenant_id: Optional[str] = Header("default_tenant", alias="X-Tenant-ID"),
    x_user_id: Optional[str] = Header("default_user", alias="X-User-ID"),
) -> tuple[str, str]:
    """Extract tenant_id and user_id from headers for multi-tenant isolation."""
    return x_tenant_id or "default_tenant", x_user_id or "default_user"


@router.post(
    "/upload-resume",
    response_model=ParsedProfile,
    summary="Upload and parse a resume document (PDF)",
)
async def upload_and_parse_resume(
    file: UploadFile = File(...),
    save_to_db: bool = Query(
        default=False,
        description="Whether to immediately persist extracted profile and embed bullets in pgvector",
    ),
    db: Session = Depends(get_db),
    auth_context: tuple[str, str] = Depends(get_tenant_and_user),
):
    """
    Upload a candidate resume PDF, extract text in-memory, and use Gemini to
    synthesize a strictly typed ParsedProfile object.
    Optionally saves the candidate profile and ingests bullets into pgvector.
    """
    tenant_id, user_id = auth_context

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currently, only PDF files are supported for resume extraction.",
        )

    try:
        content = await file.read()
        parsed = parse_resume_document(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse resume document: {str(e)}",
        )

    if save_to_db:
        try:
            save_parsed_profile_to_db(db, tenant_id=tenant_id, user_id=user_id, parsed=parsed)
        except Exception as e:
            print(f"Warning: Failed to save parsed profile to database: {e}")

    return parsed


@router.post(
    "/save",
    response_model=ProfileResponse,
    summary="Create or update candidate profile",
)
def save_profile(
    profile_data: ProfileCreate,
    db: Session = Depends(get_db),
    auth_context: tuple[str, str] = Depends(get_tenant_and_user),
):
    """Persist or update candidate profile info in the relational database."""
    tenant_id, user_id = auth_context
    return create_or_update_profile(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        profile_data=profile_data,
    )


@router.get(
    "",
    response_model=ProfileResponse,
    summary="Retrieve candidate profile",
)
def get_profile(
    db: Session = Depends(get_db),
    auth_context: tuple[str, str] = Depends(get_tenant_and_user),
):
    """Fetch candidate profile for the authenticated tenant and user."""
    tenant_id, user_id = auth_context
    profile = get_user_profile(db=db, tenant_id=tenant_id, user_id=user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found.",
        )
    return profile


@router.post(
    "/bullets",
    response_model=List[MasterBulletResponse],
    summary="Add and embed master bullets",
)
def add_bullets(
    bullets: List[MasterBulletCreate],
    db: Session = Depends(get_db),
    auth_context: tuple[str, str] = Depends(get_tenant_and_user),
):
    """
    Add new master bullets to the candidate vault and synchronize their
    embeddings into pgvector with tenant/user isolation.
    """
    tenant_id, user_id = auth_context
    return add_user_master_bullets(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        bullets=bullets,
    )


@router.get(
    "/bullets",
    response_model=List[MasterBulletResponse],
    summary="List all master bullets",
)
def list_bullets(
    db: Session = Depends(get_db),
    auth_context: tuple[str, str] = Depends(get_tenant_and_user),
):
    """Retrieve all master bullets associated with the current tenant and user."""
    tenant_id, user_id = auth_context
    return get_user_master_bullets(db=db, tenant_id=tenant_id, user_id=user_id)
