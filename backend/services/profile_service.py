from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from backend.models import Experience, MasterBullet, Profile
from backend.schemas.experience import MasterBulletCreate
from backend.schemas.profile import ParsedProfile, ProfileCreate, ProfileUpdate
from backend.services.vector_service import ingest_user_bullets


def get_user_profile(
    db: Session,
    tenant_id: str,
    user_id: str,
) -> Optional[Profile]:
    """Retrieve candidate profile by tenant and user ID."""
    return (
        db.query(Profile)
        .filter(Profile.tenant_id == tenant_id, Profile.user_id == user_id)
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
        profile = Profile(
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


def save_parsed_profile_to_db(
    db: Session,
    tenant_id: str,
    user_id: str,
    parsed: ParsedProfile,
) -> Profile:
    """
    Persist an extracted ParsedProfile into relational tables (Profile, Experience, MasterBullet)
    and ingest all extracted bullet points into the pgvector knowledge vault.
    """
    # 1. Save or update Profile
    profile = get_user_profile(db, tenant_id=tenant_id, user_id=user_id)
    education_dicts = [edu.model_dump() for edu in parsed.education]
    cert_dicts = [cert.model_dump() for cert in parsed.certifications]

    if profile is None:
        profile = Profile(
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

    # 2. Save Experiences and Master Bullets
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
            master_bullet = MasterBullet(
                tenant_id=tenant_id,
                user_id=user_id,
                experience_id=experience.id,
                bullet_text=bullet_str,
                skills_used=exp_item.skills_used or [],
                category="Work Experience",
            )
            db.add(master_bullet)
            bullets_for_vector_indexing.append({
                "bullet_text": bullet_str,
                "skills_used": exp_item.skills_used or [],
                "category": "Work Experience",
                "experience_id": experience.id,
            })

    # Also extract bullets from projects if available
    for proj in parsed.projects:
        for proj_bullet in proj.bullet_points:
            master_bullet = MasterBullet(
                tenant_id=tenant_id,
                user_id=user_id,
                experience_id=None,
                project_name=proj.title,
                bullet_text=proj_bullet,
                skills_used=proj.technologies or [],
                category="Project",
            )
            db.add(master_bullet)
            bullets_for_vector_indexing.append({
                "bullet_text": proj_bullet,
                "skills_used": proj.technologies or [],
                "category": "Project",
                "project_name": proj.title,
            })

    db.commit()

    # 3. Vector Embeddings Ingestion (pgvector)
    if bullets_for_vector_indexing:
        try:
            ingest_user_bullets(
                tenant_id=tenant_id,
                user_id=user_id,
                bullets=bullets_for_vector_indexing,
            )
        except Exception as e:
            print(f"Warning: Vector ingestion skipped or deferred: {e}")

    return profile


def add_user_master_bullets(
    db: Session,
    tenant_id: str,
    user_id: str,
    bullets: List[MasterBulletCreate],
) -> List[MasterBullet]:
    """Manually add one or more master bullets and sync them to pgvector."""
    created_records: List[MasterBullet] = []
    vector_payloads: List[Dict[str, Any]] = []

    for b in bullets:
        bullet_record = MasterBullet(
            tenant_id=tenant_id,
            user_id=user_id,
            experience_id=b.experience_id,
            project_name=b.project_name,
            bullet_text=b.bullet_text,
            skills_used=b.skills_used,
            category=b.category,
            impact_metrics=b.impact_metrics,
        )
        db.add(bullet_record)
        created_records.append(bullet_record)
        vector_payloads.append(b.model_dump())

    db.commit()
    for rec in created_records:
        db.refresh(rec)

    # Sync to vector store
    if vector_payloads:
        try:
            ingest_user_bullets(
                tenant_id=tenant_id,
                user_id=user_id,
                bullets=vector_payloads,
            )
        except Exception as e:
            print(f"Warning: Vector ingestion skipped or deferred: {e}")

    return created_records


def get_user_master_bullets(
    db: Session,
    tenant_id: str,
    user_id: str,
) -> List[MasterBullet]:
    """Retrieve all master bullets for a candidate."""
    return (
        db.query(MasterBullet)
        .filter(MasterBullet.tenant_id == tenant_id, MasterBullet.user_id == user_id)
        .all()
    )
