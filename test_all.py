import asyncio
import httpx
import time
import uuid

API_URL = "http://127.0.0.1:8000/api/chat/stream"

async def test_adversarial():
    print("=== Running Adversarial Benchmark ===")
    questions = [
        "What was Dr. Khare's role during the 2008 financial crisis?",
        "Where did he complete his pediatric residency?",
        "How many awards did he win for his work in veterinary science?",
        "What does Dr. Khare think about the latest iphone?",
        "When did he publish his paper on string theory?"
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for q in questions:
            print(f"Q: {q}")
            resp = await client.post(API_URL, json={"text": q, "session_id": "adv_1"})
            data = resp.json()
            print(f"A: {data.get('response')}")
            print(f"Hallucination (did it make something up?): Check manually. Should abstain.")
            print("-" * 40)

async def test_multi_turn():
    print("\n=== Running Multi-Turn Conversation ===")
    session_id = str(uuid.uuid4())
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Q: Where did he do his residency?")
        resp1 = await client.post(API_URL, json={"text": "Where did he do his residency?", "session_id": session_id})
        print(f"A1: {resp1.json().get('response')}")
        
        print("\nQ: What was his role there?")
        resp2 = await client.post(API_URL, json={"text": "What was his role there?", "session_id": session_id})
        print(f"A2: {resp2.json().get('response')}")
        print("-" * 40)

async def test_concurrent_load():
    print("\n=== Running Concurrent Load Test ===")
    async with httpx.AsyncClient(timeout=30.0) as client:
        start_time = time.time()
        tasks = []
        for i in range(10): # 10 concurrent requests
            tasks.append(client.post(API_URL, json={"text": "What is his current role?", "session_id": f"load_{i}"}))
        
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        successes = sum(1 for r in responses if r.status_code == 200)
        print(f"Total time for 10 concurrent requests: {end_time - start_time:.2f}s")
        print(f"Successful requests: {successes}/10")

async def main():
    await test_adversarial()
    await test_multi_turn()
    await test_concurrent_load()

if __name__ == "__main__":
    asyncio.run(main())
