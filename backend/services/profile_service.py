from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from backend.models import Experience, MasterBullet, Profile, tenant_filter
from backend.schemas.experience import MasterBulletCreate
from backend.schemas.profile import ParsedProfile, ProfileCreate, ProfileUpdate
from backend.services.vector_service import ingest_user_bullets


def _new_profile(
    tenant_id: str,
    user_id: str,
    full_name: str,
    email: str,
    phone: Optional[str] = None,
    location: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    github_url: Optional[str] = None,
    portfolio_url: Optional[str] = None,
    summary: Optional[str] = None,
    skills: Optional[List[str]] = None,
    education: Optional[List[Dict[str, Any]]] = None,
    certifications: Optional[List[Dict[str, Any]]] = None,
) -> Profile:
    """Factory helper to construct a new Profile ORM model instance (DRY-3)."""
    return Profile(
        tenant_id=tenant_id,
        user_id=user_id,
        full_name=full_name,
        email=email,
        phone=phone,
        location=location,
        linkedin_url=linkedin_url,
        github_url=github_url,
        portfolio_url=portfolio_url,
        summary=summary,
        skills=skills or [],
        education=education or [],
        certifications=certifications or [],
    )


def _add_bullet(
    db: Session,
    tenant_id: str,
    user_id: str,
    bullet_text: str,
    experience_id: Optional[str] = None,
    project_name: Optional[str] = None,
    skills_used: Optional[List[str]] = None,
    category: str = "Work Experience",
    impact_metrics: Optional[str] = None,
) -> tuple[MasterBullet, Dict[str, Any]]:
    """Helper to instantiate MasterBullet, add to DB session, and return record and vector payload (DRY-5)."""
    skills = skills_used or []
    bullet_record = MasterBullet(
        tenant_id=tenant_id,
        user_id=user_id,
        experience_id=experience_id,
        project_name=project_name,
        bullet_text=bullet_text,
        skills_used=skills,
        category=category,
        impact_metrics=impact_metrics,
    )
    db.add(bullet_record)
    vector_payload = {
        "bullet_text": bullet_text,
        "skills_used": skills,
        "category": category,
        "experience_id": experience_id,
        "project_name": project_name,
        "impact_metrics": impact_metrics,
    }
    return bullet_record, vector_payload


def get_user_profile(
    db: Session,
    tenant_id: str,
    user_id: str,
) -> Optional[Profile]:
    """Retrieve candidate profile by tenant and user ID."""
    return (
        db.query(Profile)
        .filter(*tenant_filter(Profile, tenant_id, user_id))
        .first()
    )


def create_or_update_profile(
    db: Session,
    tenant_id: str,
    user_id: str,
    profile_data: ProfileCreate,
) -> Profile:
    """Create or update a candidate profile in the relational database."""
    profile = get_user_profile(db, tenant_id=tenant_id, user_id=user_id)

    if profile is None:
        profile = _new_profile(
            tenant_id=tenant_id,
            user_id=user_id,
            full_name=profile_data.full_name,
            email=profile_data.email,
            phone=profile_data.phone,
            location=profile_data.location,
            linkedin_url=profile_data.linkedin_url,
            github_url=profile_data.github_url,
            portfolio_url=profile_data.portfolio_url,
            summary=profile_data.summary,
            skills=profile_data.skills,
            education=profile_data.education,
            certifications=profile_data.certifications,
        )
        db.add(profile)
    else:
        # Update existing profile
        update_data = profile_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


def upsert_profile_from_parsed(
    db: Session,
    tenant_id: str,
    user_id: str,
    parsed: ParsedProfile,
) -> Profile:
    """Upsert profile metadata extracted from a parsed resume document."""
    profile = get_user_profile(db, tenant_id=tenant_id, user_id=user_id)
    education_dicts = [edu.model_dump() for edu in parsed.education]
    cert_dicts = [cert.model_dump() for cert in parsed.certifications]

    if profile is None:
        profile = _new_profile(
            tenant_id=tenant_id,
            user_id=user_id,
            full_name=parsed.full_name,
            email=parsed.email,
            phone=parsed.phone,
            location=parsed.location,
            linkedin_url=parsed.linkedin,
            github_url=parsed.github,
            portfolio_url=parsed.portfolio,
            summary=parsed.summary,
            skills=parsed.skills,
            education=education_dicts,
            certifications=cert_dicts,
        )
        db.add(profile)
    else:
        profile.full_name = parsed.full_name
        profile.email = parsed.email
        if parsed.phone:
            profile.phone = parsed.phone
        if parsed.location:
            profile.location = parsed.location
        if parsed.linkedin:
            profile.linkedin_url = parsed.linkedin
        if parsed.github:
            profile.github_url = parsed.github
        if parsed.portfolio:
            profile.portfolio_url = parsed.portfolio
        if parsed.summary:
            profile.summary = parsed.summary
        if parsed.skills:
            profile.skills = list(set(profile.skills + parsed.skills))
        if education_dicts:
            profile.education = education_dicts
        if cert_dicts:
            profile.certifications = cert_dicts

    db.commit()
    db.refresh(profile)
    return profile


def persist_parsed_experiences_and_bullets(
    db: Session,
    tenant_id: str,
    user_id: str,
    parsed: ParsedProfile,
) -> List[Dict[str, Any]]:
    """Persist work experiences and master bullets from a parsed resume and return vector payloads (DRY-5)."""
    bullets_for_vector_indexing: List[Dict[str, Any]] = []

    for exp_item in parsed.experiences:
        experience = Experience(
            tenant_id=tenant_id,
            user_id=user_id,
            company=exp_item.company,
            role=exp_item.role,
            location=exp_item.location,
            start_date=exp_item.duration,
            is_current=False,
        )
        db.add(experience)
        db.flush()  # Populates experience.id

        for bullet_str in exp_item.bullet_points:
            _, payload = _add_bullet(
                db=db,
                tenant_id=tenant_id,
                user_id=user_id,
                bullet_text=bullet_str,
                experience_id=experience.id,
                skills_used=exp_item.skills_used or [],
                category="Work Experience",
            )
            bullets_for_vector_indexing.append(payload)

    # Also extract bullets from projects if available
    for proj in parsed.projects:
        for proj_bullet in proj.bullet_points:
            _, payload = _add_bullet(
                db=db,
                tenant_id=tenant_id,
                user_id=user_id,
                bullet_text=proj_bullet,
                experience_id=None,
                project_name=proj.title,
                skills_used=proj.technologies or [],
                category="Project",
            )
            bullets_for_vector_indexing.append(payload)

    db.commit()
    return bullets_for_vector_indexing


def sync_bullets_to_vector_store(
    tenant_id: str,
    user_id: str,
    bullets: List[Dict[str, Any]],
) -> None:
    """Safely ingest bullet records into the pgvector store (DRY-4 centralized helper)."""
    if not bullets:
        return
    try:
        ingest_user_bullets(
            tenant_id=tenant_id,
            user_id=user_id,
            bullets=bullets,
        )
    except Exception as e:
        print(f"Warning: Vector ingestion skipped or deferred: {e}")


def save_parsed_profile_to_db(
    db: Session,
    tenant_id: str,
    user_id: str,
    parsed: ParsedProfile,
) -> Profile:
    """
    Persist an extracted ParsedProfile into relational tables (Profile, Experience, MasterBullet)
    and ingest all extracted bullet points into the pgvector knowledge vault.
    Decomposed to adhere strictly to SRP (SRP-1).
    """
    # 1. Upsert Profile entity
    profile = upsert_profile_from_parsed(db=db, tenant_id=tenant_id, user_id=user_id, parsed=parsed)

    # 2. Persist Experiences and Master Bullets
    bullets_for_vector_indexing = persist_parsed_experiences_and_bullets(
        db=db,
        tenant_id=tenant_id,
        user_id=user_id,
        parsed=parsed,
    )

    # 3. Vector Embeddings Ingestion (pgvector)
    sync_bullets_to_vector_store(
        tenant_id=tenant_id,
        user_id=user_id,
        bullets=bullets_for_vector_indexing,
    )

    return profile


def add_user_master_bullets(
    db: Session,
    tenant_id: str,
    user_id: str,
    bullets: List[MasterBulletCreate],
) -> List[MasterBullet]:
    """Manually add one or more master bullets and sync them to pgvector (DRY-5)."""
    created_records: List[MasterBullet] = []
    vector_payloads: List[Dict[str, Any]] = []

    for b in bullets:
        bullet_record, payload = _add_bullet(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            bullet_text=b.bullet_text,
            experience_id=b.experience_id,
            project_name=b.project_name,
            skills_used=b.skills_used,
            category=b.category,
            impact_metrics=b.impact_metrics,
        )
        created_records.append(bullet_record)
        vector_payloads.append(payload)

    db.commit()
    for rec in created_records:
        db.refresh(rec)

    # Sync to vector store via shared helper (DRY-4)
    sync_bullets_to_vector_store(
        tenant_id=tenant_id,
        user_id=user_id,
        bullets=vector_payloads,
    )

    return created_records


def get_user_master_bullets(
    db: Session,
    tenant_id: str,
    user_id: str,
) -> List[MasterBullet]:
    """Retrieve all master bullets for a candidate."""
    return (
        db.query(MasterBullet)
        .filter(*tenant_filter(MasterBullet, tenant_id, user_id))
        .all()
    )
