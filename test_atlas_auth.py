import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import OperationFailure

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)

uri = os.getenv("MONGODB_URI", "").strip()

if not uri:
    print("ERROR: MONGODB_URI not found in root .env")
    raise SystemExit(1)

print("URI loaded:", bool(uri))
print("Contains placeholder:", "<db_password>" in uri)

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=15000)
    print("Ping result:", client.admin.command("ping"))
    print("SUCCESS: Atlas authentication works!")
except OperationFailure as e:
    print("Authentication/operation error")
    print("MongoDB error code:", e.code)
    print("MongoDB error:", e.details.get("errmsg", "No detailed message"))
except Exception as e:
    print("Error type:", type(e).__name__)
    print("Error:", str(e)[:500])
finally:
    if "client" in locals():
        client.close()