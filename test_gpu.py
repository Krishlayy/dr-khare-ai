import asyncio
import time
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from backend.services.llm_service import generate_response

async def test_gpu():
    print("Testing qwen2.5:3b generation speed on Vulkan iGPU...")
    
    prompt = "Explain in detail the pathogenesis of type 2 diabetes. Write at least 200 words."
    
    t0 = time.perf_counter()
    response = await generate_response(prompt, "qwen2.5:3b")
    t1 = time.perf_counter()
    
    duration = t1 - t0
    words = len(response.split())
    # rough token estimate = words * 1.3
    est_tokens = int(words * 1.3)
    tps = est_tokens / duration
    
    print(f"\nResponse:\n{response[:200]}...\n")
    print(f"Time taken: {duration:.2f} seconds")
    print(f"Estimated Words: {words}")
    print(f"Estimated Tokens: {est_tokens}")
    print(f"Tokens per second: {tps:.2f} tok/s")

if __name__ == "__main__":
    asyncio.run(test_gpu())
