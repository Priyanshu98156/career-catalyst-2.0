import unittest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import MasterBullet, Profile, TailoredResume, User
from backend.schemas.job import JDAnalysis
from backend.schemas.resume import (
    SynthesizedExperience,
    TailorRequest,
    TailoredResumeContent,
    TailoredResumeResponse,
)
from backend.services.rag_service import (
    analyze_job_description,
    retrieve_candidate_bullets,
)


class TestMilestone3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # In-memory SQLite DB for isolated unit testing
        cls.engine = create_engine("sqlite:///:memory:")
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        Base.metadata.create_all(self.engine)
        self.db = self.Session()
        self.tenant_id = f"tenant_{uuid.uuid4().hex[:8]}"
        self.user_id = f"user_{uuid.uuid4().hex[:8]}"

        # Seed test user
        user = User(
            id=self.user_id,
            tenant_id=self.tenant_id,
            email=f"candidate_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="hashed_pw_test",
            full_name="Elena Rostova",
        )
        self.db.add(user)

        # Seed test profile
        profile = Profile(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            full_name="Elena Rostova",
            email=user.email,
            skills=["Python", "FastAPI", "Docker", "PostgreSQL", "Kafka"],
            summary="Senior Backend Engineer with 6+ years of microservices experience.",
        )
        self.db.add(profile)

        # Seed master bullets
        bullets = [
            MasterBullet(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                bullet_text="Engineered distributed event-driven ingestion pipeline handling 10M events/day using Kafka and Go.",
                skills_used=["Go", "Kafka"],
                category="Work Experience",
            ),
            MasterBullet(
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                bullet_text="Reduced API latency by 45% through Redis caching and query indexing on PostgreSQL.",
                skills_used=["PostgreSQL", "Redis", "FastAPI"],
                category="Work Experience",
            ),
        ]
        self.db.add_all(bullets)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def test_empty_jd_validation(self):
        """Verify that empty or whitespace JD text is rejected."""
        with self.assertRaises(ValueError):
            analyze_job_description("")
        with self.assertRaises(ValueError):
            analyze_job_description("   ")

    def test_candidate_bullets_retrieval_fallback(self):
        """
        Verify that candidate bullet retrieval falls back to relational DB
        with strict tenant_id & user_id isolation when vector store is empty/offline.
        """
        jd_analysis = JDAnalysis(
            job_title="Senior Backend Engineer",
            primary_skills=["Python", "Kafka", "PostgreSQL"],
            core_responsibilities=["Build high-throughput APIs", "Maintain data pipelines"],
            keywords_to_target=["Distributed Systems", "Kafka", "Latency Optimization"],
        )

        retrieved = retrieve_candidate_bullets(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            jd_analysis=jd_analysis,
            top_k=5,
            db=self.db,
        )

        self.assertGreaterEqual(len(retrieved), 1)
        self.assertTrue(any("Kafka" in b for b in retrieved))

        # Check tenant isolation: another tenant should retrieve 0 bullets
        other_tenant_bullets = retrieve_candidate_bullets(
            tenant_id="other_tenant_999",
            user_id=self.user_id,
            jd_analysis=jd_analysis,
            top_k=5,
            db=self.db,
        )
        self.assertEqual(len(other_tenant_bullets), 0)

    def test_tailored_resume_persistence_and_history(self):
        """Verify creating, persisting, and querying tailored resume records."""
        sample_content = TailoredResumeContent(
            candidate_name="Elena Rostova",
            contact_info={"email": "candidate@example.com", "phone": "555-0199"},
            professional_summary="Senior Backend Engineer specialized in high-performance cloud systems.",
            highlighted_skills=["Python", "FastAPI", "Kafka", "PostgreSQL", "Docker"],
            experiences=[
                SynthesizedExperience(
                    company="CloudTech",
                    role="Senior Backend Engineer",
                    duration="2021 - Present",
                    tailored_bullets=[
                        "Architected event streaming architecture using Apache Kafka processing 10M+ events daily with 99.99% uptime.",
                        "Optimized PostgreSQL database queries and connection pooling, cutting latency by 45%."
                    ]
                )
            ]
        )

        resume = TailoredResume(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            title="Senior Backend Engineer Tailored Resume",
            structured_content=sample_content.model_dump(),
            raw_latex="\\documentclass{article} \\begin{document} Resume \\end{document}",
            match_score=92.5,
        )
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)

        self.assertIsNotNone(resume.id)

        # Retrieve resume by ID
        fetched = (
            self.db.query(TailoredResume)
            .filter_by(id=resume.id, tenant_id=self.tenant_id, user_id=self.user_id)
            .first()
        )
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.match_score, 92.5)
        self.assertEqual(fetched.structured_content["candidate_name"], "Elena Rostova")

        # Verify history count
        history = (
            self.db.query(TailoredResume)
            .filter_by(tenant_id=self.tenant_id, user_id=self.user_id)
            .all()
        )
        self.assertEqual(len(history), 1)

        # Tenant isolation check
        other_history = (
            self.db.query(TailoredResume)
            .filter_by(tenant_id="foreign_tenant", user_id=self.user_id)
            .all()
        )
        self.assertEqual(len(other_history), 0)


if __name__ == "__main__":
    unittest.main()
