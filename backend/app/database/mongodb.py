from typing import Any, Optional

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    HAS_MOTOR = True
except ImportError:
    AsyncIOMotorClient = None
    HAS_MOTOR = False

try:
    from pymongo.errors import ConfigurationError, OperationFailure, ServerSelectionTimeoutError
except ImportError:
    ConfigurationError = OperationFailure = ServerSelectionTimeoutError = Exception  # type: ignore

from backend.app.config import MONGODB_DB_NAME, MONGODB_URI

_client: Optional[Any] = None

_CLIENT_OPTIONS = {
    "serverSelectionTimeoutMS": 12000,
}


def _normalized_uri() -> Optional[str]:
    if not MONGODB_URI:
        return None
    cleaned = MONGODB_URI.strip()
    return cleaned or None


def is_mongodb_configured() -> bool:
    """True when MONGODB_URI is set (value is never exposed)."""
    return _normalized_uri() is not None


def _classify_connection_error(exc: BaseException) -> str:
    if isinstance(exc, OperationFailure):
        code = getattr(exc, "code", None)
        message = str(exc).lower()
        if code in (8000, 18) or "authentication failed" in message or "bad auth" in message:
            return "authentication_failed"
        return "operation_failed"
    if isinstance(exc, ServerSelectionTimeoutError):
        return "server_selection_timeout"
    if isinstance(exc, ConfigurationError):
        return "configuration_error"
    return "ping_failed"


def get_database() -> Optional[Any]:
    """Return MongoDB database handle when URI and Motor are available."""
    global _client

    uri = _normalized_uri()
    if uri is None or not HAS_MOTOR:
        return None

    try:
        if _client is None:
            _client = AsyncIOMotorClient(uri, **_CLIENT_OPTIONS)
        return _client[MONGODB_DB_NAME]
    except Exception:
        return None


async def ping_mongodb() -> tuple[bool, Optional[str]]:
    """
    Verify Atlas/cluster connectivity without logging credentials.
    Returns (success, error_kind) where error_kind is a short label or None.
    """
    uri = _normalized_uri()
    if uri is None:
        return False, "not_configured"
    if not HAS_MOTOR:
        return False, "motor_unavailable"

    db = get_database()
    if db is None:
        return False, "client_init_failed"

    try:
        await db.command("ping")
        return True, None
    except Exception as exc:
        return False, _classify_connection_error(exc)
