import asyncio
import re
import csv
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.database.database import SessionLocal
from backend.services.chat_service import process_chat

def parse_questions():
    questions = []
    with open("question_bank.txt", "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r'\*\*Q\d+\.\*\*', content)
    for block in blocks[1:]: # skip preamble
        q_match = re.search(r'Question:\s*(.*?)\n', block)
        a_match = re.search(r'Expected Answer:\s*(.*?)\n', block)
        if q_match and a_match:
            questions.append({
                "question": q_match.group(1).strip(),
                "expected_answer": a_match.group(1).strip()
            })
    return questions

def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[\W_]+', '', text)
    return text

def check_correctness(expected, actual):
    expected_lower = expected.lower()
    actual_lower = actual.lower()
    
    # 1. Direct substring
    if expected_lower in actual_lower:
        return True
        
    # 2. Normalized substring (ignores spaces/punctuation)
    if normalize_text(expected) in normalize_text(actual):
        return True
        
    # 3. Token overlap
    stopwords = {"is", "a", "an", "the", "and", "or", "to", "of", "in", "on", "for", "with", "as", "by", "at", "yes", "no", "he", "she", "it", "dr", "khare"}
    exp_tokens = set(re.findall(r'\b\w+\b', expected_lower)) - stopwords
    act_tokens = set(re.findall(r'\b\w+\b', actual_lower))
    
    if not exp_tokens:
        return True
        
    overlap = exp_tokens.intersection(act_tokens)
    ratio = len(overlap) / len(exp_tokens)
    
    # If 75% of meaningful words from expected answer are in actual answer
    return ratio >= 0.75

async def run_validation(limit=None):
    questions = parse_questions()
    if limit is not None:
        questions = questions[:limit]
        
    print(f"Loaded {len(questions)} questions from bank.")
    
    db = SessionLocal()
    session_id = "validation_run"
    
    passed = 0
    total_failures = 0
    
    # Initialize files
    with open("benchmark_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Question", "Expected Answer", "Actual Answer", "Pass"])
        
    with open("failures.md", "w", encoding="utf-8") as f:
        f.write("# Validation Failures\n\n")
        
    import time
    start_time = time.time()
    
    # Process sequentially to avoid overwhelming rate limits or local GPU
    for i, item in enumerate(questions):
        q = item["question"]
        expected = item["expected_answer"]
        
        print(f"[{i+1}/{len(questions)}] Q: {q}")
        q_start = time.time()
        
        is_correct = False
        actual = ""
        
        try:
            resp = await process_chat(db, q, session_id, mode="doctor")
            actual = resp.get("response", "")
            is_correct = check_correctness(expected, actual)
            if is_correct:
                passed += 1
            else:
                total_failures += 1
        except Exception as e:
            actual = f"ERROR: {str(e)}"
            total_failures += 1
            print(f"   -> FAILED (Exception: {e})")
            
        q_time = time.time() - q_start
        status_str = "PASS" if is_correct else "FAIL"
        print(f"   -> {status_str} ({q_time:.2f}s)")
        
        # Incremental write CSV
        with open("benchmark_results.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([i + 1, q, expected, actual, is_correct])
            
        # Incremental write failure
        if not is_correct:
            with open("failures.md", "a", encoding="utf-8") as f:
                f.write(f"### Q{i+1}: {q}\n")
                f.write(f"**Expected:** {expected}\n\n")
                f.write(f"**Actual:** {actual}\n\n")
                f.write("---\n\n")
                
    db.close()
    
    end_time = time.time()
    duration = end_time - start_time
            
    # Write validation_report.md
    with open("validation_report.md", "w", encoding="utf-8") as f:
        f.write("# RAG Chatbot Validation Report\n\n")
        f.write(f"**Total Questions:** {len(questions)}\n")
        f.write(f"**Passed:** {passed}\n")
        f.write(f"**Failed:** {total_failures}\n")
        f.write(f"**Accuracy:** {(passed/len(questions))*100:.2f}%\n" if len(questions) > 0 else "")
        f.write(f"**Duration:** {duration:.2f} seconds (avg {duration/len(questions):.2f}s per query)\n" if len(questions) > 0 else "")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Limit number of questions")
    args = parser.parse_args()
    asyncio.run(run_validation(limit=args.limit))
