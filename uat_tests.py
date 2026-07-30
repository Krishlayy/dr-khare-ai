import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.services.chat_service import process_chat
from backend.database.database import SessionLocal
from backend.core.http_client import get_client, close_client
from backend.rag.embeddings import get_embedding_model
from backend.rag.retrieval import get_cross_encoder, get_bm25_index

async def run_uat():
    get_client()
    db = SessionLocal()
    session_id = "uat_test_final"
    
    # 1. Verify ChromaDB persistence by checking initialization
    get_embedding_model()
    get_cross_encoder()
    get_bm25_index()
    
    questions = [
        "Hello, what can you do?",
        "Where did Dr. Khare do his residency?",
        "What awards has he won?",
        "Tell me about his research.",
        "Where is he currently working?",
        "Is he a member of the American College of Physicians?",
        "Does he treat Parkinson's?",
        "Did he win the Champion's Trophy?",
        "Where did he go to medical school?",
        "What is Compendious Med Works?",
        "Is he registered with the Delhi Medical Council?",
        "Has he published anything on leukemia?",
        "What languages does he speak?", # From original doctor_profile.txt (I might not have included it in the strict extraction, let's see how it behaves)
        "What are his hobbies?",
        "Is he a Chief Resident?",
        "Has he worked in California?",
        "Has he worked in Texas?",
        "Tell me about his role at Lompoc Valley Medical Center.",
        "What are his specialties?",
        "Thank you for the information."
    ]
    
    print("Running 20 UAT Questions...\n")
    results = []
    for q in questions:
        try:
            resp = await process_chat(db, q, session_id, mode="doctor")
            res_text = f"Q: {q}\nA: {resp['response']}\nSources: {[s['filename'] for s in resp['sources']]}\nBypassed: {resp.get('bypassed_llm', False)}\n"
            print(res_text)
            results.append(res_text)
        except Exception as e:
            err = f"Q: {q}\nError: {e}\n"
            print(err)
            results.append(err)
            
    with open("UAT_RESULTS.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))
            
    db.close()
    await close_client()

if __name__ == "__main__":
    asyncio.run(run_uat())
