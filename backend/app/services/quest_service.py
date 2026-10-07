import json
import re

from backend.app.services.gemma_service import generate_quest
from backend.app.services.serpapi_service import search_outdoor_locations


def _extract_json(text: str) -> dict:
    """Attempts to parse JSON from response string, supporting markdown block wrapping."""
    cleaned = text.strip()
    # Remove markdown backticks if present
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: search for first '{' and last '}'
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        raise ValueError("Failed to parse valid JSON from model response.")


async def generate_user_quest(
    location: str,
    available_time: int,
    activity: str,
    difficulty: str,
    interests: str = "",
) -> dict:
    """Orchestrates location search and quest generation using Gemma."""
    locations = await search_outdoor_locations(location)
    if not locations:
        raise ValueError(f"No real outdoor locations found for '{location}'.")

    locations_formatted = "\n".join(
        [
            f"- {loc.get('name', 'Unknown')} (Address: {loc.get('address', 'N/A')}, Type: {loc.get('type', 'N/A')})"
            for loc in locations
        ]
    )

    prompt = f"""You are an outdoor adventure guide. Create ONE outdoor quest for a user based STRICTLY on the real locations provided.

CRITICAL INSTRUCTIONS:
- You MUST select the primary location from the SUPPLIED REAL LOCATIONS list below.
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
    except ValueError:
        # Graceful fallback if JSON parsing fails completely
        first_loc = locations[0].get("name", location)
        quest_data = {
            "title": f"{activity.title()} Quest at {first_loc}",
            "location": first_loc,
            "estimated_duration": available_time,
            "difficulty": difficulty,
            "description": f"Enjoy a {available_time}-minute {activity} session at {first_loc}.",
            "objectives": [
                f"Arrive at {first_loc}",
                f"Spend {available_time} minutes engaging in {activity}",
                "Take in your surroundings safely",
            ],
            "safety_note": "Stay hydrated and be aware of your environment.",
        }

    # Ensure required fields exist and match location address
    quest_data.setdefault("title", "Outdoor Quest")
    chosen_loc_name = quest_data.get("location", locations[0].get("name", location))
    quest_data["location"] = chosen_loc_name
    quest_data.setdefault("estimated_duration", available_time)
    quest_data.setdefault("difficulty", difficulty)
    quest_data.setdefault("description", "Outdoor activity quest.")
    quest_data.setdefault(
        "objectives", ["Explore the area", "Complete activity", "Return safely"]
    )
    quest_data.setdefault(
        "safety_note", "Stay hydrated and follow local regulations."
    )

    # Attach matched location details and address from SerpApi locations
    selected_loc_obj = locations[0]
    matched = False
    for loc in locations:
        if loc.get("name") and (loc.get("name").lower() in chosen_loc_name.lower() or chosen_loc_name.lower() in loc.get("name").lower()):
            selected_loc_obj = loc
            matched = True
            break

    if not matched and locations:
        # Enforce SerpApi location if model returned an unlisted location
        chosen_loc_name = locations[0].get("name", location)
        quest_data["location"] = chosen_loc_name
        selected_loc_obj = locations[0]

    quest_data["address"] = selected_loc_obj.get("address")
    quest_data["_selected_location"] = {
        "name": selected_loc_obj.get("name"),
        "address": selected_loc_obj.get("address"),
        "rating": selected_loc_obj.get("rating"),
        "type": selected_loc_obj.get("type"),
    }

    return quest_data



