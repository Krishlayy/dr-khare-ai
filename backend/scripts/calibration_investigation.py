import os
import json
import asyncio
import sys
import numpy as np

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

async def run_investigation():
    get_embedding_model()
    get_cross_encoder()
    get_bm25_index()
    
    baseline_data = load_baseline()
    test_suite = GROUND_TRUTH_DATA[:25]
    
    results = []
    
    for item in test_suite:
        q = item["question"]
        base_res = baseline_data.get(q, {})
        base_fact = base_res.get("factual_coverage", 0.0)
        base_lat = base_res.get("latency", 10000.0)
        
        retrieval = await retrieve_context(q)
        
        if not retrieval.matches:
            continue
            
        top_match = retrieval.matches[0]
        confidence = retrieval.confidence
        raw_logit = top_match.raw_logit
        sigmoid_score = top_match.sigmoid_score
        
        context = retrieval.context or ""
        
        chunks_text = []
        for block in context.split("[DOCUMENT]"):
            if "CONTENT:\n" in block:
                chunk = block.split("CONTENT:\n")[-1].strip()
                if chunk:
                    chunks_text.append(f"• {chunk}")
        combined_chunks = "\n\n".join(chunks_text) if chunks_text else "No data."
        after_answer = f"According to Dr. Khare's verified documents:\n\n{combined_chunks}"
        
        expected_facts = item["expected_facts"]
        hits_after = sum(1 for f in expected_facts if f.lower() in after_answer.lower())
        bypass_fact = hits_after / len(expected_facts) if expected_facts else 0.0
        
        correct = bypass_fact >= 1.0
        
        results.append({
            "question": q,
            "raw_logit": raw_logit,
            "sigmoid": sigmoid_score,
            "confidence": confidence,
            "correct": correct,
            "bypass_fact": bypass_fact,
            "base_fact": base_fact,
            "base_lat": base_lat
        })
        
    print("# Confidence Calibration Investigation\n")
    
    print("## 1. Raw Logit vs Sigmoid vs Correctness (Sample)\n")
    print("| Question | Raw Logit | Sigmoid Score | Actual Correctness |")
    print("| --- | --- | --- | --- |")
    for r in results[:10]:
        print(f"| {r['question']} | {r['raw_logit']:.4f} | {r['sigmoid']:.4f} | {r['correct']} |")
        
    print("\n## 2. Sigmoid Calibration Table\n")
    print("| Sigmoid Range | Queries | Correct | Incorrect | Accuracy % |")
    print("| --- | --- | --- | --- | --- |")
    
    buckets = {"0.95 - 1.00": [], "0.90 - 0.95": [], "0.80 - 0.90": [], "< 0.80": []}
    for r in results:
        s = r["sigmoid"]
        if s >= 0.95: buckets["0.95 - 1.00"].append(r)
        elif s >= 0.90: buckets["0.90 - 0.95"].append(r)
        elif s >= 0.80: buckets["0.80 - 0.90"].append(r)
        else: buckets["< 0.80"].append(r)
        
    for name in ["0.95 - 1.00", "0.90 - 0.95", "0.80 - 0.90", "< 0.80"]:
        items = buckets[name]
        t = len(items)
        c = sum(1 for i in items if i["correct"])
        acc = (c/t)*100 if t else 0.0
        print(f"| {name} | {t} | {c} | {t-c} | {acc:.1f}% |")
        
    # Correlation
    logits = [r["raw_logit"] for r in results]
    corrects = [1.0 if r["correct"] else 0.0 for r in results]
    corr = np.corrcoef(logits, corrects)[0, 1] if len(logits) > 1 else 0.0
    print(f"\n**Pearson Correlation (Logit vs Correctness)**: {corr:.4f}\n")
    
    # Eval with Composite Confidence
    # Since confidence is now already updated in retrieval.py, `results` holds the new composite confidence
    # Let's evaluate using threshold 0.95
    # Wait, threshold is 0.98 in settings. But since composite confidence maxes out at:
    # 0.50 * 1.0 + 0.30 * 1.0 + 0.20 * 1.0 = 1.0
    # It might rarely hit 0.98. Let's see how many hit 0.98.
    
    threshold = 0.98
    bypassed_count = 0
    total_fact = 0
    total_lat = 0
    incorrect_bypasses = 0
    
    for r in results:
        if r["confidence"] >= threshold:
            bypassed_count += 1
            total_fact += r["bypass_fact"]
            total_lat += 600.0
            if r["bypass_fact"] < 1.0:
                incorrect_bypasses += 1
        else:
            total_fact += r["base_fact"]
            total_lat += r["base_lat"]
            
    pct = bypassed_count / 25
    avg_fact = total_fact / 25
    avg_lat = total_lat / 25
    fb_rate = incorrect_bypasses / bypassed_count if bypassed_count else 0.0
    
    print("## 3. Composite Confidence Prototype Metrics (Threshold = 0.98)\n")
    print(f"- **False Bypass Rate**: {fb_rate:.2f}")
    print(f"- **Factual Coverage**: {avg_fact:.2f}")
    print(f"- **Bypass Percentage**: {pct*100:.1f}%")
    print(f"- **Avg Latency**: {avg_lat:.1f}ms")

if __name__ == "__main__":
    asyncio.run(run_investigation())
