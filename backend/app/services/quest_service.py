import json
import re
from typing import Any

from backend.app.services.gemma_service import generate_quest
from backend.app.services.serpapi_service import search_outdoor_locations


def _extract_json(text: str) -> dict:
    """Parse JSON from model response, including optional markdown fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        raise ValueError("Failed to parse valid JSON from model response.")


def _normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _match_location(
    chosen_name: str, locations: list[dict]
) -> tuple[dict | None, bool]:
    """Return (matched_location, exact_or_fuzzy_match). None if no match."""
    if not locations or not chosen_name:
        return None, False

    normalized_chosen = _normalize_name(chosen_name)
    for loc in locations:
        name = loc.get("name")
        if not name:
            continue
        normalized_name = _normalize_name(name)
        if normalized_name == normalized_chosen:
            return loc, True
        if normalized_name in normalized_chosen or normalized_chosen in normalized_name:
            return loc, True

    return None, False


def _validate_quest_payload(
    quest_data: dict,
    locations: list[dict],
    available_time: int,
    difficulty: str,
) -> tuple[dict, dict]:
    """
    Validate model output and bind the quest to a real SerpApi location.
    Returns (quest_data, selected_location_dict).
    """
    required_fields = ("title", "location", "description", "objectives", "safety_note")
    for field in required_fields:
        if not quest_data.get(field):
            raise ValueError(f"Generated quest is missing required field: {field}")

    objectives = quest_data.get("objectives")
    if not isinstance(objectives, list):
        raise ValueError("Generated quest objectives must be a list.")
    objectives = [str(o).strip() for o in objectives if str(o).strip()]
    if len(objectives) < 3 or len(objectives) > 5:
        raise ValueError("Generated quest must include 3 to 5 objectives.")

    chosen_name = str(quest_data["location"]).strip()
    matched_loc, was_matched = _match_location(chosen_name, locations)
    if not was_matched or matched_loc is None:
        raise ValueError(
            "Generated quest selected a location that is not in the search results."
        )

    duration = quest_data.get("estimated_duration", available_time)
    try:
        duration = int(duration)
    except (TypeError, ValueError):
        duration = available_time

    validated = {
        "title": str(quest_data["title"]).strip(),
        "location": matched_loc["name"],
        "address": matched_loc.get("address"),
        "estimated_duration": duration,
        "difficulty": str(quest_data.get("difficulty", difficulty)).strip(),
        "description": str(quest_data["description"]).strip(),
        "objectives": objectives,
        "safety_note": str(quest_data["safety_note"]).strip(),
    }

    selected_location = {
        "name": matched_loc.get("name"),
        "address": matched_loc.get("address"),
        "rating": matched_loc.get("rating"),
        "type": matched_loc.get("type"),
        "source_url": matched_loc.get("source_url"),
    }

    return validated, selected_location


async def generate_user_quest(
    location: str,
    available_time: int,
    activity: str,
    difficulty: str,
    interests: str = "",
) -> dict:
    """Orchestrates location search and quest generation using Ollama."""
    locations = await search_outdoor_locations(location)
    if not locations:
        raise ValueError(f"No real outdoor locations found for '{location}'.")

    locations_formatted = "\n".join(
        [
            f"- {loc.get('name', 'Unknown')} (Address: {loc.get('address') or 'N/A'}, "
            f"Type: {loc.get('type') or 'N/A'})"
            for loc in locations
        ]
    )

    prompt = f"""You are an outdoor adventure guide. Create ONE outdoor quest for a user based STRICTLY on the real locations provided.

CRITICAL INSTRUCTIONS:
- You MUST select the primary location from the SUPPLIED REAL LOCATIONS list below.
- Use the EXACT location name from the list for the "location" field.
- Do NOT invent, fabricate, or hallucinate any parks, trails, gardens, lakes, or outdoor locations.
- Do NOT use any location outside the supplied list.
- Return ONLY a single valid JSON object without any additional conversational text or explanation.

USER PREFERENCES:
- Target Area: {location}
- Available Time: {available_time} minutes
- Preferred Activity: {activity}
- Difficulty Level: {difficulty}
- Interests: {interests if interests else 'General outdoor exploration'}

SUPPLIED REAL LOCATIONS (Choose ONE location from this list):
{locations_formatted}

JSON OUTPUT FORMAT:
{{
  "title": "A short engaging quest title",
  "location": "Exact name of chosen location from the supplied list",
  "estimated_duration": {available_time},
  "difficulty": "{difficulty}",
  "description": "A short 2-3 sentence description of the quest.",
  "objectives": [
    "Objective 1",
    "Objective 2",
    "Objective 3"
  ],
  "safety_note": "A practical safety tip for this activity."
}}
"""

    raw_response = await generate_quest(prompt)

    try:
        quest_data = _extract_json(raw_response)
    except ValueError as exc:
        raise ValueError("AI service returned invalid JSON for the quest.") from exc

    if not isinstance(quest_data, dict):
        raise ValueError("AI service returned an invalid quest structure.")

    validated, selected_location = _validate_quest_payload(
        quest_data, locations, available_time, difficulty
    )
    validated["_selected_location"] = selected_location
    return validated
