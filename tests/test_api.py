import asyncio
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.quest_repository import quest_repo

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


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


@patch("backend.app.main.generate_user_quest")
def test_generate_quest_success(mock_gen):
    mock_gen.return_value = {
        "title": "Test Quest",
        "location": "Test Park",
        "estimated_duration": 60,
        "difficulty": "easy",
        "description": "A test quest.",
        "objectives": ["Walk 1 km"],
        "safety_note": "Stay safe",
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


def test_complete_statuses_and_retrieval():
    # 1. Test 'completed'
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
                "objectives": ["Obj 1"],
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

    # 2. Test 'partially_completed'
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
                "objectives": ["Obj 1"],
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

    # 3. Test 'not_completed'
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
                "objectives": ["Obj 1"],
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
    # Nonexistent quest ID (404)
    res_404 = client.post(
        "/quests/nonexistent-id-12345/complete",
        json={"status": "completed", "reflection": "Test"},
    )
    assert res_404.status_code == 404

    # Invalid status value (422)
    res_422 = client.post(
        "/quests/some-id/complete",
        json={"status": "invalid_status_value"},
    )
    assert res_422.status_code == 422
