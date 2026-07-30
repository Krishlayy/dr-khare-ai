import asyncio
import json
import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.redis_client import redis_client

client = TestClient(app)

def test_rate_limit():
    print("Starting Rate Limit Validation Test...")
    
    # 1. Reset Redis for testing IP "testclient"
    test_ip = "testclient"
    
    async def reset_redis():
        await redis_client.delete(f"chat_limit:{test_ip}")
        await redis_client.delete(f"chat_count:{test_ip}")
    
    asyncio.run(reset_redis())
    
    # Send 5 questions
    for i in range(1, 6):
        resp = client.post("/api/chat/stream", json={"text": f"Question {i}", "stream": True, "mode": "doctor"})
        assert resp.status_code == 200
        # Normal chat returns multiple SSE data lines
        content = resp.content.decode("utf-8")
        assert "data: {" in content
        print(f"Question {i} succeeded")
    
    # Question 6 should be blocked
    resp = client.post("/api/chat/stream", json={"text": "Question 6", "stream": True, "mode": "doctor"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/event-stream; charset=utf-8"
    content = resp.content.decode("utf-8")
    
    # Expected SSE lines
    assert "data: {\"type\": \"token\", \"content\": \"You have reached your limit of 5 questions per 6 hours. Please try again later.\"}" in content
    assert "data: {\"type\": \"done\"}" in content
    print("Question 6 correctly returned the limit message in SSE format.")
    
    # Verify remaining questions endpoint
    resp = client.get("/api/chat/remaining-questions")
    data = resp.json()
    assert data["remaining"] == 0
    assert data["reset_in_seconds"] > 0
    print("Remaining questions endpoint correctly reports 0 remaining and provides TTL.")
    
    # Mock TTL expiration
    async def expire_redis():
        await redis_client.delete(f"chat_limit:{test_ip}")
    
    asyncio.run(expire_redis())
    
    # Verify TTL expiration resets limit
    resp = client.get("/api/chat/remaining-questions")
    data = resp.json()
    assert data["remaining"] == 5
    assert data["reset_in_seconds"] == 0
    print("Limit automatically resets after TTL expiration.")
    
    print("\nAll validation tests passed successfully!")

if __name__ == "__main__":
    test_rate_limit()
