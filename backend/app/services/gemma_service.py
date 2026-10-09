import httpx

from backend.app.config import OLLAMA_MODEL, OLLAMA_URL


class OllamaConnectionError(Exception):
    """Raised when Ollama cannot be reached or returns an error."""


async def generate_quest(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.ConnectError as exc:
        raise OllamaConnectionError(
            "Could not connect to Ollama. Ensure Ollama is running locally."
        ) from exc
    except httpx.TimeoutException as exc:
        raise OllamaConnectionError(
            "Ollama request timed out while generating the quest."
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise OllamaConnectionError(
            "Ollama returned an error while generating the quest."
        ) from exc

    response_text = data.get("response")
    if not response_text or not str(response_text).strip():
        raise OllamaConnectionError("Ollama returned an empty response.")

    return str(response_text)
