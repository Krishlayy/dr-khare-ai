import asyncio
import aiohttp
import time
import json

URL_CHAT = "http://localhost:8000/api/chat/stream"
URL_HEALTH = "http://localhost:8000/"

async def fetch(session, url, method="GET", payload=None):
    start = time.perf_counter()
    try:
        if method == "POST":
            async with session.post(url, json=payload, timeout=120) as response:
                status = response.status
                await response.read()
        else:
            async with session.get(url, timeout=10) as response:
                status = response.status
                await response.read()
        end = time.perf_counter()
        return status, end - start
    except Exception as e:
        return str(e), time.perf_counter() - start

async def run_load_test(concurrency, url, method="GET", payload=None):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url, method, payload) for _ in range(concurrency)]
        results = await asyncio.gather(*tasks)
        
        successes = [r for r in results if isinstance(r[0], int) and r[0] == 200]
        failures = [r for r in results if not (isinstance(r[0], int) and r[0] == 200)]
        times = [r[1] for r in successes]
        
        avg_time = sum(times)/len(times) if times else 0
        return {
            "concurrency": concurrency,
            "success": len(successes),
            "fail": len(failures),
            "avg_latency": avg_time,
            "min_latency": min(times) if times else 0,
            "max_latency": max(times) if times else 0
        }

async def main():
    print("Starting Load Tests...")
    levels = [10, 25, 50, 100]
    
    print("\n--- Testing Health Endpoint (FastAPI + Uvicorn Throughput) ---")
    for c in levels:
        res = await run_load_test(c, URL_HEALTH)
        print(f"Users: {c:3} | Success: {res['success']:3} | Fail: {res['fail']:3} | Avg Latency: {res['avg_latency']:.2f}s | Max: {res['max_latency']:.2f}s")
        await asyncio.sleep(1)

    print("\n--- Testing Chat Endpoint (FastAPI + VectorDB + Ollama) ---")
    payload = {"text": "Who is Dr. Khare?", "stream": False}
    for c in [10, 25]: # 50 and 100 will likely timeout/OOM locally
        res = await run_load_test(c, URL_CHAT, "POST", payload)
        print(f"Users: {c:3} | Success: {res['success']:3} | Fail: {res['fail']:3} | Avg Latency: {res['avg_latency']:.2f}s | Max: {res['max_latency']:.2f}s")
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
