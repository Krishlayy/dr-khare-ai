import httpx
import json
import asyncio
import time
import uuid
import threading
from typing import AsyncGenerator

from backend.core.config import settings
from backend.core.logging_config import get_logger
from backend.core.http_client import get_client
from backend.database.database import SessionLocal
from backend.database.models import Analytics

import sentry_sdk

logger = get_logger("services.llm")

# Optionally use Redis for distributed circuit breaking
redis_client = None
if settings.REDIS_URL:
    import redis.asyncio as redis
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def _log_analytics(event_type: str, event_data: dict):
    try:
        def do_insert():
            try:
                with SessionLocal() as db:
                    db.add(Analytics(event_type=event_type, event_data=event_data))
                    db.commit()
            except Exception as e:
                logger.error(f"Failed to insert analytics to DB: {e}")
        threading.Thread(target=do_insert, daemon=True).start()
    except Exception as e:
        logger.error(f"Failed to queue analytics: {e}")

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: int = 300):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._local_failures = {}
        self._local_unhealthy_until = {}

    async def is_healthy(self, provider_name: str) -> bool:
        if redis_client:
            is_unhealthy = await redis_client.get(f"cb_unhealthy_{provider_name}")
            return not bool(is_unhealthy)
        else:
            unhealthy_until = self._local_unhealthy_until.get(provider_name, 0)
            return time.time() > unhealthy_until

    async def record_success(self, provider_name: str):
        if redis_client:
            await redis_client.delete(f"cb_failures_{provider_name}")
            was_unhealthy = await redis_client.get(f"cb_unhealthy_{provider_name}")
            if was_unhealthy:
                await redis_client.delete(f"cb_unhealthy_{provider_name}")
                logger.info(f"Circuit breaker recovered for {provider_name}")
                _log_analytics("circuit_breaker_recovery", {"provider": provider_name})
        else:
            self._local_failures[provider_name] = 0
            if provider_name in self._local_unhealthy_until:
                del self._local_unhealthy_until[provider_name]
                logger.info(f"Circuit breaker recovered for {provider_name}")
                _log_analytics("circuit_breaker_recovery", {"provider": provider_name})

    async def record_failure(self, provider_name: str):
        if redis_client:
            failures = await redis_client.incr(f"cb_failures_{provider_name}")
            if failures >= self.failure_threshold:
                # Trip the breaker
                await redis_client.setex(f"cb_unhealthy_{provider_name}", self.cooldown_seconds, "true")
                await redis_client.delete(f"cb_failures_{provider_name}")
                logger.warning(f"Circuit breaker tripped for {provider_name}")
                _log_analytics("circuit_breaker_open", {"provider": provider_name})
        else:
            fails = self._local_failures.get(provider_name, 0) + 1
            self._local_failures[provider_name] = fails
            if fails >= self.failure_threshold:
                self._local_unhealthy_until[provider_name] = time.time() + self.cooldown_seconds
                self._local_failures[provider_name] = 0
                logger.warning(f"Circuit breaker tripped for {provider_name}")
                _log_analytics("circuit_breaker_open", {"provider": provider_name})

cb = CircuitBreaker()

class BaseLLMProvider:
    name: str

    async def generate(self, prompt: str, temperature: float) -> str:
        raise NotImplementedError

    async def stream(self, prompt: str, temperature: float) -> AsyncGenerator[str, None]:
        raise NotImplementedError
        yield ""

class GroqProvider(BaseLLMProvider):
    name = "groq"

    async def generate(self, prompt: str, temperature: float) -> str:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not configured")
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
        client = get_client()
        start = time.perf_counter()
        try:
            resp = await asyncio.wait_for(
                client.post(
                    url,
                    headers=headers,
                    json={
                        "model": settings.GROQ_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": temperature,
                        "stream": False
                    }
                ),
                timeout=20.0
            )
            resp.raise_for_status()
            latency = int((time.perf_counter() - start) * 1000)
            _log_analytics("llm_request", {"provider": self.name, "latency_ms": latency, "status": "success"})
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            _log_analytics("llm_request", {"provider": self.name, "latency_ms": latency, "status": "error", "error": str(e)})
            raise

    async def stream(self, prompt: str, temperature: float) -> AsyncGenerator[str, None]:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not configured")
            
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
        client = get_client()
        start = time.perf_counter()
        
        try:
            req = client.build_request(
                "POST",
                url,
                headers=headers,
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "stream": True
                }
            )
            response = await asyncio.wait_for(client.send(req, stream=True), timeout=20.0)
            response.raise_for_status()
        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            _log_analytics("llm_request", {"provider": self.name, "latency_ms": latency, "status": "error", "error": str(e)})
            raise

        async for line in response.aiter_lines():
            if not line or not line.startswith("data: "):
                continue
            data_str = line[6:]
            if data_str == "[DONE]":
                break
            try:
                data = json.loads(data_str)
                token = data["choices"][0].get("delta", {}).get("content", "")
                if token:
                    yield token
            except Exception:
                pass
        await response.aclose()
        latency = int((time.perf_counter() - start) * 1000)
        _log_analytics("llm_request", {"provider": self.name, "latency_ms": latency, "status": "success"})

class OllamaProvider(BaseLLMProvider):
    name = "ollama"

    async def _get_model(self) -> str:
        try:
            client = get_client()
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5.0)
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            for preferred in settings.OLLAMA_MODEL_PRIORITY:
                if preferred in models:
                    return preferred
            return models[0] if models else "qwen2.5:3b"
        except Exception:
            return "qwen2.5:3b"

    async def generate(self, prompt: str, temperature: float) -> str:
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        client = get_client()
        options = {"temperature": temperature}
        if settings.OLLAMA_NUM_GPU is not None:
            options["num_gpu"] = settings.OLLAMA_NUM_GPU
            
        model = await self._get_model()
        start = time.perf_counter()
        try:
            resp = await asyncio.wait_for(
                client.post(
                    url,
                    json={"model": model, "prompt": prompt, "stream": False, "options": options},
                ),
                timeout=45.0
            )
            resp.raise_for_status()
            latency = int((time.perf_counter() - start) * 1000)
            _log_analytics("llm_request", {"provider": self.name, "latency_ms": latency, "status": "success"})
            return resp.json().get("response", "").strip()
        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            _log_analytics("llm_request", {"provider": self.name, "latency_ms": latency, "status": "error", "error": str(e)})
            raise

    async def stream(self, prompt: str, temperature: float) -> AsyncGenerator[str, None]:
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        client = get_client()
        options = {"temperature": temperature}
        if settings.OLLAMA_NUM_GPU is not None:
            options["num_gpu"] = settings.OLLAMA_NUM_GPU
            
        model = await self._get_model()
        start = time.perf_counter()
        
        try:
            req = client.build_request(
                "POST",
                url,
                json={"model": model, "prompt": prompt, "stream": True, "options": options},
            )
            response = await asyncio.wait_for(client.send(req, stream=True), timeout=45.0)
            response.raise_for_status()
        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            _log_analytics("llm_request", {"provider": self.name, "latency_ms": latency, "status": "error", "error": str(e)})
            raise

        async for line in response.aiter_lines():
            if not line:
                continue
            try:
                data = json.loads(line)
                token = data.get("response", "")
                if token:
                    yield token
                if data.get("done"):
                    break
            except Exception:
                pass
        await response.aclose()
        latency = int((time.perf_counter() - start) * 1000)
        _log_analytics("llm_request", {"provider": self.name, "latency_ms": latency, "status": "success"})

_providers = {
    "groq": GroqProvider(),
    "ollama": OllamaProvider(),
}

async def get_selected_model(force_refresh: bool = False) -> str | None:
    if await cb.is_healthy(settings.PRIMARY_PROVIDER):
        return settings.PRIMARY_PROVIDER
    return settings.FALLBACK_PROVIDER

async def generate_response(prompt: str, model: str | None = None, temperature: float = 0.0) -> str:
    primary_name = settings.PRIMARY_PROVIDER
    fallback_name = settings.FALLBACK_PROVIDER
    
    primary = _providers.get(primary_name)
    fallback = _providers.get(fallback_name)

    if primary and await cb.is_healthy(primary_name):
        try:
            res = await primary.generate(prompt, temperature)
            await cb.record_success(primary_name)
            return res
        except Exception as e:
            logger.error(f"Primary provider '{primary_name}' failed: {e}")
            await cb.record_failure(primary_name)
            _log_analytics("failover_event", {"from": primary_name, "to": fallback_name, "reason": str(e)})
            # Fallthrough to fallback
    elif primary:
        logger.info(f"Primary provider '{primary_name}' is unhealthy. Routing to fallback.")

    if fallback:
        try:
            res = await fallback.generate(prompt, temperature)
            return res
        except Exception as e:
            logger.error(f"Fallback provider '{fallback_name}' failed: {e}")
            if settings.SENTRY_DSN:
                sentry_sdk.capture_exception(e)
            
            return "Dr. Khare AI is temporarily unavailable due to a system issue. Please try again in a few minutes."
    
    return "Dr. Khare AI is temporarily unavailable due to a system issue. Please try again in a few minutes."

async def stream_response(prompt: str, model: str | None = None, temperature: float = 0.0):
    primary_name = settings.PRIMARY_PROVIDER
    fallback_name = settings.FALLBACK_PROVIDER
    
    primary = _providers.get(primary_name)
    fallback = _providers.get(fallback_name)

    if primary and await cb.is_healthy(primary_name):
        try:
            gen = primary.stream(prompt, temperature)
            first_chunk = await anext(gen)
            await cb.record_success(primary_name)
            
            async def generator_wrapper():
                yield first_chunk
                async for chunk in gen:
                    yield chunk
                    
            async for chunk in generator_wrapper():
                yield chunk
            return
        except StopAsyncIteration:
            await cb.record_success(primary_name)
            return
        except Exception as e:
            logger.error(f"Primary provider '{primary_name}' failed during stream setup: {e}")
            await cb.record_failure(primary_name)
            _log_analytics("failover_event", {"from": primary_name, "to": fallback_name, "reason": str(e)})
            # Fallthrough
            
    elif primary:
        logger.info(f"Primary provider '{primary_name}' is unhealthy. Routing to fallback.")

    if fallback:
        try:
            gen = fallback.stream(prompt, temperature)
            first_chunk = await anext(gen)
            
            async def generator_wrapper():
                yield first_chunk
                async for chunk in gen:
                    yield chunk
                    
            async for chunk in generator_wrapper():
                yield chunk
            return
        except StopAsyncIteration:
            return
        except Exception as e:
            logger.error(f"Fallback provider '{fallback_name}' failed: {e}")
            if settings.SENTRY_DSN:
                sentry_sdk.capture_exception(e)
            
            yield "Dr. Khare AI is temporarily unavailable due to a system issue. Please try again in a few minutes."
            return
            
    yield "Dr. Khare AI is temporarily unavailable due to a system issue. Please try again in a few minutes."

async def get_ollama_status() -> dict:
    try:
        client = get_client()
        resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2.0)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        reachable = True
    except Exception:
        models = []
        reachable = False
        
    selected = None
    if reachable:
        for preferred in settings.OLLAMA_MODEL_PRIORITY:
            if preferred in models:
                selected = preferred
                break
        if not selected and models:
            selected = models[0]
            
    return {
        "reachable": reachable,
        "selected_model": selected,
        "models": models,
        "priority": settings.OLLAMA_MODEL_PRIORITY,
    }
