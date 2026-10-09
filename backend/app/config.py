import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=True)

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "trailquest_db")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")

SERPAPI_TIMEOUT_SECONDS = float(os.getenv("SERPAPI_TIMEOUT_SECONDS", "30"))
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))
QUEST_GENERATE_TIMEOUT_SECONDS = float(
    os.getenv("QUEST_GENERATE_TIMEOUT_SECONDS", "240")
)
