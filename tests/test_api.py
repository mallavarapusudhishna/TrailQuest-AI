import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.gemma_service import OllamaConnectionError
from backend.app.services.quest_repository import quest_repo
from backend.app.services.serpapi_service import SerpApiError

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["storage"]["mode"] in ("mongodb", "in_memory")
    assert "durable" in body["storage"]


def test_frontend_assets_served():
    index = client.get("/")
    assert index.status_code == 200
    assert "TrailQuest" in index.text
    assert client.get("/script.js").status_code == 200
    assert client.get("/style.css").status_code == 200


def test_invalid_request_validation():
    response = client.post(
        "/generate-quest",
        json={
            "location": "A",
            "available_time": 0,
            "activity": "walking",
            "difficulty": "easy",
        },
    )
    assert response.status_code == 422


def test_invalid_request_time_too_long():
    response = client.post(
        "/generate-quest",
        json={
            "location": "Chennai",
            "available_time": 200,
            "activity": "walking",
            "difficulty": "easy",
        },
    )
    assert response.status_code == 422


@patch("backend.app.main.generate_user_quest", new_callable=AsyncMock)
def test_generate_quest_success(mock_gen):
    mock_gen.return_value = {
        "title": "Test Quest",
        "location": "Test Park",
        "address": "123 Park Rd",
        "estimated_duration": 60,
        "difficulty": "easy",
        "description": "A test quest.",
        "objectives": ["Walk 1 km", "Find a bench", "Breathe deeply"],
        "safety_note": "Stay safe",
        "_selected_location": {"name": "Test Park", "address": "123 Park Rd"},
    }

    response = client.post(
        "/generate-quest",
        json={
            "location": "Chennai",
            "available_time": 60,
            "activity": "walking",
            "difficulty": "easy",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Quest"
    assert "id" in data


@patch("backend.app.main.generate_user_quest", new_callable=AsyncMock)
def test_no_locations_found(mock_gen):
    mock_gen.side_effect = ValueError("No real outdoor locations found for 'Nowhere'.")
    response = client.post(
        "/generate-quest",
        json={
            "location": "Nowhere",
            "available_time": 60,
            "activity": "walking",
            "difficulty": "easy",
        },
    )
    assert response.status_code == 404


@patch("backend.app.main.generate_user_quest", new_callable=AsyncMock)
def test_serpapi_key_missing(mock_gen):
    mock_gen.side_effect = ValueError("SERPAPI_API_KEY is not configured.")
    response = client.post(
        "/generate-quest",
        json={
            "location": "Chennai",
            "available_time": 60,
            "activity": "walking",
            "difficulty": "easy",
        },
    )
    assert response.status_code == 500
    assert "not configured" in response.json()["detail"].lower()


@patch("backend.app.services.quest_service.search_outdoor_locations", new_callable=AsyncMock)
def test_serpapi_timeout(mock_search):
    mock_search.side_effect = SerpApiError("Location search timed out.")
    response = client.post(
        "/generate-quest",
        json={
            "location": "Chennai",
            "available_time": 60,
            "activity": "walking",
            "difficulty": "easy",
        },
    )
    assert response.status_code == 502
    assert "timed out" in response.json()["detail"].lower()


@patch("backend.app.services.quest_service.search_outdoor_locations", new_callable=AsyncMock)
def test_serpapi_failure(mock_search):
    mock_search.side_effect = SerpApiError("fail")
    response = client.post(
        "/generate-quest",
        json={
            "location": "Chennai",
            "available_time": 60,
            "activity": "walking",
            "difficulty": "easy",
        },
    )
    assert response.status_code == 502


@patch("backend.app.services.quest_service.search_outdoor_locations", new_callable=AsyncMock)
def test_serpapi_empty_results(mock_search):
    mock_search.return_value = []
    response = client.post(
        "/generate-quest",
        json={
            "location": "Nowhere",
            "available_time": 60,
            "activity": "walking",
            "difficulty": "easy",
        },
    )
    assert response.status_code == 404
    assert "No real outdoor locations found" in response.json()["detail"]


@patch("backend.app.services.quest_service.generate_quest", new_callable=AsyncMock)
@patch("backend.app.services.quest_service.search_outdoor_locations", new_callable=AsyncMock)
def test_ollama_model_not_found(mock_search, mock_gemma):
    from backend.app.services.gemma_service import OllamaModelNotFoundError

    mock_search.return_value = [
        {"name": "Real Park", "address": "1 Main St", "rating": 4.5, "type": "Park"}
    ]
    mock_gemma.side_effect = OllamaModelNotFoundError("Model missing")
    response = client.post(
        "/generate-quest",
        json={
            "location": "Chennai",
            "available_time": 60,
            "activity": "walking",
            "difficulty": "easy",
        },
    )
    assert response.status_code == 503
    assert "model" in response.json()["detail"].lower()


@patch("backend.app.main.QUEST_GENERATE_TIMEOUT_SECONDS", 0.001)
@patch("backend.app.main.generate_user_quest", new_callable=AsyncMock)
def test_generate_quest_pipeline_timeout(mock_gen):
    async def slow_generate(*_args, **_kwargs):
        await asyncio.sleep(0.05)
        return {
            "title": "Late Quest",
            "location": "Park",
            "estimated_duration": 60,
            "difficulty": "easy",
            "description": "D",
            "objectives": ["a", "b", "c"],
            "safety_note": "S",
            "_selected_location": {"name": "Park"},
        }

    mock_gen.side_effect = slow_generate
    response = client.post(
        "/generate-quest",
        json={
            "location": "Chennai",
            "available_time": 60,
            "activity": "walking",
            "difficulty": "easy",
        },
    )
    assert response.status_code == 504


@patch("backend.app.services.quest_service.generate_quest", new_callable=AsyncMock)
@patch("backend.app.services.quest_service.search_outdoor_locations", new_callable=AsyncMock)
def test_ollama_connection_failure(mock_search, mock_gemma):
    mock_search.return_value = [
        {
            "name": "Real Park",
            "address": "1 Main St",
            "rating": 4.5,
            "type": "Park",
        }
    ]
    mock_gemma.side_effect = OllamaConnectionError("Ollama down")
    response = client.post(
        "/generate-quest",
        json={
            "location": "Chennai",
            "available_time": 60,
            "activity": "walking",
            "difficulty": "easy",
        },
    )
    assert response.status_code == 503


@patch("backend.app.services.quest_service.generate_quest", new_callable=AsyncMock)
@patch("backend.app.services.quest_service.search_outdoor_locations", new_callable=AsyncMock)
def test_invalid_gemma_json(mock_search, mock_gemma):
    mock_search.return_value = [
        {"name": "Real Park", "address": "1 Main St", "rating": 4.5, "type": "Park"}
    ]
    mock_gemma.return_value = "Sorry, I cannot format JSON today."
    response = client.post(
        "/generate-quest",
        json={
            "location": "Chennai",
            "available_time": 60,
            "activity": "walking",
            "difficulty": "easy",
        },
    )
    assert response.status_code == 502
    assert "invalid JSON" in response.json()["detail"]


@patch("backend.app.services.quest_service.generate_quest", new_callable=AsyncMock)
@patch("backend.app.services.quest_service.search_outdoor_locations", new_callable=AsyncMock)
def test_invented_location_rejected(mock_search, mock_gemma):
    mock_search.return_value = [
        {"name": "Real Park", "address": "1 Main St", "rating": 4.5, "type": "Park"}
    ]
    mock_gemma.return_value = """
    {
      "title": "Fake",
      "location": "Imaginary Gardens",
      "description": "A quest",
      "objectives": ["A", "B", "C"],
      "safety_note": "Hydrate",
      "estimated_duration": 60,
      "difficulty": "easy"
    }
    """
    response = client.post(
        "/generate-quest",
        json={
            "location": "Chennai",
            "available_time": 60,
            "activity": "walking",
            "difficulty": "easy",
        },
    )
    assert response.status_code == 502
    assert "search results" in response.json()["detail"]


def test_get_quest_by_id():
    qid = asyncio.run(
        quest_repo.save_quest(
            user_preferences={"location": "Chennai"},
            selected_location={"name": "Park A"},
            quest_data={
                "title": "Quest A",
                "location": "Park A",
                "estimated_duration": 60,
                "difficulty": "easy",
                "description": "Walk A",
                "objectives": ["Obj 1", "Obj 2", "Obj 3"],
                "safety_note": "Safe",
            },
        )
    )
    res = client.get(f"/quests/{qid}")
    assert res.status_code == 200
    assert res.json()["quest"]["title"] == "Quest A"


def test_missing_quest_returns_404():
    res = client.get("/quests/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404


@patch("backend.app.main.quest_repo.save_quest", new_callable=AsyncMock)
@patch("backend.app.main.generate_user_quest", new_callable=AsyncMock)
def test_database_error_on_save(mock_gen, mock_save):
    mock_gen.return_value = {
        "title": "Test Quest",
        "location": "Test Park",
        "estimated_duration": 60,
        "difficulty": "easy",
        "description": "A test quest.",
        "objectives": ["A", "B", "C"],
        "safety_note": "Stay safe",
        "_selected_location": {"name": "Test Park"},
    }
    mock_save.side_effect = RuntimeError("db down")
    response = client.post(
        "/generate-quest",
        json={
            "location": "Chennai",
            "available_time": 60,
            "activity": "walking",
            "difficulty": "easy",
        },
    )
    assert response.status_code == 500


def test_complete_statuses_and_retrieval():
    qid1 = asyncio.run(
        quest_repo.save_quest(
            user_preferences={"location": "Chennai"},
            selected_location={"name": "Park A"},
            quest_data={
                "title": "Quest A",
                "location": "Park A",
                "estimated_duration": 60,
                "difficulty": "easy",
                "description": "Walk A",
                "objectives": ["Obj 1", "Obj 2", "Obj 3"],
                "safety_note": "Safe",
            },
        )
    )

    res1 = client.post(
        f"/quests/{qid1}/complete",
        json={"status": "completed", "reflection": "Great outdoor experience."},
    )
    assert res1.status_code == 200
    assert res1.json()["completion_status"] == "completed"
    assert res1.json()["reflection"] == "Great outdoor experience."
    assert res1.json()["completed_at"] is not None
    assert res1.json()["quest"]["title"] == "Quest A"

    qid2 = asyncio.run(
        quest_repo.save_quest(
            user_preferences={"location": "Chennai"},
            selected_location={"name": "Park B"},
            quest_data={
                "title": "Quest B",
                "location": "Park B",
                "estimated_duration": 45,
                "difficulty": "medium",
                "description": "Walk B",
                "objectives": ["Obj 1", "Obj 2", "Obj 3"],
                "safety_note": "Safe",
            },
        )
    )

    res2 = client.post(
        f"/quests/{qid2}/complete",
        json={
            "status": "partially_completed",
            "reflection": "Completed most of objectives.",
        },
    )
    assert res2.status_code == 200
    assert res2.json()["completion_status"] == "partially_completed"

    qid3 = asyncio.run(
        quest_repo.save_quest(
            user_preferences={"location": "Chennai"},
            selected_location={"name": "Park C"},
            quest_data={
                "title": "Quest C",
                "location": "Park C",
                "estimated_duration": 30,
                "difficulty": "easy",
                "description": "Walk C",
                "objectives": ["Obj 1", "Obj 2", "Obj 3"],
                "safety_note": "Safe",
            },
        )
    )

    res3 = client.post(
        f"/quests/{qid3}/complete",
        json={
            "status": "not_completed",
            "reflection": "Weather changed.",
        },
    )
    assert res3.status_code == 200
    assert res3.json()["completion_status"] == "not_completed"


def test_completion_error_handling():
    res_404 = client.post(
        "/quests/nonexistent-id-12345/complete",
        json={"status": "completed", "reflection": "Test"},
    )
    assert res_404.status_code == 404

    res_422 = client.post(
        "/quests/some-id/complete",
        json={"status": "invalid_status_value"},
    )
    assert res_422.status_code == 422
