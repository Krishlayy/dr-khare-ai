import os
import sys
import asyncio
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.services.chat_service import process_chat
from backend.scripts.eval_suite import GROUND_TRUTH_DATA, eval_hallucination_and_facts
from backend.rag.retrieval import get_cross_encoder, get_bm25_index
from backend.rag.embeddings import get_embedding_model
from backend.database.core import SessionLocal

async def main():
    db = SessionLocal()
    test_suite = GROUND_TRUTH_DATA[:25]
    print(f"Starting Real Evaluation on {len(test_suite)} questions...", flush=True)
    
    results = []
    
    for idx, item in enumerate(test_suite):
        q = item["question"]
        print(f"\n[{idx+1}/{len(test_suite)}] Testing: {q}")
        
        start_t = time.time()
        try:
            chat_resp = await process_chat(db, q, "session_test", mode="doctor")
            full_response = chat_resp["response"]
                        
            latency = (time.time() - start_t) * 1000
            
            # Re-retrieve to get the context for judging
            from backend.rag.retrieval import retrieve_context
            retrieval = await retrieve_context(q)
            
            f_score, h_score = await eval_hallucination_and_facts(q, full_response, retrieval.context, item["expected_facts"])
            
            retrieved_docs = [m.document for m in retrieval.matches]
            recall_score = 1.0 if any(item["expected_document"] in doc for doc in retrieved_docs) else 0.0
            precision_score = 1.0 if any(item["expected_document"] in src for src in retrieved_docs[:3]) else 0.0
            
            results.append({
                "recall": recall_score,
                "precision": precision_score,
                "factual_coverage": f_score,
                "hallucination": h_score
            })
            
            print(f"  -> Factual: {f_score:.2f} | Hallucination: {h_score:.2f}")
            
        except Exception as e:
            print(f"  -> Error: {e}")
            
    print("\n# 25-Question Prompt Optimization Evaluation")
    
    avg_recall = sum(r["recall"] for r in results) / len(results) if results else 0.0
    avg_prec = sum(r["precision"] for r in results) / len(results) if results else 0.0
    avg_fact = sum(r["factual_coverage"] for r in results) / len(results) if results else 0.0
    avg_hall = sum(r["hallucination"] for r in results) / len(results) if results else 0.0
    
    print("\n## Comparison vs Baseline (Pure Generation)")
    print("| Metric | Baseline (25Q) | Post-Optimization (25Q) |")
    print("| --- | --- | --- |")
    print(f"| Recall | 0.85 | {avg_recall:.2f} |")
    print(f"| Precision | 0.90 | {avg_prec:.2f} |")
    print(f"| Factual Coverage | 0.64 | {avg_fact:.2f} |")
    print(f"| Hallucination Rate | 0.12 | {avg_hall:.2f} |")

if __name__ == "__main__":
    print("-> Preloading models globally before event loop...", flush=True)
    get_embedding_model()
    get_cross_encoder()
    get_bm25_index()
    print("-> Preloaded successfully.", flush=True)
    
    asyncio.run(main())
