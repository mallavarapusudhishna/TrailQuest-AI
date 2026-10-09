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
            "mongodb_error_kind": "not_configured",
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
            "mongodb_error_kind": None,
            "message": (
                "MongoDB Atlas is connected. Quests persist across server restarts."
            ),
        }

    if error_kind == "authentication_failed":
        message = (
            "MONGODB_URI is set but Atlas authentication failed. "
            "Verify the database username and password in Atlas, and URL-encode "
            "special characters in the password inside the connection string. "
            "Using in-memory fallback until connection works."
        )
    elif error_kind == "server_selection_timeout":
        message = (
            "MONGODB_URI is set but the cluster could not be reached in time. "
            "Check Network Access in Atlas (allow your current IP). "
            "Using in-memory fallback until connection works."
        )
    else:
        message = (
            "MONGODB_URI is set but MongoDB is not reachable "
            f"({error_kind or 'unknown'}). Using in-memory fallback until connection works."
        )

    return {
        "mode": "in_memory",
        "mongodb_configured": True,
        "mongodb_reachable": False,
        "durable": False,
        "mongodb_error_kind": error_kind,
        "message": message,
    }
