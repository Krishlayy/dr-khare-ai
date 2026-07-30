import asyncio
import csv
import re
import math
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.rag.retrieval import retrieve_context

def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[\W_]+', '', text)
    return text

def token_overlap(expected, actual):
    stopwords = {"is", "a", "an", "the", "and", "or", "to", "of", "in", "on", "for", "with", "as", "by", "at"}
    exp_tokens = set(re.findall(r'\b\w+\b', expected.lower())) - stopwords
    act_tokens = set(re.findall(r'\b\w+\b', actual.lower()))
    if not exp_tokens: return True
    overlap = exp_tokens.intersection(act_tokens)
    return len(overlap) / len(exp_tokens)

def is_match(expected, chunk):
    c_exp = normalize_text(expected)
    c_ctx = normalize_text(chunk)
    return (c_exp in c_ctx) or (token_overlap(expected, chunk) >= 0.5)

async def main():
    questions = []
    with open('benchmark_results.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append((row['Question'], row['Expected Answer']))

    r1, r3, r5 = 0, 0, 0
    mrr_sum = 0
    ndcg_sum = 0
    total = len(questions)

    print(f"Evaluating {total} questions...")

    for i, (q, exp) in enumerate(questions):
        # We need to get up to top 5 chunks
        retrieval = await retrieve_context(q, top_k=5)
        chunks = [m.chunk for m in retrieval.matches]
        
        hit_rank = -1
        for rank, chunk in enumerate(chunks):
            if is_match(exp, chunk):
                hit_rank = rank + 1
                break
                
        if hit_rank == 1: r1 += 1
        if 1 <= hit_rank <= 3: r3 += 1
        if 1 <= hit_rank <= 5: r5 += 1
        
        if hit_rank > 0:
            mrr_sum += 1.0 / hit_rank
            ndcg_sum += 1.0 / math.log2(hit_rank + 1)
            
        if (i+1) % 50 == 0:
            print(f"Processed {i+1}/{total}")

    print("\n--- Retrieval Metrics ---")
    print(f"Recall@1: {r1/total*100:.2f}%")
    print(f"Recall@3: {r3/total*100:.2f}%")
    print(f"Recall@5: {r5/total*100:.2f}%")
    print(f"MRR: {mrr_sum/total:.4f}")
    print(f"nDCG@5: {ndcg_sum/total:.4f}")

if __name__ == "__main__":
    asyncio.run(main())
