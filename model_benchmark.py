import asyncio
import re
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.rag.retrieval import retrieve_context
from backend.services.chat_service import build_doctor_kb_prompt
from backend.services.llm_service import generate_response
from backend.database.database import SessionLocal

def parse_questions(limit=25):
    questions = []
    with open("question_bank.txt", "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r'\*\*Q\d+\.\*\*', content)
    for block in blocks[1:]:
        q_match = re.search(r'Question:\s*(.*?)\n', block)
        a_match = re.search(r'Expected Answer:\s*(.*?)\n', block)
        if q_match and a_match:
            questions.append({
                "question": q_match.group(1).strip(),
                "expected": a_match.group(1).strip()
            })
            if len(questions) >= limit:
                break
    return questions

def check_correctness(expected, actual):
    expected_lower = expected.lower()
    actual_lower = actual.lower()
    if expected_lower in actual_lower: return True
    stopwords = {"is", "a", "an", "the", "and", "or", "to", "of", "in", "on", "for", "with", "as", "by", "at", "yes", "no", "he", "she", "it", "dr", "khare"}
    exp_tokens = set(re.findall(r'\b\w+\b', expected_lower)) - stopwords
    act_tokens = set(re.findall(r'\b\w+\b', actual_lower))
    if not exp_tokens: return True
    overlap = exp_tokens.intersection(act_tokens)
    return (len(overlap) / len(exp_tokens)) >= 0.75

def is_refusal(text):
    text_lower = text.lower()
    return ("not available" in text_lower or 
            "cannot find" in text_lower or 
            "not stated" in text_lower or 
            "does not contain" in text_lower or 
            "no information" in text_lower or 
            "not provided" in text_lower)

async def run_benchmark():
    models = ["qwen2.5:3b", "llama3.1:8b", "gemma3:12b"]
    questions = parse_questions(25)
    
    print(f"Loaded {len(questions)} questions.")
    
    results = {}
    
    for model in models:
        print(f"\n--- Benchmarking Model: {model} ---")
        
        latencies = []
        hallucinations = 0
        correct_refusals = 0
        false_refusals = 0
        correct_answers = 0
        
        # Grounding context status
        total_missing_context = 0
        total_present_context = 0
        
        for i, q_data in enumerate(questions):
            q = q_data["question"]
            expected = q_data["expected"]
            
            # Retrieve context once
            retrieval = await retrieve_context(q)
            context = retrieval.context
            
            # Determine if context actually contains the expected answer
            context_has_answer = check_correctness(expected, context)
            if context_has_answer:
                total_present_context += 1
            else:
                total_missing_context += 1
                
            prompt = build_doctor_kb_prompt(q, context, [])
            
            start_time = time.perf_counter()
            try:
                answer = await generate_response(prompt, model=model)
            except Exception as e:
                print(f"  [Q{i+1}] Error with model {model}: {e}")
                answer = ""
            end_time = time.perf_counter()
            
            latency = (end_time - start_time) * 1000
            if answer:
                latencies.append(latency)
            
            model_refused = is_refusal(answer)
            model_correct = check_correctness(expected, answer)
            
            if context_has_answer:
                if model_correct:
                    correct_answers += 1
                    status = "CORRECT"
                elif model_refused:
                    false_refusals += 1
                    status = "FALSE REFUSAL"
                else:
                    hallucinations += 1
                    status = "HALLUCINATION (ignored context)"
            else:
                if model_refused:
                    correct_refusals += 1
                    status = "CORRECT REFUSAL"
                elif model_correct:
                    # Model answered correctly despite context missing it -> External knowledge hallucination
                    hallucinations += 1
                    status = "HALLUCINATION (used external knowledge)"
                else:
                    hallucinations += 1
                    status = "HALLUCINATION (invented answer)"
                    
            print(f"  [{i+1}/25] {latency:.0f}ms | {status:35} | {q[:40]}...")

        avg_latency = sum(latencies)/len(latencies) if latencies else 0
        
        # Calculate rates
        total_q = len(questions)
        hallucination_rate = (hallucinations / total_q) * 100
        refusal_accuracy = (correct_refusals / total_missing_context * 100) if total_missing_context > 0 else 100
        retrieval_grounding_score = (correct_answers / total_present_context * 100) if total_present_context > 0 else 100
        
        results[model] = {
            "avg_latency_ms": avg_latency,
            "hallucination_rate": hallucination_rate,
            "refusal_accuracy": refusal_accuracy,
            "retrieval_grounding_score": retrieval_grounding_score,
            "correct_answers": correct_answers,
            "correct_refusals": correct_refusals,
            "false_refusals": false_refusals,
            "hallucinations": hallucinations
        }

    # Generate Markdown Report
    md = f"# Model Benchmark Comparison\n\n"
    md += f"Benchmarked on the first 25 questions from the validation set.\n\n"
    md += f"| Model | Avg Latency (ms) | Hallucination Rate | Refusal Accuracy | Retrieval Grounding Score |\n"
    md += f"|-------|------------------|--------------------|------------------|---------------------------|\n"
    for m in models:
        r = results[m]
        md += f"| {m} | {r['avg_latency_ms']:.0f}ms | {r['hallucination_rate']:.1f}% | {r['refusal_accuracy']:.1f}% | {r['retrieval_grounding_score']:.1f}% |\n"
    
    md += "\n## Definitions\n"
    md += "- **Hallucination Rate**: % of times the model invented an answer not in the context, or ignored context to provide an incorrect answer.\n"
    md += "- **Refusal Accuracy**: % of times the model correctly refused to answer when the context lacked the answer.\n"
    md += "- **Retrieval Grounding Score**: % of times the model correctly answered when the context *contained* the answer.\n"
    
    md += "\n## Recommendation\n"
    
    # Simple recommendation logic based on highest grounding and lowest hallucination
    best_model = min(models, key=lambda m: (results[m]['hallucination_rate'], -results[m]['retrieval_grounding_score']))
    md += f"**Recommended Model for Demo:** `{best_model}`\n"
    
    with open("MODEL_COMPARISON.md", "w", encoding="utf-8") as f:
        f.write(md)
        
    print("\nBenchmark complete! Results saved to MODEL_COMPARISON.md")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
