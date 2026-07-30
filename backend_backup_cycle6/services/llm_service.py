import httpx
import json

from backend.core.config import settings
from backend.core.logging_config import get_logger
from backend.core.http_client import get_client

logger = get_logger("services.llm")

_selected_model: str | None = None

async def list_models() -> tuple[bool, list[str]]:
    try:
        client = get_client()
        resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        return True, models
    except Exception as exc:
        logger.error("Ollama unreachable: %s", exc)
        return False, []

def _pick_model(available: list[str]) -> str | None:
    for preferred in settings.OLLAMA_MODEL_PRIORITY:
        if preferred in available:
            return preferred
        base = preferred.split(":")[0]
        for name in available:
            if name == base or name.startswith(f"{base}:"):
                return name
    return available[0] if available else None

async def get_selected_model(force_refresh: bool = False) -> str | None:
    if settings.LLM_PROVIDER == "groq" and settings.GROQ_API_KEY:
        return "groq/llama3-8b-8192"
        
    global _selected_model
    if _selected_model and not force_refresh:
        return _selected_model

    reachable, models = await list_models()
    if not reachable:
        return None

    _selected_model = _pick_model(models)
    logger.info("Selected Ollama model: %s (available: %s)", _selected_model, models)
    return _selected_model

async def get_ollama_status() -> dict:
    reachable, models = await list_models()
    selected = _pick_model(models) if reachable else None
    return {
        "reachable": reachable,
        "selected_model": selected,
        "models": models,
        "priority": settings.OLLAMA_MODEL_PRIORITY,
    }

async def generate_response(prompt: str, model: str | None = None, temperature: float = 0.0) -> str:
    model = model or await get_selected_model()
    if not model:
        raise RuntimeError("No LLM available (Groq offline or Ollama unreachable)")

    if model.startswith("groq/") and settings.GROQ_API_KEY:
        return await _generate_groq(prompt, model.split("/")[1], temperature)

    return await _generate_ollama(prompt, model, temperature)

async def _generate_groq(prompt: str, model: str, temperature: float) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
    client = get_client()
    import asyncio
    try:
        resp = await asyncio.wait_for(
            client.post(
                url,
                headers=headers,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "stream": False
                }
            ),
            timeout=20.0
        )
    except asyncio.TimeoutError:
        raise RuntimeError("Groq API timed out after 20 seconds")
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()

async def _generate_ollama(prompt: str, model: str, temperature: float) -> str:
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    client = get_client()
    options = {"temperature": temperature}
    if settings.OLLAMA_NUM_GPU is not None:
        options["num_gpu"] = settings.OLLAMA_NUM_GPU
        
    import asyncio
    try:
        resp = await asyncio.wait_for(
            client.post(
                url,
                json={"model": model, "prompt": prompt, "stream": False, "options": options},
            ),
            timeout=20.0
        )
    except asyncio.TimeoutError:
        raise RuntimeError("Ollama API timed out after 20 seconds")
    resp.raise_for_status()
    return resp.json().get("response", "").strip()

async def stream_response(prompt: str, model: str | None = None, temperature: float = 0.0):
    model = model or await get_selected_model()
    if not model:
        raise RuntimeError("No LLM available (Groq offline or Ollama unreachable)")

    if model.startswith("groq/") and settings.GROQ_API_KEY:
        async for token in _stream_groq(prompt, model.split("/")[1], temperature):
            yield token
        return

    async for token in _stream_ollama(prompt, model, temperature):
        yield token

async def _stream_groq(prompt: str, model: str, temperature: float):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
    client = get_client()
    async with client.stream(
        "POST",
        url,
        headers=headers,
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "stream": True
        }
    ) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if not line or not line.startswith("data: "):
                continue
            data_str = line[6:]
            if data_str == "[DONE]":
                break
            data = json.loads(data_str)
            token = data["choices"][0].get("delta", {}).get("content", "")
            if token:
                yield token

async def _stream_ollama(prompt: str, model: str, temperature: float):
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    client = get_client()
    options = {"temperature": temperature}
    if settings.OLLAMA_NUM_GPU is not None:
        options["num_gpu"] = settings.OLLAMA_NUM_GPU
        
    async with client.stream(
        "POST",
        url,
        json={"model": model, "prompt": prompt, "stream": True, "options": options},
    ) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if not line:
                continue
            data = json.loads(line)
            token = data.get("response", "")
            if token:
                yield token
            if data.get("done"):
                break
