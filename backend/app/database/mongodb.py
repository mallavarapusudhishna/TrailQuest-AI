from typing import Optional, Any

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    HAS_MOTOR = True
except ImportError:
    AsyncIOMotorClient = None
    HAS_MOTOR = False

from backend.app.config import MONGODB_DB_NAME, MONGODB_URI


def get_database() -> Optional[Any]:
    """Return MongoDB database handle when MONGODB_URI and Motor are available."""
    if not MONGODB_URI or not HAS_MOTOR:
        return None

    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        return client[MONGODB_DB_NAME]
    except Exception:
        return None
