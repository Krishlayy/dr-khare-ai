import re
import sys

def parse_log(filepath):
    results = {}
    current_q = None
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            q_match = re.search(r"Testing: (.*)", line)
            if q_match:
                current_q = q_match.group(1).strip()
            
            lat_match = re.search(r"-> Latency: .*\| Recall: .*\| Hallucination: .*\| Factual: (.*)", line)
            if lat_match and current_q:
                results[current_q] = float(lat_match.group(1).strip())
            
            # For the new script output:
            if "-> Latency:" in line and "Factual:" not in line:
                # Need to grab from eval_results.json instead for 'After' if not in log
                pass
    return results

def main():
    before_log = r"C:\Users\hello\.gemini\antigravity\brain\beda72bb-6583-44e7-8a94-42ba9a6439d0\.system_generated\tasks\task-463.log"
    after_json = r"C:\Users\hello\dr_khare_ai\eval_results.json"
    
    before_results = parse_log(before_log)
    
    import json
    try:
        with open(after_json, "r", encoding="utf-8") as f:
            after_data = json.load(f)
            after_results = {r["question"]: r["factual_coverage"] for r in after_data["results"]}
            bypass_status = {r["question"]: r["bypassed"] for r in after_data["results"]}
    except Exception as e:
        print("Failed to load after json:", e)
        return
        
    print("Question | Before Factual | After Factual | Bypassed?")
    print("--- | --- | --- | ---")
    for q in before_results:
        b = before_results[q]
        a = after_results.get(q, "N/A")
        bypassed = bypass_status.get(q, "N/A")
        
        # Only show regressions
        if a != "N/A" and float(a) < b:
            print(f"{q} | {b} | {a} | {bypassed}")

if __name__ == "__main__":
    main()
