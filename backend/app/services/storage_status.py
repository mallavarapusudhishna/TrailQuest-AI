from backend.app.database.mongodb import is_mongodb_configured, ping_mongodb


async def get_storage_status() -> dict:
    """
    Describe whether quests are stored in MongoDB or in-memory fallback.
    Safe to expose via /health (no secrets).
    """
    if not is_mongodb_configured():
        return {
            "mode": "in_memory",
            "mongodb_configured": False,
            "mongodb_reachable": False,
            "durable": False,
            "message": (
                "MONGODB_URI is not set. Quests are kept in memory only and "
                "are lost when the server restarts."
            ),
        }

    reachable, error_kind = await ping_mongodb()
    if reachable:
        return {
            "mode": "mongodb",
            "mongodb_configured": True,
            "mongodb_reachable": True,
            "durable": True,
            "message": (
                "MongoDB Atlas is connected. Quests persist across server restarts."
            ),
        }

    return {
        "mode": "in_memory",
        "mongodb_configured": True,
        "mongodb_reachable": False,
        "durable": False,
        "message": (
            "MONGODB_URI is set but MongoDB is not reachable "
            f"({error_kind or 'unknown'}). Using in-memory fallback until connection works."
        ),
    }
