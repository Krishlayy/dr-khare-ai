import asyncio
import aiohttp
import json
import time

URL_CHAT = "http://localhost:8000/api/chat/stream"
URL_LIMIT = "http://localhost:8000/api/chat/remaining-questions"

async def test_audit():
    async with aiohttp.ClientSession() as session:
        print("--- Testing /remaining-questions ---")
        async with session.get(URL_LIMIT) as resp:
            data = await resp.json()
            print(f"Remaining Questions Data: {data}")
            assert "remaining" in data
            
        print("\n--- Testing Cache Miss / LLM Path ---")
        payload = {"text": "What is the capital of France? (Audit Test)", "stream": False}
        
        start = time.perf_counter()
        async with session.post(URL_CHAT, json=payload) as resp:
            data = await resp.json()
            # It will probably return Hard Grounding because it's not in the KB
            print(f"Status: {resp.status}")
            print(f"Model Used: {data.get('model')}")
            print(f"Bypassed LLM: {data.get('bypassed_llm')}")
            print(f"Response Time: {data.get('response_time_ms')}ms")
        
        print("\n--- Testing Cache Hit Path ---")
        start = time.perf_counter()
        async with session.post(URL_CHAT, json=payload) as resp:
            data = await resp.json()
            print(f"Status: {resp.status}")
            print(f"Model Used: {data.get('model')}")
            print(f"Bypassed LLM: {data.get('bypassed_llm')}")
            print(f"Response Time: {data.get('response_time_ms')}ms")
            
        print("\n--- Testing Question Limit Enforcement ---")
        # We did 2 questions. Let's do 4 more to trigger the limit (5 total).
        for i in range(4):
            async with session.post(URL_CHAT, json={"text": f"Zxqkjwhdfbasdkjfbasdkhjf {i}", "stream": False}) as r:
                try:
                    d = await r.json()
                    if "limit of 5 questions" in str(d):
                        print(f"Hit limit on attempt {i+3}: {d}")
                    else:
                        print(f"Attempt {i+3} succeeded.")
                except Exception as e:
                    print(f"Attempt {i+3} failed with status {r.status}")

        print("\n--- Re-testing /remaining-questions after limit ---")
        async with session.get(URL_LIMIT) as resp:
            data = await resp.json()
            print(f"Remaining Questions Data: {data}")

if __name__ == "__main__":
    asyncio.run(test_audit())
