import httpx

from backend.app.config import SERPAPI_API_KEY, SERPAPI_TIMEOUT_SECONDS


SERPAPI_URL = "https://serpapi.com/search.json"


class SerpApiError(Exception):
    """Raised when SerpApi request fails."""


async def search_outdoor_locations(location: str) -> list[dict]:
    if not SERPAPI_API_KEY:
        raise ValueError("SERPAPI_API_KEY is not configured.")

    params = {
        "engine": "google_maps",
        "q": f"outdoor parks gardens trails nature areas near {location}",
        "api_key": SERPAPI_API_KEY,
    }

    timeout = httpx.Timeout(SERPAPI_TIMEOUT_SECONDS, connect=10.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(SERPAPI_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException as exc:
        raise SerpApiError("Location search timed out.") from exc
    except httpx.HTTPError as exc:
        raise SerpApiError("Location search request failed.") from exc

    locations = []

    for place in data.get("local_results", [])[:5]:
        name = place.get("title")
        if not name:
            continue
        locations.append(
            {
                "name": name,
                "address": place.get("address"),
                "rating": place.get("rating"),
                "type": place.get("type"),
                "source_url": place.get("link") or place.get("website"),
            }
        )

    return locations
