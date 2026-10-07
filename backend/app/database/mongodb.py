from typing import Optional, Any

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    HAS_MOTOR = True
except ImportError:
    AsyncIOMotorClient = None
    HAS_MOTOR = False

from backend.app.config import MONGODB_URI


def get_database() -> Optional[Any]:
    """Establishes and returns a MongoDB database connection if MONGODB_URI is provided."""
    if not MONGODB_URI or not HAS_MOTOR:
        return None

    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        return client.get_default_database("trailquest_db")
    except Exception:
        return None
