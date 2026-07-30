import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.services.chat_service import process_chat
from backend.database.database import SessionLocal
from backend.core.http_client import get_client, close_client
from backend.rag.embeddings import get_embedding_model
from backend.rag.retrieval import get_cross_encoder, get_bm25_index

async def run_adversarial_tests():
    get_client()
    db = SessionLocal()
    session_id = "adv_test_direct"
    
    get_embedding_model()
    get_cross_encoder()
    get_bm25_index()
    
    questions = [
        "Did Dr. Khare ever work at Fortis Memorial Research Institute?",
        "Was Dr. Khare a Chief Resident?",
        "Is Dr. Khare registered with the Delhi Medical Council?",
        "Tell me about Dr. Khare's COPE Trial."
    ]
    
    print("Running Adversarial Tests...")
    for q in questions:
        print(f"\n[Q] {q}")
        try:
            resp = await process_chat(db, q, session_id, mode="doctor")
            print(f"[A] {resp['response']}")
            print(f"[Sources] {[s['filename'] for s in resp['sources']]}")
        except Exception as e:
            print(f"[Error] {e}")
            
    db.close()
    await close_client()

if __name__ == "__main__":
    asyncio.run(run_adversarial_tests())
