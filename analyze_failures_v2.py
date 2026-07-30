import csv
import re

def reclassify(q, expected, actual):
    actual_lower = actual.lower()
    
    if "i cannot find that information in the source documents" in actual_lower:
        # Check if the expected answer is actually a refusal
        if "none" in expected.lower() or "not available" in expected.lower() or "not listed" in expected.lower():
            return "Correct Refusal"
        # Since grounding rejected it or retrieval failed, it's a retrieval failure or missing fact
        return "Retrieval Failure / Missing Fact"
        
    if "is not available in the source documents" in actual_lower:
        return "Retrieval Failure / Missing Fact"

    # Assume hallucination if it generated a claim that doesn't match expected
    return "Hallucination"

failures = []
with open("benchmark_results.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader) # skip header
    for row in reader:
        if len(row) < 5: continue
        q_id, q, expected, actual, passed = row
        if passed == "False":
            category = reclassify(q, expected, actual)
            failures.append({
                "Question": q,
                "Expected Answer": expected,
                "Actual Answer": actual,
                "Category": category
            })

with open("failed_questions_analysis_v2.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["Question", "Expected Answer", "Actual Answer", "Category"])
    writer.writeheader()
    writer.writerows(failures)

print(f"Processed {len(failures)} failures.")
