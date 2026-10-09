import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.quest_repository import QuestRepository, _memory_db
from backend.app.services.storage_status import get_storage_status


client = TestClient(app)


def test_storage_status_not_configured():
    with patch("backend.app.services.storage_status.is_mongodb_configured", return_value=False):
        status = asyncio.run(get_storage_status())
    assert status["mode"] == "in_memory"
    assert status["mongodb_configured"] is False
    assert status["durable"] is False


def test_storage_status_mongodb_reachable():
    with patch("backend.app.services.storage_status.is_mongodb_configured", return_value=True):
        with patch(
            "backend.app.services.storage_status.ping_mongodb",
            new_callable=AsyncMock,
            return_value=(True, None),
        ):
            status = asyncio.run(get_storage_status())
    assert status["mode"] == "mongodb"
    assert status["durable"] is True


def test_storage_status_uri_set_but_unreachable():
    with patch("backend.app.services.storage_status.is_mongodb_configured", return_value=True):
        with patch(
            "backend.app.services.storage_status.ping_mongodb",
            new_callable=AsyncMock,
            return_value=(False, "ping_failed"),
        ):
            status = asyncio.run(get_storage_status())
    assert status["mode"] == "in_memory"
    assert status["mongodb_configured"] is True
    assert status["mongodb_reachable"] is False


def test_health_includes_storage_block():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "storage" in body
    assert "mode" in body["storage"]
    assert "durable" in body["storage"]
    assert "message" in body["storage"]


def test_repository_uses_mongodb_on_successful_insert():
    _memory_db.clear()
    repo = QuestRepository()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.insert_one = AsyncMock(return_value=None)
    mock_db.quests = mock_collection
    repo.db = mock_db

    qid = asyncio.run(
        repo.save_quest(
            user_preferences={"location": "Chennai"},
            selected_location={"name": "Park"},
            quest_data={
                "title": "T",
                "location": "Park",
                "estimated_duration": 30,
                "difficulty": "easy",
                "description": "D",
                "objectives": ["a", "b", "c"],
                "safety_note": "S",
            },
        )
    )

    assert qid
    mock_collection.insert_one.assert_awaited_once()
    assert repo.last_write_backend == "mongodb"
    assert qid not in _memory_db


def test_repository_falls_back_when_insert_fails():
    _memory_db.clear()
    repo = QuestRepository()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.insert_one = AsyncMock(side_effect=RuntimeError("db error"))
    mock_db.quests = mock_collection
    repo.db = mock_db

    qid = asyncio.run(
        repo.save_quest(
            user_preferences={"location": "Chennai"},
            selected_location={"name": "Park"},
            quest_data={
                "title": "T",
                "location": "Park",
                "estimated_duration": 30,
                "difficulty": "easy",
                "description": "D",
                "objectives": ["a", "b", "c"],
                "safety_note": "S",
            },
        )
    )

    assert qid in _memory_db
    assert repo.last_write_backend == "in_memory"


def test_repository_mongodb_completion_update():
    _memory_db.clear()
    repo = QuestRepository()
    quest_id = "test-quest-uuid"
    updated_doc = {
        "_id": quest_id,
        "quest_id": quest_id,
        "completion_status": "completed",
        "reflection": "Done",
        "quest": {"title": "T"},
        "user_preferences": {},
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one_and_update = AsyncMock(return_value=updated_doc)
    mock_db.quests = mock_collection
    repo.db = mock_db

    result = asyncio.run(
        repo.update_completion(quest_id, "completed", reflection="Done")
    )
    assert result is not None
    assert result["completion_status"] == "completed"
    mock_collection.find_one_and_update.assert_awaited_once()
