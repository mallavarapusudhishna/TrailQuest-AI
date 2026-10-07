import os
from typing import List
from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx

from backend.app.models.quest import (
    QuestCompletionRequest,
    QuestDetailResponse,
    QuestGenerateRequest,
    QuestResponse,
)
from backend.app.services.gemma_service import generate_quest
from backend.app.services.quest_repository import quest_repo
from backend.app.services.quest_service import generate_user_quest
from backend.app.services.serpapi_service import search_outdoor_locations


app = FastAPI(
    title="TrailQuest AI",
    description="AI-powered outdoor quest generator",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/generate-quest", response_model=QuestResponse)
async def generate_quest_endpoint(request: QuestGenerateRequest):
    try:
        quest_data = await generate_user_quest(
            location=request.location,
            available_time=request.available_time,
            activity=request.activity,
            difficulty=request.difficulty,
            interests=request.interests or "",
        )

        user_prefs = request.model_dump()
        selected_location = quest_data.pop("_selected_location", {})

        # Save to database repository
        quest_id = await quest_repo.save_quest(
            user_preferences=user_prefs,
            selected_location=selected_location,
            quest_data=quest_data,
        )
        quest_data["id"] = quest_id
        quest_data["quest_id"] = quest_id

        return quest_data

    except ValueError as e:
        err_msg = str(e)
        if "SERPAPI_API_KEY" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Location search service is not configured properly.",
            )
        elif "No real outdoor locations found" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=err_msg,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg,
            )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service (Ollama) or search service is unreachable. Please ensure Ollama is running locally.",
        )
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="External service request failed.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating your quest.",
        )


@app.post("/quests/{quest_id}/complete", response_model=QuestDetailResponse)
async def complete_quest_endpoint(
    quest_id: str, request: QuestCompletionRequest
):
    updated = await quest_repo.update_completion(
        quest_id=quest_id,
        status=request.status,
        reflection=request.reflection,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quest with ID '{quest_id}' not found.",
        )
    return updated


@app.get("/quests/{quest_id}", response_model=QuestDetailResponse)
async def get_quest_endpoint(quest_id: str):
    quest_record = await quest_repo.get_quest_by_id(quest_id)
    if not quest_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quest with ID '{quest_id}' not found.",
        )
    return quest_record


@app.get("/quests", response_model=List[QuestDetailResponse])
async def list_quests_endpoint(limit: int = 10):
    quests = await quest_repo.get_recent_quests(limit=limit)

    return quests


@app.post("/test-gemma")
async def test_gemma(prompt: str):
    result = await generate_quest(prompt)
    return {"response": result}


@app.get("/test-serpapi")
async def test_serpapi(location: str = "Chennai"):
    locations = await search_outdoor_locations(location)
    return {"location": location, "results": locations}


# Serve static frontend files
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")