import pytest

from backend.app.services.quest_service import (
    _extract_json,
    _match_location,
    _validate_quest_payload,
)


LOCATIONS = [
    {
        "name": "Guindy National Park",
        "address": "Chennai, Tamil Nadu",
        "rating": 4.2,
        "type": "National park",
    },
    {
        "name": "Semmozhi Poonga",
        "address": "Cathedral Road, Chennai",
        "rating": 4.0,
        "type": "Botanical garden",
    },
]


def test_extract_json_plain():
    data = _extract_json('{"title": "Test", "location": "Park"}')
    assert data["title"] == "Test"


def test_extract_json_markdown_fence():
    raw = '```json\n{"title": "Quest", "location": "Park"}\n```'
    data = _extract_json(raw)
    assert data["title"] == "Quest"


def test_extract_json_invalid_raises():
    with pytest.raises(ValueError, match="Failed to parse"):
        _extract_json("not json at all")


def test_match_location_exact():
    loc, matched = _match_location("Guindy National Park", LOCATIONS)
    assert matched is True
    assert loc["name"] == "Guindy National Park"


def test_match_location_fuzzy_substring():
    loc, matched = _match_location("Guindy National", LOCATIONS)
    assert matched is True
    assert loc is not None


def test_match_location_invented_fails():
    loc, matched = _match_location("Imaginary Lake Trail", LOCATIONS)
    assert matched is False
    assert loc is None


def test_validate_quest_rejects_invented_location():
    quest = {
        "title": "Fake Quest",
        "location": "Totally Made Up Park",
        "description": "Desc",
        "objectives": ["A", "B", "C"],
        "safety_note": "Stay safe",
        "estimated_duration": 60,
        "difficulty": "easy",
    }
    with pytest.raises(ValueError, match="not in the search results"):
        _validate_quest_payload(quest, LOCATIONS, 60, "easy")


def test_validate_quest_accepts_valid_payload():
    quest = {
        "title": "Nature Walk",
        "location": "Guindy National Park",
        "description": "Explore greenery.",
        "objectives": ["Walk 20 min", "Photograph trees", "Rest by pond"],
        "safety_note": "Carry water.",
        "estimated_duration": 60,
        "difficulty": "Easy",
    }
    validated, selected = _validate_quest_payload(quest, LOCATIONS, 60, "easy")
    assert validated["location"] == "Guindy National Park"
    assert validated["address"] == "Chennai, Tamil Nadu"
    assert selected["name"] == "Guindy National Park"


def test_validate_quest_objectives_count():
    quest = {
        "title": "Short",
        "location": "Guindy National Park",
        "description": "Desc",
        "objectives": ["Only one"],
        "safety_note": "Safe",
    }
    with pytest.raises(ValueError, match="3 to 5 objectives"):
        _validate_quest_payload(quest, LOCATIONS, 60, "easy")
