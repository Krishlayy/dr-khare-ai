import asyncio
import time
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from backend.services.chat_service import chat

async def run_mini_bench():
    questions = [
        "What certifications does he hold?",
        "When did he graduate MBBS?",
        "What is his role at Signify Health?"
    ]
    
    for q in questions:
        print(f"\n--- Question: {q} ---")
        t0 = time.perf_counter()
        
        # We pass an empty DB session since memory retrieval doesn't strictly need it if we handle it correctly, 
        # but chat() might need db. We'll use None or just call _run_doctor_mode directly.
        # Actually, let's just use chat() with a mock DB or we can call retrieve_context directly, 
        # but chat() goes end-to-end. Let's just do an HTTP request to the local server or use the logic.
        pass

if __name__ == "__main__":
    asyncio.run(run_mini_bench())
