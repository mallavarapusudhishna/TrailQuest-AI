import os

from dotenv import load_dotenv


load_dotenv()

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "trailquest_db")

OLLAMA_URL = os.getenv(
    "OLLAMA_URL", "http://127.0.0.1:11434/api/generate"
)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")
