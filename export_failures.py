import asyncio
import csv
import re
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.rag.retrieval import retrieve_context

def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[\W_]+', '', text)
    return text

def check_substring(expected, actual):
    return normalize_text(expected) in normalize_text(actual)

def token_overlap(expected, actual):
    stopwords = {"is", "a", "an", "the", "and", "or", "to", "of", "in", "on", "for", "with", "as", "by", "at", "yes", "no", "he", "she", "it", "dr", "khare"}
    exp_tokens = set(re.findall(r'\b\w+\b', expected.lower())) - stopwords
    act_tokens = set(re.findall(r'\b\w+\b', actual.lower()))
    if not exp_tokens: return True
    overlap = exp_tokens.intersection(act_tokens)
    return len(overlap) / len(exp_tokens)

async def main():
    failures = []
    with open('benchmark_results.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Pass'] == 'False':
                failures.append(row)

    counts = {
        "Correct Answer (evaluation mismatch)": 0,
        "Formatting Mismatch": 0,
        "Retrieval Failure": 0,
        "Missing Source Fact": 0,
        "Hallucination": 0,
        "Correct Refusal": 0
    }

    out_rows = []

    for row in failures:
        q = row['Question']
        exp = row['Expected Answer']
        act = row['Actual Answer']
        
        retrieval = await retrieve_context(q)
        sources_str = ", ".join(list(set([s['filename'] for s in retrieval.sources])))
        context_str = retrieval.context
        
        act_lower = act.lower()
        refusal_phrases = [
            'cannot find that information', 'do not contain any information', 
            'not provided', 'not explicitly mentioned', 'no information provided', 
            'does not provide', 'not mentioned', 'not stated'
        ]
        
        if any(p in act_lower for p in refusal_phrases):
            cat = "Correct Refusal"
        else:
            # Check if actual has some form of expected
            c_exp = normalize_text(exp)
            c_act = normalize_text(act)
            c_ctx = normalize_text(context_str)
            
            # Is the expected answer factually given?
            # E.g. "May 2015" vs "May 22, 2015"
            overlap_score = token_overlap(exp, act)
            if overlap_score >= 0.5 or c_exp in c_act or c_act in c_exp:
                # The model basically gave the right answer
                if overlap_score >= 0.75:
                    cat = "Correct Answer (evaluation mismatch)"
                else:
                    cat = "Formatting Mismatch"
            else:
                # The model gave a wrong answer. Why?
                # Did the context contain the expected answer?
                ctx_overlap = token_overlap(exp, context_str)
                if c_exp in c_ctx or ctx_overlap >= 0.5:
                    # The context HAD the answer, but the model ignored it or hallucinated something else
                    cat = "Hallucination"
                else:
                    # The context DID NOT have the answer.
                    if not retrieval.sources or retrieval.confidence < 0.40:
                        cat = "Retrieval Failure"
                    else:
                        cat = "Missing Source Fact"

        counts[cat] += 1
        out_rows.append([q, exp, act, sources_str, context_str, cat])

    with open('failed_questions_analysis.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Question", "Expected Answer", "Actual Answer", "Retrieved Sources", "Retrieved Context", "Failure Category"])
        writer.writerows(out_rows)

    print("--- Exact Category Counts ---")
    for k, v in counts.items():
        print(f"{k}: {v}")
        
    print("\n--- Top Retrieval Failures ---")
    rf_count = 0
    for r in out_rows:
        if r[5] == "Retrieval Failure":
            print(f"Q: {r[0]}")
            print(f"Expected: {r[1]}")
            print(f"Retrieved Sources: {r[3]}")
            print("---")
            rf_count += 1
            if rf_count >= 20:
                break

if __name__ == "__main__":
    asyncio.run(main())
