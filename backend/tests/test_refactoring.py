import unittest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config import DATABASE_URL, VECTOR_COLLECTION_NAME
import backend.database as db_mod
import backend.services.vector_service as vs_mod
import backend.models as models_mod
from backend.database import Base
from backend.dependencies import get_tenant_and_user
from backend.models import (
    Experience,
    JobDescription,
    MasterBullet,
    Profile,
    RefreshToken,
    TailoredResume,
    TenantMixin,
    User,
    UserTenantMixin,
    tenant_filter,
)
from backend.schemas.job import JDAnalysis
from backend.schemas.profile import (
    EducationItem,
    ParsedExperienceItem,
    ParsedProfile,
    ProjectItem,
)
from backend.schemas.resume import TailorRequest
from backend.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from backend.services.rag_service import retrieve_candidate_bullets
from backend.services.profile_service import (
    _add_bullet,
    _new_profile,
    persist_parsed_experiences_and_bullets,
    save_parsed_profile_to_db,
    sync_bullets_to_vector_store,
    upsert_profile_from_parsed,
)
from backend.services.resume_service import (
    get_resume_by_id,
    get_resume_history,
    save_job_description_record,
)


class TestRefactoringSuites(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self.tenant_id = f"tenant_{uuid.uuid4().hex[:8]}"
        self.user_id = f"user_{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_dry1_database_url_from_config(self):
        """DRY-1: Verify database.py shares the exact DATABASE_URL from config.py."""
        self.assertEqual(db_mod.DATABASE_URL, DATABASE_URL)

    def test_dry9_vector_collection_name_from_config(self):
        """DRY-9: Verify vector_service.py imports VECTOR_COLLECTION_NAME directly without alias."""
        self.assertEqual(vs_mod.VECTOR_COLLECTION_NAME, VECTOR_COLLECTION_NAME)
        self.assertFalse(hasattr(vs_mod, "COLLECTION_NAME"))

    def test_srp5_models_init_exports_only_orm_entities(self):
        """SRP-5: Verify models/__init__.py only exports ORM entities, not Pydantic schemas."""
        self.assertNotIn("ParsedProfile", models_mod.__all__)
        self.assertNotIn("TailorRequest", models_mod.__all__)
        self.assertIn("User", models_mod.__all__)
        self.assertIn("Profile", models_mod.__all__)
        self.assertIn("TailoredResume", models_mod.__all__)

    def test_dry2_dependencies_get_tenant_and_user(self):
        """DRY-2: Verify get_tenant_and_user correctly parses headers with defaults."""
        tid, uid = get_tenant_and_user(None, None)
        self.assertEqual(tid, "default_tenant")
        self.assertEqual(uid, "default_user")

        tid2, uid2 = get_tenant_and_user("corp_acme", "user_42")
        self.assertEqual(tid2, "corp_acme")
        self.assertEqual(uid2, "user_42")

    def test_srp3_security_module_isolation(self):
        """SRP-3: Verify security module handles crypto and JWT independently of DB."""
        hashed = hash_password("secretpass")
        self.assertTrue(verify_password("secretpass", hashed))
        self.assertFalse(verify_password("wrong", hashed))

        token = create_access_token("user_123", "tenant_abc", "user@test.com")
        payload = decode_token(token)
        self.assertEqual(payload["sub"], "user_123")
        self.assertEqual(payload["tenant_id"], "tenant_abc")
        self.assertEqual(payload["type"], "access")

    def test_srp2_dip2_resume_service_isolation(self):
        """SRP-2 & DIP-2: Verify resume_service handles JD persistence and resume queries."""
        analysis = JDAnalysis(
            job_title="ML Engineer",
            company="Neural Corp",
            primary_skills=["PyTorch", "FastAPI"],
            core_responsibilities=["Train LLMs"],
            keywords_to_target=["Transformers"],
        )
        jd_rec = save_job_description_record(
            db=self.db,
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            raw_text="Job description text here",
            analysis=analysis,
        )
        self.assertIsNotNone(jd_rec.id)
        self.assertEqual(jd_rec.title, "ML Engineer")

        # Create tailored resume in DB
        resume = TailoredResume(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            title="ML Engineer Tailored Resume",
            structured_content={"headline": "ML Engineer"},
            raw_latex="\\documentclass{article}",
            match_score=94.5,
        )
        self.db.add(resume)
        self.db.commit()

        history = get_resume_history(self.db, self.tenant_id, self.user_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].title, "ML Engineer Tailored Resume")

        fetched = get_resume_by_id(self.db, self.tenant_id, self.user_id, resume.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, resume.id)

    def test_srp1_dry3_dry4_profile_service_decomposition(self):
        """SRP-1, DRY-3, DRY-4: Verify decomposed profile service functions."""
        parsed = ParsedProfile(
            full_name="Jane Doe",
            email="jane@example.com",
            phone="1234567890",
            location="San Francisco, CA",
            linkedin="linkedin.com/in/janedoe",
            github="github.com/janedoe",
            portfolio=None,
            summary="Passionate AI Engineer",
            skills=["Python", "TensorFlow"],
            education=[
                EducationItem(degree="BS CS", institution="MIT", graduation_year="2020")
            ],
            experiences=[
                ParsedExperienceItem(
                    company="AI Labs",
                    role="Research Engineer",
                    duration="2020 - Present",
                    bullet_points=["Designed diffusion models for image synthesis."],
                    skills_used=["Python", "PyTorch"],
                )
            ],
            projects=[
                ProjectItem(
                    title="OpenSource Agent",
                    technologies=["LangChain", "FastAPI"],
                    bullet_points=["Created autonomous coding workflow."],
                )
            ],
            certifications=[],
        )

        # 1. Upsert Profile
        prof = upsert_profile_from_parsed(self.db, self.tenant_id, self.user_id, parsed)
        self.assertEqual(prof.full_name, "Jane Doe")
        self.assertEqual(prof.email, "jane@example.com")

        # 2. Persist experiences
        payloads = persist_parsed_experiences_and_bullets(self.db, self.tenant_id, self.user_id, parsed)
        self.assertEqual(len(payloads), 2)

        # 3. Vector sync helper should not crash when offline
        sync_bullets_to_vector_store(self.tenant_id, self.user_id, payloads)

    def test_dry3_new_profile_factory(self):
        """DRY-3: Verify _new_profile factory creates populated Profile instances."""
        p = _new_profile(
            tenant_id="tenant_test",
            user_id="user_test",
            full_name="Alice Smith",
            email="alice@test.com",
            skills=["Python", "Go"],
        )
        self.assertEqual(p.tenant_id, "tenant_test")
        self.assertEqual(p.full_name, "Alice Smith")
        self.assertEqual(p.skills, ["Python", "Go"])
        self.assertEqual(p.education, [])

    def test_dry5_add_bullet_helper(self):
        """DRY-5: Verify _add_bullet helper creates record and vector payload."""
        rec, payload = _add_bullet(
            db=self.db,
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            bullet_text="Built low-latency gRPC service.",
            category="Work Experience",
            skills_used=["Go", "gRPC"],
        )
        self.db.commit()
        self.assertIsNotNone(rec.id)
        self.assertEqual(rec.bullet_text, "Built low-latency gRPC service.")
        self.assertEqual(payload["bullet_text"], "Built low-latency gRPC service.")
        self.assertEqual(payload["category"], "Work Experience")

    def test_dry8_tenant_filter(self):
        """DRY-8: Verify tenant_filter constructs correct SQL clauses."""
        clauses_user = tenant_filter(Profile, "tenant_xyz", "user_123")
        self.assertEqual(len(clauses_user), 2)

        clauses_tenant_only = tenant_filter(User, "tenant_xyz")
        self.assertEqual(len(clauses_tenant_only), 1)

    def test_dry10_mixins_inheritance(self):
        """DRY-10: Verify all models inherit from TenantMixin and UserTenantMixin."""
        self.assertTrue(issubclass(User, TenantMixin))
        self.assertTrue(issubclass(Profile, UserTenantMixin))
        self.assertTrue(issubclass(Experience, UserTenantMixin))
        self.assertTrue(issubclass(MasterBullet, UserTenantMixin))
        self.assertTrue(issubclass(JobDescription, UserTenantMixin))
        self.assertTrue(issubclass(TailoredResume, UserTenantMixin))
        self.assertTrue(issubclass(RefreshToken, UserTenantMixin))

    def test_isp1_tailor_request_validation(self):
        """ISP-1: Verify TailorRequest mutual exclusivity and minimum length validation."""
        # 1. Valid request without master_bullets defaults top_k_bullets to 8
        req1 = TailorRequest(job_description="Senior Backend Engineer role with Python and FastAPI experience")
        self.assertEqual(req1.top_k_bullets, 8)
        self.assertIsNone(req1.master_bullets)

        # 2. When master_bullets provided, top_k_bullets is set to None (mutual exclusivity guard)
        req2 = TailorRequest(
            job_description="Senior Backend Engineer role with Python and FastAPI experience",
            master_bullets=["Engineered distributed event ingestion pipeline"],
            top_k_bullets=10,
        )
        self.assertIsNone(req2.top_k_bullets)
        self.assertEqual(len(req2.master_bullets), 1)

        # 3. Empty job description fails validation
        with self.assertRaises(ValueError):
            TailorRequest(job_description="short")

    def test_isp2_rag_service_fallback_loader(self):
        """ISP-2: Verify retrieve_candidate_bullets works with decoupled fallback_loader (no DB)."""
        jd_analysis = JDAnalysis(
            job_title="DevOps Lead",
            primary_skills=["Terraform", "Kubernetes"],
            core_responsibilities=["Maintain CI/CD pipelines"],
            keywords_to_target=["GitOps", "Kubernetes"],
        )
        mock_bullets = ["Automated multi-region AWS infrastructure with Terraform."]

        # Invoking without a db Session, using pure fallback callable
        results = retrieve_candidate_bullets(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            jd_analysis=jd_analysis,
            top_k=3,
            fallback_loader=lambda: mock_bullets,
        )
        self.assertEqual(results, mock_bullets)


