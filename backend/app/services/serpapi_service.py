import httpx

from backend.app.config import SERPAPI_API_KEY


SERPAPI_URL = "https://serpapi.com/search.json"


async def search_outdoor_locations(location: str) -> list[dict]:
    if not SERPAPI_API_KEY:
        raise ValueError("SERPAPI_API_KEY is not configured.")

    params = {
        "engine": "google_maps",
        "q": f"outdoor parks gardens trails nature areas near {location}",
        "api_key": SERPAPI_API_KEY,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(SERPAPI_URL, params=params)
        response.raise_for_status()

        data = response.json()

    locations = []

    for place in data.get("local_results", [])[:5]:
        locations.append(
            {
                "name": place.get("title"),
                "address": place.get("address"),
                "rating": place.get("rating"),
                "type": place.get("type"),
            }
        )

    return locations