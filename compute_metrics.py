import json
import math

with open('eval_results_v2.json', 'r', encoding='utf-8') as f:
    eval_data = json.load(f)

with open('backend/scripts/ground_truth_100_v2.json', 'r', encoding='utf-8') as f:
    ground_truth = json.load(f)

gt_map = {item['question']: item['expected_document'] for item in ground_truth}

results = eval_data['results']
total = len(results)

recall_1_count = 0
recall_3_count = 0
recall_5_count = 0
mrr_sum = 0
ndcg_sum = 0

failures = []

for r in results:
    q = r['question']
    expected = gt_map.get(q)
    sources = r.get('sources', [])
    
    # rank is 1-indexed. Find the first occurrence.
    rank = -1
    for i, src in enumerate(sources):
        if src == expected:
            rank = i + 1
            break
            
    if rank == 1:
        recall_1_count += 1
    if 1 <= rank <= 3:
        recall_3_count += 1
    if 1 <= rank <= 5:
        recall_5_count += 1
        
    if rank > 0:
        mrr_sum += 1.0 / rank
        # nDCG calculation: DCG / IDCG. 
        # IDCG = 1 / log2(1 + 1) = 1 since there's 1 relevant doc.
        # DCG = 1 / log2(rank + 1)
        ndcg_sum += 1.0 / math.log2(rank + 1)
        
    if r['factual_coverage'] < 1.0 or r['hallucination'] > 0.0:
        failures.append({
            "question": q,
            "expected_document": expected,
            "retrieved_documents": sources,
            "answer": r['answer'],
            "factual": r['factual_coverage'],
            "hallucination": r['hallucination'],
            "recall_rank": rank
        })

print(f"Total: {total}")
print(f"Recall@1: {recall_1_count / total:.2f}")
print(f"Recall@3: {recall_3_count / total:.2f}")
print(f"Recall@5: {recall_5_count / total:.2f}")
print(f"MRR: {mrr_sum / total:.4f}")
print(f"nDCG: {ndcg_sum / total:.4f}")
print(f"Failures: {len(failures)}")

with open('eval_metrics_detailed.json', 'w', encoding='utf-8') as f:
    json.dump({
        "Recall@1": recall_1_count / total,
        "Recall@3": recall_3_count / total,
        "Recall@5": recall_5_count / total,
        "MRR": mrr_sum / total,
        "nDCG": ndcg_sum / total,
        "failures": failures
    }, f, indent=2)
