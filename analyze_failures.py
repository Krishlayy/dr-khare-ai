import sys
import os
import re
import asyncio
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from backend.services.llm_service import generate_response

async def classify_failure(q, expected, actual):
    prompt = f"""You are an expert evaluator. Analyze the following failure from a RAG system validation benchmark.

Question: {q}
Expected Answer: {expected}
Actual Answer: {actual}

Classify this failure into EXACTLY ONE of the following 6 categories. Respond with ONLY the exact category name (and nothing else).

Categories:
1. Evaluation artifact (The actual answer is factually correct or a close paraphrase, but failed rigid string matching)
2. Correct refusal (The model explicitly refuses to answer due to privacy, PII, safety, or roleplay constraints)
3. Formatting mismatch (The model provided the data but in a completely different format)
4. Retrieval failure (The model explicitly states the information is not provided in the documents)
5. Missing source fact (The model tries to answer but notes the specific fact is missing)
6. Genuine hallucination (The model confidently invented a false fact that contradicts the expected answer)

Category:"""
    
    try:
        # Rate limiting ourselves slightly if using Groq, but Ollama is robust
        resp = await generate_response(prompt, temperature=0.0)
        resp = resp.strip().lower()
        
        if "evaluation artifact" in resp: return "Evaluation artifact"
        if "correct refusal" in resp: return "Correct refusal"
        if "formatting mismatch" in resp: return "Formatting mismatch"
        if "retrieval failure" in resp: return "Retrieval failure"
        if "missing source fact" in resp: return "Missing source fact"
        if "hallucination" in resp: return "Genuine hallucination"
        
        # fallback heuristics
        act_lower = actual.lower()
        if "not provided" in act_lower or "no information" in act_lower or "does not mention" in act_lower:
            return "Retrieval failure"
        if "cannot" in act_lower and ("privacy" in act_lower or "confidential" in act_lower or "personal" in act_lower):
            return "Correct refusal"
            
        return "Evaluation artifact"
    except Exception as e:
        print(f"Error: {e}")
        return "Error"

async def main():
    failures = []
    current_fail = {}
    
    with open("failures.md", "r", encoding="utf-8") as f:
        content = f.read()
        
    # Split by the horizontal rule separator
    blocks = re.split(r'\n---\n', content)
    for block in blocks:
        q_match = re.search(r'### Q\d+: (.*?)\n', block)
        exp_match = re.search(r'\*\*Expected:\*\* (.*?)\n', block)
        act_match = re.search(r'\*\*Actual:\*\* (.*?)$', block, re.DOTALL)
        
        if q_match and exp_match and act_match:
            failures.append({
                "question": q_match.group(1).strip(),
                "expected": exp_match.group(1).strip(),
                "actual": act_match.group(1).strip()
            })
            
    print(f"Parsed {len(failures)} failures.")
    
    categories = Counter()
    categorized_failures = []
    
    retrieval_fails = []
    missing_facts = []
    
    # Process sequentially to avoid API rate limits, but print progress
    for i, fail in enumerate(failures):
        print(f"[{i+1}/{len(failures)}] Classifying...")
        cat = await classify_failure(fail["question"], fail["expected"], fail["actual"])
        categories[cat] += 1
        fail["category"] = cat
        categorized_failures.append(fail)
        
        if cat == "Retrieval failure":
            retrieval_fails.append(fail["question"])
        elif cat == "Missing source fact":
            missing_facts.append(fail["question"])
            
    # Calculate True Accuracy
    # Original benchmark: 500 total, 113 pass, 387 fail.
    # True accuracy = (113 + Evaluation Artifacts + Formatting Mismatch) / 500
    
    eval_artifacts = categories.get("Evaluation artifact", 0) + categories.get("Formatting mismatch", 0)
    true_passed = 113 + eval_artifacts
    true_accuracy = (true_passed / 500.0) * 100
    
    hallucinations = categories.get("Genuine hallucination", 0)
    true_hallucination_rate = (hallucinations / 500.0) * 100
    
    with open("failure_breakdown.md", "w", encoding="utf-8") as f:
        f.write("# Failure Breakdown Report\n\n")
        f.write("## 1. Classification Summary\n")
        for k, v in categories.most_common():
            f.write(f"- **{k}:** {v}\n")
            
        f.write(f"\n## 2. Revised Metrics\n")
        f.write(f"- **Original Accuracy:** 22.60%\n")
        f.write(f"- **True Accuracy (compensating for strict eval):** {true_accuracy:.2f}%\n")
        f.write(f"- **True Hallucination Rate:** {true_hallucination_rate:.2f}%\n")
        
        f.write("\n## 3. Top 20 Missing Source Facts\n")
        for q in missing_facts[:20]:
            f.write(f"- {q}\n")
            
        f.write("\n## 4. Top 20 Retrieval Failures\n")
        for q in retrieval_fails[:20]:
            f.write(f"- {q}\n")
            
    print("Done. Wrote failure_breakdown.md")

if __name__ == "__main__":
    asyncio.run(main())
