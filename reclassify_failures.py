import csv
import re
import os

def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[\W_]+', '', text)
    return text

def token_overlap(expected, actual):
    stopwords = {"is", "a", "an", "the", "and", "or", "to", "of", "in", "on", "for", "with", "as", "by", "at", "yes", "no", "he", "she", "it", "dr", "khare"}
    exp_tokens = set(re.findall(r'\b\w+\b', expected.lower())) - stopwords
    act_tokens = set(re.findall(r'\b\w+\b', actual.lower()))
    if not exp_tokens: return True
    overlap = exp_tokens.intersection(act_tokens)
    return len(overlap) / len(exp_tokens)

# Load all source files to represent the KB
kb_content = {}
files = [
    "biography.txt", "employment.txt", "education_training.txt", "awards.txt", 
    "publications.txt", "research.txt", "memberships_leadership.txt", 
    "volunteer_community_service.txt", "certifications.txt", "knowledge_boundaries.txt"
]

for filename in files:
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            kb_content[filename] = f.read()
    else:
        # Check in knowledge_base dir if they are moved
        alt_path = os.path.join("storage", "uploads", filename)
        if os.path.exists(alt_path):
            with open(alt_path, 'r', encoding='utf-8') as f:
                kb_content[filename] = f.read()
        else:
            # Maybe inside the project dir directly
            kb_content[filename] = ""

# Load the CSV
rows = []
with open('failed_questions_analysis.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# Reclassify
counts = {
    "Correct Answer (evaluation mismatch)": 0,
    "Formatting Mismatch": 0,
    "Retrieval Failure": 0,
    "Missing Source Fact": 0,
    "Hallucination": 0,
    "Correct Refusal": 0
}

out_rows = []
for row in rows:
    cat = row["Failure Category"]
    exp = row["Expected Answer"]
    
    if cat == "Missing Source Fact":
        # Check if expected answer exists in any KB file
        c_exp = normalize_text(exp)
        found_in_kb = False
        target_file = ""
        for fname, content in kb_content.items():
            if not content: continue
            c_ctx = normalize_text(content)
            
            # Use same overlap logic
            ctx_overlap = token_overlap(exp, content)
            if c_exp in c_ctx or ctx_overlap >= 0.5:
                found_in_kb = True
                target_file = fname
                break
                
        if found_in_kb:
            cat = "Retrieval Failure"
            # We'll stick the target_file into a new column or just print it later
            row["Expected Source File"] = target_file
        else:
            row["Expected Source File"] = "N/A"
    else:
        row["Expected Source File"] = "N/A"

    counts[cat] += 1
    row["Failure Category"] = cat
    out_rows.append(row)

# Rewrite CSV with new column
fieldnames = ["Question", "Expected Answer", "Actual Answer", "Retrieved Sources", "Retrieved Context", "Failure Category", "Expected Source File"]
with open('failed_questions_analysis.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(out_rows)

print("--- Exact Category Counts ---")
for k, v in counts.items():
    print(f"{k}: {v}")

print("\n--- Top 20 Retrieval Failures ---")
rf_count = 0
for r in out_rows:
    if r["Failure Category"] == "Retrieval Failure":
        print(f"Q: {r['Question']}")
        print(f"Expected: {r['Expected Answer']}")
        print(f"Should be in: {r['Expected Source File']}")
        print(f"Actually retrieved: {r['Retrieved Sources']}")
        print("---")
        rf_count += 1
        if rf_count >= 20:
            break
