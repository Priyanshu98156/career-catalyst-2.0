import uuid
from datetime import datetime, timezone
from backend.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)
