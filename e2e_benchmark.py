import json
import time
import asyncio
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.database.database import SessionLocal
from backend.services.document_pipeline import run_document_pipeline
from backend.database.models import Document, ChatHistory
from backend.services.intent_service import detect_intent
from backend.rag.retrieval import retrieve_context, get_chroma_collection
from backend.services.chat_service import build_doctor_kb_prompt
from backend.services.llm_service import generate_response
from backend.core.config import settings

# Global timing dict
current_timings = {}

# Original methods
import chromadb
orig_chroma_query = None

def get_orig_chroma():
    global orig_chroma_query
    coll = get_chroma_collection()
    if orig_chroma_query is None:
        orig_chroma_query = coll.query
    return coll

def patched_chroma_query(*args, **kwargs):
    start = time.perf_counter()
    coll = get_orig_chroma()
    res = orig_chroma_query(*args, **kwargs)
    current_timings['dense'] = (time.perf_counter() - start) * 1000
    return res

from rank_bm25 import BM25Okapi
orig_bm25_get_scores = BM25Okapi.get_scores

def patched_bm25_get_scores(self, query):
    start = time.perf_counter()
    res = orig_bm25_get_scores(self, query)
    current_timings['bm25'] = (time.perf_counter() - start) * 1000
    return res

from sentence_transformers import CrossEncoder
orig_cross_predict = CrossEncoder.predict

def patched_cross_predict(self, sentences, **kwargs):
    start = time.perf_counter()
    res = orig_cross_predict(self, sentences, **kwargs)
    current_timings['rerank'] = (time.perf_counter() - start) * 1000
    return res


def check_assertions(text, expected_sources, required_kw, forbidden_kw, sources_found):
    text_lower = text.lower()
    
    for kw in forbidden_kw:
        if kw.lower() in text_lower:
            return False, f"Found forbidden keyword: '{kw}'"
            
    if required_kw:
        if not any(kw.lower() in text_lower for kw in required_kw):
            return False, f"Missing any of the required keywords: {required_kw}"
            
    if expected_sources:
        for es in expected_sources:
            if not any(es in sf for sf in sources_found):
                return False, f"Expected source '{es}' not found in retrieved sources {sources_found}"
                
    return True, None

async def run_benchmark():
    db = SessionLocal()
    
    # Ingest document
    print("Ingesting dr_khare_hobbies.txt...")
    existing = db.query(Document).filter(Document.filename == "dr_khare_hobbies.txt").first()
    if not existing:
        doc = Document(
            filename="dr_khare_hobbies.txt",
            filepath=os.path.abspath("dr_khare_hobbies.txt"),
            filetype="txt",
            status="processing",
            processing_stage="extracting_text"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        run_document_pipeline(doc.id)
        print("Ingestion complete.")
    else:
        print("Document already exists.")

    with open("e2e_test_cases.json", "r") as f:
        cases = json.load(f)

    results = []
    session_history = {}
    
    orig_wait_for = asyncio.wait_for
    async def patched_wait_for(aw, timeout=None):
        return await orig_wait_for(aw, timeout=300.0)
    asyncio.wait_for = patched_wait_for
    
    coll = get_orig_chroma()
    coll.query = patched_chroma_query
    BM25Okapi.get_scores = patched_bm25_get_scores
    CrossEncoder.predict = patched_cross_predict
    
    for i, c in enumerate(cases):
        global current_timings
        current_timings = {'dense': 0, 'bm25': 0, 'rerank': 0}
        
        q = c["q"]
        print(f"\n[{i+1}/{len(cases)}] {q}")
        
        session_id = c.get("session_group", "default")
        history = session_history.get(session_id, [])
        
        t0 = time.perf_counter()
        
        i_t0 = time.perf_counter()
        intent = detect_intent(q)
        i_time = (time.perf_counter() - i_t0) * 1000
        
        r_t0 = time.perf_counter()
        retrieval = await retrieve_context(q)
        r_time = (time.perf_counter() - r_t0) * 1000
        
        # Test harness implementation of Anti-Hallucination Policy
        confidence = retrieval.confidence
        bypassed_llm = False
        response_text = ""
        g_time = 0
        p_time = 0
        
        retrieval_only = False
        
        if confidence < settings.SIMILARITY_THRESHOLD: # Low Confidence
            bypassed_llm = True
            response_text = "I could not find verified information about this topic in Dr. Khare's available documents. You may discuss it with him during your next meeting."
        else:
            p_t0 = time.perf_counter()
            prompt = build_doctor_kb_prompt(q, retrieval.context, history)
            if confidence < 0.20: # Medium Confidence
                prompt += "\n\nCRITICAL INSTRUCTION: Your retrieval confidence is MEDIUM. Answer cautiously. Explicitly state that limited information was found. Do not infer missing details."
            p_time = (time.perf_counter() - p_t0) * 1000
            
            if retrieval_only:
                bypassed_llm = True
                response_text = "RETRIEVAL_ONLY_MODE_SIMULATED_ANSWER"
                g_time = 0
            else:
                g_t0 = time.perf_counter()
                response_text = await generate_response(prompt, model="qwen2.5:3b")
                g_time = (time.perf_counter() - g_t0) * 1000
            
        t_total = (time.perf_counter() - t0) * 1000
        
        history.append({"role": "user", "content": q})
        history.append({"role": "assistant", "content": response_text})
        session_history[session_id] = history
        
        sources_found = [s["filename"] for s in retrieval.sources]
        passed, reason = check_assertions(response_text, c["expected_sources"], c["required_keywords"], c["forbidden_keywords"], sources_found)
        
        if c["type"] == "new_upload":
            if not any("hobbies" in sf for sf in sources_found):
                reason = "Retrieval Failure (Likely BM25 cache staleness for new upload)"
                passed = False

        results.append({
            "question": q,
            "type": c["type"],
            "passed": passed,
            "latency_ms": t_total,
            "timings": {
                "intent_ms": i_time,
                "retrieval_ms": r_time,
                "bm25_ms": current_timings.get("bm25", 0),
                "dense_ms": current_timings.get("dense", 0),
                "rerank_ms": current_timings.get("rerank", 0),
                "prompt_ms": p_time,
                "llm_ms": g_time
            },
            "retrieval": {
                "confidence": confidence,
                "sources": sources_found,
                "bypassed_llm": bypassed_llm,
                "num_chunks": len(retrieval.context.split("---")) if retrieval.context else 0
            },
            "response": response_text,
            "failure_reason": reason
        })
        
        status = "PASS" if passed else f"FAIL ({reason})"
        print(f"  -> {status} | Latency: {t_total:.0f}ms | Conf: {confidence:.2f}")
        
    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=4)
        
    db.close()
    
    coll.query = orig_chroma_query
    BM25Okapi.get_scores = orig_bm25_get_scores
    CrossEncoder.predict = orig_cross_predict

if __name__ == "__main__":
    asyncio.run(run_benchmark())
