import asyncio
import json
import math
import os
import sys

# Ensure backend imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.rag.retrieval import retrieve_context, get_cross_encoder, get_bm25_index
from backend.rag.embeddings import get_embedding_model

async def run_retrieval_eval():
    print("Preloading assets...")
    get_embedding_model()
    get_cross_encoder()
    get_bm25_index()
    
    path = os.path.join(os.path.dirname(__file__), "ground_truth_100_v2.json")
    with open(path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    total = len(ground_truth)
    recall_1 = 0
    recall_3 = 0
    recall_5 = 0
    mrr_sum = 0
    ndcg_sum = 0
    
    failures = []

    print(f"Testing {total} questions...")
    for idx, item in enumerate(ground_truth):
        q = item["question"]
        expected = item["expected_document"]
        
        result = await retrieve_context(q)
        retrieved_docs = [m.document for m in result.matches]
        
        rank = -1
        for i, doc in enumerate(retrieved_docs):
            if doc == expected:
                rank = i + 1
                break
                
        if rank == 1:
            recall_1 += 1
        if 1 <= rank <= 3:
            recall_3 += 1
        if 1 <= rank <= 5:
            recall_5 += 1
            
        if rank > 0:
            mrr_sum += 1.0 / rank
            ndcg_sum += 1.0 / math.log2(rank + 1)
        else:
            failures.append({
                "question": q,
                "expected": expected,
                "retrieved": retrieved_docs
            })
            
        if (idx + 1) % 10 == 0:
            print(f"[{idx + 1}/{total}] Processed.")

    print("\n=== FAST RETRIEVAL METRICS ===")
    print(f"Total: {total}")
    print(f"Recall@1: {recall_1 / total:.4f}")
    print(f"Recall@3: {recall_3 / total:.4f}")
    print(f"Recall@5: {recall_5 / total:.4f}")
    print(f"MRR: {mrr_sum / total:.4f}")
    print(f"nDCG: {ndcg_sum / total:.4f}")
    print(f"Failures (not in top 5): {len(failures)}")
    
    if failures:
        print("\nSample Failures:")
        for f in failures[:5]:
            print(f"Q: {f['question']}")
            print(f"Expected: {f['expected']}")
            print(f"Got: {f['retrieved']}\n")

if __name__ == "__main__":
    asyncio.run(run_retrieval_eval())
