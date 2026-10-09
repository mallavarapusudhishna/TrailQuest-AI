import httpx

from backend.app.config import OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS, OLLAMA_URL


class OllamaConnectionError(Exception):
    """Raised when Ollama cannot be reached or returns an error."""


class OllamaModelNotFoundError(OllamaConnectionError):
    """Raised when the configured model is missing from Ollama."""


async def generate_quest(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    timeout = httpx.Timeout(OLLAMA_TIMEOUT_SECONDS, connect=15.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.ConnectError as exc:
        raise OllamaConnectionError(
            "Could not connect to Ollama. Ensure Ollama is running locally."
        ) from exc
    except httpx.TimeoutException as exc:
        raise OllamaConnectionError(
            "Ollama request timed out while generating the quest. "
            "Try again or increase OLLAMA_TIMEOUT_SECONDS."
        ) from exc
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise OllamaModelNotFoundError(
                f"Model '{OLLAMA_MODEL}' was not found in Ollama. Run: ollama pull {OLLAMA_MODEL}"
            ) from exc
        raise OllamaConnectionError(
            "Ollama returned an error while generating the quest."
        ) from exc

    response_text = data.get("response")
    if not response_text or not str(response_text).strip():
        raise OllamaConnectionError("Ollama returned an empty response.")

    return str(response_text)
