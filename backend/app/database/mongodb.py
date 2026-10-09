from typing import Any, Optional

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    HAS_MOTOR = True
except ImportError:
    AsyncIOMotorClient = None
    HAS_MOTOR = False

from backend.app.config import MONGODB_DB_NAME, MONGODB_URI

_client: Optional[Any] = None


def is_mongodb_configured() -> bool:
    """True when MONGODB_URI is set (value is never exposed)."""
    return bool(MONGODB_URI and MONGODB_URI.strip())


def get_database() -> Optional[Any]:
    """Return MongoDB database handle when URI and Motor are available."""
    global _client

    if not is_mongodb_configured() or not HAS_MOTOR:
        return None

    try:
        if _client is None:
            _client = AsyncIOMotorClient(MONGODB_URI)
        return _client[MONGODB_DB_NAME]
    except Exception:
        return None


async def ping_mongodb() -> tuple[bool, Optional[str]]:
    """
    Verify Atlas/cluster connectivity without logging credentials.
    Returns (success, error_kind) where error_kind is a short label or None.
    """
    db = get_database()
    if db is None:
        if not is_mongodb_configured():
            return False, "not_configured"
        if not HAS_MOTOR:
            return False, "motor_unavailable"
        return False, "client_init_failed"

    try:
        await db.command("ping")
        return True, None
    except Exception:
        return False, "ping_failed"
