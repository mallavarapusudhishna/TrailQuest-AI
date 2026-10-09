"""Local MongoDB connectivity check. Never prints MONGODB_URI."""
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv()

uri = (os.getenv("MONGODB_URI") or "").strip()


def main() -> int:
    print("uri_loaded", bool(uri))
    print("scheme_mongodb", uri.startswith("mongodb"))
    print("uses_srv", uri.startswith("mongodb+srv"))
    print("length", len(uri))

    try:
        import pymongo

        print("pymongo_version", pymongo.version)
    except ImportError:
        print("pymongo_version", None)
        return 1

    try:
        import motor  # noqa: F401

        print("motor_installed", True)
    except ImportError:
        print("motor_installed", False)
        return 1

    from backend.app.database.mongodb import ping_mongodb

    ok, error_kind = asyncio.run(ping_mongodb())
    print("ping_ok", ok)
    print("error_kind", error_kind)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
