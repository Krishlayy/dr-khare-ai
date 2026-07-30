import asyncio
import time
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from backend.core.config import settings
from backend.services.llm_service import (
    generate_response, stream_response, cb, _providers, _log_analytics
)

class MockGroqProvider:
    name = "groq"
    def __init__(self):
        self.should_fail = False
        self.fail_reason = None
        self.generate_called = 0
        
    async def generate(self, prompt, temp):
        self.generate_called += 1
        if self.should_fail:
            raise Exception(self.fail_reason)
        return "Groq response"
        
    async def stream(self, prompt, temp):
        self.generate_called += 1
        if self.should_fail:
            raise Exception(self.fail_reason)
        yield "Groq stream response"

class MockOllamaProvider:
    name = "ollama"
    def __init__(self):
        self.should_fail = False
        self.generate_called = 0
        
    async def generate(self, prompt, temp):
        self.generate_called += 1
        if self.should_fail:
            raise Exception("Ollama failed")
        return "Ollama response"

    async def stream(self, prompt, temp):
        self.generate_called += 1
        if self.should_fail:
            raise Exception("Ollama failed")
        yield "Ollama stream response"

async def run_tests():
    print("Running LLM Failover & Circuit Breaker Tests...")
    
    # 1. Setup mocks
    groq = MockGroqProvider()
    ollama = MockOllamaProvider()
    _providers["groq"] = groq
    _providers["ollama"] = ollama
    
    settings.PRIMARY_PROVIDER = "groq"
    settings.FALLBACK_PROVIDER = "ollama"
    
    # Clear local circuit breaker state
    cb._local_failures.clear()
    cb._local_unhealthy_until.clear()
    
    # Test 1: Groq Success Path
    res = await generate_response("Hello")
    assert res == "Groq response"
    assert groq.generate_called == 1
    assert ollama.generate_called == 0
    print("Test 1 Passed: Groq Success Path")
    
    # Test 2: Groq Timeout -> Ollama Fallback
    groq.should_fail = True
    groq.fail_reason = "Timeout"
    
    res = await generate_response("Hello again")
    assert res == "Ollama response"
    assert groq.generate_called == 2
    assert ollama.generate_called == 1
    assert cb._local_failures["groq"] == 1
    print("Test 2 Passed: Groq Timeout -> Ollama Fallback")
    
    # Test 3: Groq Rate-limit -> Ollama Fallback
    groq.fail_reason = "429 Rate Limit"
    res = await generate_response("Hello 3")
    assert res == "Ollama response"
    assert cb._local_failures["groq"] == 2
    print("Test 3 Passed: Groq Rate-limit -> Ollama Fallback")
    
    # Test 4: Circuit Breaker Activation
    # Third failure should open the circuit
    res = await generate_response("Hello 4")
    assert res == "Ollama response"
    assert cb._local_failures["groq"] == 0 # reset upon tripping
    assert "groq" in cb._local_unhealthy_until
    print("Test 4 Passed: Circuit Breaker Activation")
    
    # Test 5: Fast routing when Circuit is Open (Groq shouldn't be called)
    groq.should_fail = False # even if healthy, shouldn't be called
    res = await generate_response("Hello 5")
    assert res == "Ollama response"
    assert groq.generate_called == 4 # still 4
    print("Test 5 Passed: Fast routing when Circuit Open")
    
    # Test 6: Circuit Breaker Recovery
    cb._local_unhealthy_until["groq"] = time.time() - 10 # Simulate 5 mins past
    res = await generate_response("Hello 6")
    assert res == "Groq response" # Groq works again
    assert "groq" not in cb._local_unhealthy_until
    print("Test 6 Passed: Circuit Breaker Recovery")
    
    # Test 7: Dual Provider Failure
    groq.should_fail = True
    ollama.should_fail = True
    res = await generate_response("Hello 7")
    assert res == "Dr. Khare AI is temporarily unavailable due to a system issue. Please try again in a few minutes."
    print("Test 7 Passed: Dual Provider Failure handled gracefully")
    
    print("\nAll failover architecture tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(run_tests())
