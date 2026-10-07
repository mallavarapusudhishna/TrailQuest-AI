from fastapi import FastAPI
from pydantic import BaseModel

from backend.app.services.gemma_service import generate_quest
from backend.app.services.serpapi_service import search_outdoor_locations


app = FastAPI(
    title="TrailQuest AI",
    description="AI-powered outdoor quest generator",
    version="0.1.0",
)


class QuestRequest(BaseModel):
    prompt: str


@app.get("/")
def root():
    return {
        "message": "TrailQuest AI API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/test-gemma")
async def test_gemma(request: QuestRequest):
    result = await generate_quest(request.prompt)

    return {
        "response": result
    }

@app.get("/test-serpapi")
async def test_serpapi(location: str = "Chennai"):
    locations = await search_outdoor_locations(location)

    return {
        "location": location,
        "results": locations
    }