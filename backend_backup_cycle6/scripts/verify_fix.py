import os
import json
import asyncio
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.rag.retrieval import retrieve_context
from backend.scripts.eval_suite import GROUND_TRUTH_DATA
from backend.rag.retrieval import get_cross_encoder, get_bm25_index
from backend.rag.embeddings import get_embedding_model

def load_baseline():
    path = os.path.join(os.path.dirname(__file__), "../../eval_results.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {r["question"]: r for r in data.get("results", [])}

async def verify_fix():
    get_embedding_model()
    get_cross_encoder()
    get_bm25_index()
    
    baseline_data = load_baseline()
    test_suite = GROUND_TRUTH_DATA[:25]
    
    results = []
    
    for item in test_suite:
        q = item["question"]
        base_res = baseline_data.get(q, {})
        
        # LLM generated facts
        base_fact = base_res.get("factual_coverage", 0.0)
        
        retrieval = await retrieve_context(q)
        confidence = retrieval.confidence
        context = retrieval.context or ""
        
        # --- BEFORE FIX (Truncated) ---
        first_chunk = context.split("CONTENT:\n")[-1] if "CONTENT:\n" in context else "No data."
        before_answer = f"According to Dr. Khare's verified documents:\n\n• {first_chunk.strip()}"
        
        # --- AFTER FIX (Concatenated) ---
        chunks_text = []
        for block in context.split("[DOCUMENT]"):
            if "CONTENT:\n" in block:
                chunk = block.split("CONTENT:\n")[-1].strip()
                if chunk:
                    chunks_text.append(f"• {chunk}")
        combined_chunks = "\n\n".join(chunks_text) if chunks_text else "No data."
        after_answer = f"According to Dr. Khare's verified documents:\n\n{combined_chunks}"
        num_chunks = len(chunks_text)
        
        expected_facts = item["expected_facts"]
        
        hits_before = sum(1 for f in expected_facts if f.lower() in before_answer.lower())
        bypass_fact_before = hits_before / len(expected_facts) if expected_facts else 0.0
        
        hits_after = sum(1 for f in expected_facts if f.lower() in after_answer.lower())
        bypass_fact_after = hits_after / len(expected_facts) if expected_facts else 0.0
        
        bypassed = confidence >= 0.98
        
        results.append({
            "question": q,
            "confidence": confidence,
            "bypassed": bypassed,
            "base_fact": base_fact,
            "bypass_fact_before": bypass_fact_before,
            "bypass_fact_after": bypass_fact_after,
            "num_chunks": num_chunks
        })
        
    # Calculate Overall Metrics
    def calc_metrics(use_after):
        total_fact = 0
        bypassed_count = 0
        incorrect_bypasses = 0
        
        buckets = {"0.99 - 1.00": [], "0.97 - 0.99": [], "0.95 - 0.97": [], "0.90 - 0.95": [], "< 0.90": []}
        
        for d in results:
            fact = d["bypass_fact_after"] if (d["bypassed"] and use_after) else (d["bypass_fact_before"] if d["bypassed"] else d["base_fact"])
            total_fact += fact
            
            if d["bypassed"]:
                bypassed_count += 1
                if fact < 1.0:
                    incorrect_bypasses += 1
                    
            c = d["confidence"]
            if c >= 0.99: buckets["0.99 - 1.00"].append(fact)
            elif c >= 0.97: buckets["0.97 - 0.99"].append(fact)
            elif c >= 0.95: buckets["0.95 - 0.97"].append(fact)
            elif c >= 0.90: buckets["0.90 - 0.95"].append(fact)
            else: buckets["< 0.90"].append(fact)
            
        avg_fact = total_fact / 25
        fb_rate = incorrect_bypasses / bypassed_count if bypassed_count else 0.0
        
        return avg_fact, fb_rate, buckets
        
    before_fact, before_fb, _ = calc_metrics(use_after=False)
    after_fact, after_fb, after_buckets = calc_metrics(use_after=True)
    
    print("# Bypass Truncation Fix Validation\n")
    print("## 1. Metric Comparison (Threshold = 0.98)\n")
    print("| Metric | Before Fix | After Fix |")
    print("| --- | --- | --- |")
    print(f"| Factual Coverage | {before_fact:.2f} | {after_fact:.2f} |")
    print(f"| False Bypass Rate | {before_fb:.2f} | {after_fb:.2f} |")
    
    print("\n## 2. Confidence Bucket Analysis (After Fix)\n")
    print("| Confidence Range | Queries | Correct | Incorrect | Accuracy % |")
    print("| --- | --- | --- | --- | --- |")
    for name in ["0.99 - 1.00", "0.97 - 0.99", "0.95 - 0.97", "0.90 - 0.95", "< 0.90"]:
        items = after_buckets[name]
        total = len(items)
        correct = sum(1 for f in items if f >= 1.0)
        acc = (correct/total)*100 if total else 0.0
        print(f"| {name} | {total} | {correct} | {total-correct} | {acc:.1f}% |")
        
    print("\n## 3. Multi-Chunk Context Validation\n")
    print("| Query | Number of Retrieved Chunks Used | Correctness |")
    print("| --- | --- | --- |")
    for r in results:
        if r["bypassed"]:
            correct_str = "Correct" if r["bypass_fact_after"] >= 1.0 else "Incorrect"
            print(f"| {r['question']} | {r['num_chunks']} | {correct_str} |")

if __name__ == "__main__":
    asyncio.run(verify_fix())
