import os

from dotenv import load_dotenv


load_dotenv()


SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")