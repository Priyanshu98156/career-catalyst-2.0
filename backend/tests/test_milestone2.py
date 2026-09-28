import io
import unittest
import uuid
from pypdf import PdfWriter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import Experience, MasterBullet, Profile, User
from backend.schemas.experience import MasterBulletCreate
from backend.schemas.profile import (
    EducationItem,
    ParsedExperienceItem,
    ParsedProfile,
    ProfileCreate,
    ProjectItem,
)
from backend.services.parser_service import extract_text_from_pdf
from backend.services.profile_service import (
    add_user_master_bullets,
    create_or_update_profile,
    get_user_master_bullets,
    get_user_profile,
    save_parsed_profile_to_db,
)


class TestMilestone2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # In-memory SQLite DB for testing
        cls.engine = create_engine("sqlite:///:memory:")
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        Base.metadata.create_all(self.engine)
        self.db = self.Session()
        self.tenant_id = f"tenant_{uuid.uuid4().hex[:8]}"
        self.user_id = f"user_{uuid.uuid4().hex[:8]}"

        user = User(
            id=self.user_id,
            tenant_id=self.tenant_id,
            email=f"candidate_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="hashed_pw_test",
            full_name="Alex Mercer",
        )
        self.db.add(user)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def test_pdf_extraction_in_memory(self):
        """Verify that PDF text extraction handles byte streams and validates text presence."""
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        pdf_stream = io.BytesIO()
        writer.write(pdf_stream)
        pdf_bytes = pdf_stream.getvalue()

        # Blank PDF has no text, so it should raise ValueError
        with self.assertRaises(ValueError):
            extract_text_from_pdf(pdf_bytes)

    def test_profile_creation_and_update(self):
        """Test creating and subsequently updating a candidate profile."""
        profile_data = ProfileCreate(
            full_name="Alex Mercer",
            email="candidate@example.com",
            phone="+1-555-0199",
            location="San Francisco, CA",
            skills=["Python", "FastAPI", "PostgreSQL"],
        )

        created = create_or_update_profile(
            self.db,
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            profile_data=profile_data,
        )

        self.assertIsNotNone(created.id)
        self.assertEqual(created.full_name, "Alex Mercer")
        self.assertIn("Python", created.skills)

        # Update profile
        profile_data.location = "New York, NY"
        profile_data.skills.append("LangChain")
        updated = create_or_update_profile(
            self.db,
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            profile_data=profile_data,
        )
        self.assertEqual(updated.location, "New York, NY")
        self.assertIn("LangChain", updated.skills)

    def test_save_parsed_profile_hierarchy(self):
        """Test converting ParsedProfile into relational records (Profile, Experience, MasterBullets)."""
        parsed = ParsedProfile(
            full_name="Alex Mercer",
            email="candidate@example.com",
            phone="123-456-7890",
            skills=["Go", "Docker", "PostgreSQL"],
            education=[
                EducationItem(institution="MIT", degree="B.S. Computer Science", start_year="2018", end_year="2022")
            ],
            experiences=[
                ParsedExperienceItem(
                    company="Tech Corp",
                    role="Senior Backend Engineer",
                    duration="2022 - Present",
                    bullet_points=[
                        "Architected event-driven microservices reducing p99 latency by 35%",
                        "Led team of 4 engineers implementing Kafka event streaming pipeline"
                    ],
                    skills_used=["Go", "Kafka", "Docker"]
                )
            ],
            projects=[
                ProjectItem(
                    title="Distributed KV Store",
                    technologies=["Raft", "Go"],
                    bullet_points=["Built Raft consensus algorithm handling node partitions gracefully"]
                )
            ]
        )

        profile = save_parsed_profile_to_db(
            self.db,
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            parsed=parsed,
        )

        self.assertIsNotNone(profile)
        self.assertEqual(profile.full_name, "Alex Mercer")

        # Verify experiences created
        experiences = self.db.query(Experience).filter_by(user_id=self.user_id).all()
        self.assertEqual(len(experiences), 1)
        self.assertEqual(experiences[0].company, "Tech Corp")

        # Verify master bullets created (2 from experience + 1 from project = 3 total)
        bullets = get_user_master_bullets(self.db, tenant_id=self.tenant_id, user_id=self.user_id)
        self.assertEqual(len(bullets), 3)

        bullet_texts = [b.bullet_text for b in bullets]
        self.assertTrue(any("latency by 35%" in t for t in bullet_texts))
        self.assertTrue(any("Raft consensus" in t for t in bullet_texts))

    def test_add_and_list_master_bullets(self):
        """Test manually inserting master bullets and verifying tenant isolation."""
        bullets_input = [
            MasterBulletCreate(
                bullet_text="Optimized SQL queries cutting report generation time from 10m to 15s",
                skills_used=["PostgreSQL", "Query Optimization"],
                category="Work Experience",
                impact_metrics="97% time reduction",
            )
        ]

        added = add_user_master_bullets(
            self.db,
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            bullets=bullets_input,
        )
        self.assertEqual(len(added), 1)

        fetched = get_user_master_bullets(self.db, tenant_id=self.tenant_id, user_id=self.user_id)
        self.assertTrue(any(b.impact_metrics == "97% time reduction" for b in fetched))

        # Check tenant isolation: another tenant should see 0 bullets
        other_tenant_bullets = get_user_master_bullets(self.db, tenant_id="other_tenant", user_id=self.user_id)
        self.assertEqual(len(other_tenant_bullets), 0)


if __name__ == "__main__":
    unittest.main()
