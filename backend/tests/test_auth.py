import unittest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import User, RefreshToken
from backend.schemas.auth import UserCreate
from backend.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    register_user,
    revoke_user_refresh_token,
    rotate_refresh_token,
    verify_password,
)


class TestAuthDoubleToken(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database for fast isolated unit testing
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self.test_tenant = f"tenant_{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_password_hashing_and_verification(self):
        password = "superSecurePassword123!"
        hashed = hash_password(password)

        self.assertNotEqual(password, hashed)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("wrongPassword", hashed))

    def test_user_registration_and_authentication(self):
        user_in = UserCreate(
            email="priyanshu@example.com",
            password="mypassword123",
            full_name="Priyanshu Gupta",
            tenant_id=self.test_tenant,
        )
        user = register_user(user_in, self.db)

        self.assertIsNotNone(user.id)
        self.assertEqual(user.email, "priyanshu@example.com")
        self.assertEqual(user.tenant_id, self.test_tenant)

        # Authenticate with valid credentials
        authed = authenticate_user("priyanshu@example.com", "mypassword123", self.test_tenant, self.db)
        self.assertIsNotNone(authed)
        self.assertEqual(authed.id, user.id)

        # Authenticate with invalid credentials
        invalid = authenticate_user("priyanshu@example.com", "wrongpass", self.test_tenant, self.db)
        self.assertIsNone(invalid)

    def test_double_token_issuance_and_decoding(self):
        user_in = UserCreate(
            email="developer@example.com",
            password="password999",
            full_name="Dev User",
            tenant_id=self.test_tenant,
        )
        user = register_user(user_in, self.db)

        access_token = create_access_token(user_id=user.id, tenant_id=user.tenant_id, email=user.email)
        refresh_token = create_refresh_token(user_id=user.id, tenant_id=user.tenant_id, db=self.db)

        self.assertIsInstance(access_token, str)
        self.assertIsInstance(refresh_token, str)

        payload = decode_token(access_token)
        self.assertEqual(payload["sub"], user.id)
        self.assertEqual(payload["tenant_id"], user.tenant_id)
        self.assertEqual(payload["type"], "access")

    def test_refresh_token_rotation(self):
        user_in = UserCreate(
            email="rotate@example.com",
            password="rotatepass123",
            full_name="Rotate User",
            tenant_id=self.test_tenant,
        )
        user = register_user(user_in, self.db)
        refresh_token = create_refresh_token(user_id=user.id, tenant_id=user.tenant_id, db=self.db)

        # Rotate token
        new_acc, new_ref, _ = rotate_refresh_token(refresh_token, self.db)

        self.assertNotEqual(refresh_token, new_ref)
        self.assertIsInstance(new_acc, str)

        # Attempt to reuse the old refresh token (should fail)
        with self.assertRaises(Exception):
            rotate_refresh_token(refresh_token, self.db)

    def test_token_revocation_on_logout(self):
        user_in = UserCreate(
            email="logout@example.com",
            password="logoutpass123",
            full_name="Logout User",
            tenant_id=self.test_tenant,
        )
        user = register_user(user_in, self.db)
        refresh_token = create_refresh_token(user_id=user.id, tenant_id=user.tenant_id, db=self.db)

        # Revoke
        success = revoke_user_refresh_token(refresh_token, self.db)
        self.assertTrue(success)

        # Attempt to rotate revoked token (should fail)
        with self.assertRaises(Exception):
            rotate_refresh_token(refresh_token, self.db)


if __name__ == "__main__":
    unittest.main()
