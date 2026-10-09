import asyncio
import logging
import os
import time
from typing import List

import httpx
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse

from backend.app.config import QUEST_GENERATE_TIMEOUT_SECONDS
from backend.app.models.quest import (
    QuestCompletionRequest,
    QuestDetailResponse,
    QuestGenerateRequest,
    QuestResponse,
)
from backend.app.services.gemma_service import (
    OllamaConnectionError,
    OllamaModelNotFoundError,
    generate_quest,
)
from backend.app.services.quest_repository import quest_repo
from backend.app.services.quest_service import generate_user_quest
from backend.app.services.serpapi_service import SerpApiError, search_outdoor_locations
from backend.app.services.storage_status import get_storage_status

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("trailquest")

app = FastAPI(
    title="TrailQuest AI",
    description="AI-powered outdoor quest generator",
    version="1.0.0",
)

frontend_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
)


@app.get("/health")
async def health():
    storage = await get_storage_status()
    return {
        "status": "healthy",
        "storage": storage,
    }


@app.post("/generate-quest", response_model=QuestResponse)
async def generate_quest_endpoint(request: QuestGenerateRequest):
    started = time.perf_counter()
    logger.info(
        "Quest request received location=%s activity=%s difficulty=%s minutes=%s",
        request.location,
        request.activity,
        request.difficulty,
        request.available_time,
    )

    try:
        logger.info("Location search started")
        t0 = time.perf_counter()

        async def _generate_pipeline() -> dict:
            quest_data = await generate_user_quest(
                location=request.location,
                available_time=request.available_time,
                activity=request.activity,
                difficulty=request.difficulty,
                interests=request.interests or "",
            )
            logger.info(
                "AI generation and validation completed in %.2fs",
                time.perf_counter() - t0,
            )

            user_prefs = request.model_dump()
            selected_location = quest_data.pop("_selected_location", {})

            logger.info("MongoDB persistence started")
            t1 = time.perf_counter()
            quest_id = await quest_repo.save_quest(
                user_preferences=user_prefs,
                selected_location=selected_location,
                quest_data=quest_data,
            )
            logger.info(
                "MongoDB persistence completed in %.2fs backend=%s quest_id=%s",
                time.perf_counter() - t1,
                quest_repo.last_write_backend,
                quest_id,
            )

            quest_data["id"] = quest_id
            quest_data["quest_id"] = quest_id
            return quest_data

        quest_data = await asyncio.wait_for(
            _generate_pipeline(),
            timeout=QUEST_GENERATE_TIMEOUT_SECONDS,
        )

        logger.info(
            "Response returned total_elapsed=%.2fs quest_id=%s",
            time.perf_counter() - started,
            quest_data.get("quest_id"),
        )
        return quest_data

    except asyncio.TimeoutError:
        logger.error(
            "Quest generation timed out after %.2fs",
            time.perf_counter() - started,
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=(
                "Quest generation took too long. Ollama may still be loading the model—"
                "wait a moment and try again."
            ),
        )
    except ValueError as e:
        err_msg = str(e)
        if "SERPAPI_API_KEY" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Location search service is not configured properly.",
            )
        if "No real outdoor locations found" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=err_msg,
            )
        if "not in the search results" in err_msg or "invalid JSON" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=err_msg,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg,
        )
    except OllamaModelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except OllamaConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except SerpApiError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "AI service (Ollama) or search service is unreachable. "
                "Please ensure Ollama is running locally."
            ),
        )
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="External service request failed.",
        )
    except Exception:
        logger.exception("Unexpected error during quest generation")
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
    logger.info(
        "Quest completion saved quest_id=%s status=%s backend=%s",
        quest_id,
        request.status,
        quest_repo.last_write_backend,
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
    if limit < 1 or limit > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 50.",
        )
    return await quest_repo.get_recent_quests(limit=limit)


@app.post("/test-gemma")
async def test_gemma(prompt: str):
    try:
        result = await generate_quest(prompt)
    except OllamaConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"response": result}


@app.get("/test-serpapi")
async def test_serpapi(location: str = "Chennai"):
    try:
        locations = await search_outdoor_locations(location)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except SerpApiError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"location": location, "results": locations}


def _frontend_file(name: str) -> str:
    return os.path.join(frontend_path, name)


@app.get("/")
async def serve_index():
    return FileResponse(_frontend_file("index.html"))


@app.get("/style.css")
async def serve_css():
    return FileResponse(_frontend_file("style.css"), media_type="text/css")


@app.get("/script.js")
async def serve_js():
    return FileResponse(_frontend_file("script.js"), media_type="application/javascript")
