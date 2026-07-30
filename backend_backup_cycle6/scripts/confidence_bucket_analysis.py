import re

def main():
    log_file = r"C:\Users\hello\.gemini\antigravity\brain\beda72bb-6583-44e7-8a94-42ba9a6439d0\.system_generated\tasks\task-629.log"
    
    current_threshold = None
    current_q = None
    
    data = [] # List of dicts
    
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                thresh_match = re.search(r"Running Sweep for Threshold: (.*)", line)
                if thresh_match:
                    current_threshold = thresh_match.group(1).strip()
                    continue
                    
                q_match = re.search(r"\[\d+/\d+\] (.*)", line)
                if q_match:
                    current_q = q_match.group(1).strip()
                    continue
                    
                if "Latency:" in line and "Confidence:" in line and "Factual:" in line:
                    bypassed = "True" in line.split("|")[1]
                    conf_match = re.search(r"Confidence:\s*([0-9.]+)", line)
                    fact_match = re.search(r"Factual:\s*([0-9.]+)", line)
                    
                    if conf_match and fact_match and current_q and current_threshold:
                        conf = float(conf_match.group(1))
                        fact = float(fact_match.group(1))
                        data.append({
                            "threshold": current_threshold,
                            "question": current_q,
                            "bypassed": bypassed,
                            "confidence": conf,
                            "factual": fact,
                            "correct": fact >= 1.0
                        })
    except Exception as e:
        print("Log file not ready or error:", e)
        return

    # We only want to analyze the distinct queries once for the confidence buckets.
    # The confidence score for a query is deterministic and independent of the bypass threshold
    # because it is computed by retrieval before bypass evaluation.
    # Therefore, we can just grab the 25 distinct questions from the "1.00" baseline run.
    baseline_data = [d for d in data if d["threshold"] == "1.00"]
    
    # 1. Confidence Bucket Table
    buckets = {
        "0.99 - 1.00": [],
        "0.97 - 0.99": [],
        "0.95 - 0.97": [],
        "0.90 - 0.95": [],
        "< 0.90": []
    }
    
    for d in baseline_data:
        c = d["confidence"]
        if c >= 0.99:
            buckets["0.99 - 1.00"].append(d)
        elif c >= 0.97:
            buckets["0.97 - 0.99"].append(d)
        elif c >= 0.95:
            buckets["0.95 - 0.97"].append(d)
        elif c >= 0.90:
            buckets["0.90 - 0.95"].append(d)
        else:
            buckets["< 0.90"].append(d)
            
    print("## 1. Confidence Bucket Table\n")
    print("| Confidence Range | Queries | Correct | Incorrect | Accuracy % |")
    print("| --- | --- | --- | --- | --- |")
    
    bucket_stats = {}
    for name in ["0.99 - 1.00", "0.97 - 0.99", "0.95 - 0.97", "0.90 - 0.95", "< 0.90"]:
        items = buckets[name]
        total = len(items)
        correct = sum(1 for i in items if i["correct"])
        incorrect = total - correct
        acc = (correct / total * 100) if total > 0 else 0.0
        avg_conf = sum(i["confidence"] for i in items) / total if total > 0 else 0.0
        
        bucket_stats[name] = {"avg_conf": avg_conf, "acc": acc}
        print(f"| {name} | {total} | {correct} | {incorrect} | {acc:.1f}% |")
        
    print("\n## 3. Calibration Check\n")
    print("| Bucket | Average Confidence | Actual Accuracy |")
    print("| --- | --- | --- |")
    for name, stats in bucket_stats.items():
        print(f"| {name} | {stats['avg_conf']:.4f} | {stats['acc']:.1f}% |")
        
    # 2. Highest Confidence Failures
    # We will look at failures across the 0.98 run, which represents the regression state.
    run_098 = [d for d in data if d["threshold"] == "0.98"]
    failures = [d for d in run_098 if not d["correct"]]
    failures.sort(key=lambda x: x["confidence"], reverse=True)
    
    print("\n## 2. Highest Confidence Failures (Top 10)\n")
    print("| Question | Confidence | Threshold | Bypassed? | Correct? | Root Cause |")
    print("| --- | --- | --- | --- | --- | --- |")
    
    for f in failures[:10]:
        root_cause = "Unknown"
        if f["bypassed"]:
            root_cause = "Missing retrieval context (Bypass truncation)"
        else:
            root_cause = "LLM Hallucination / Evaluation Artifact"
            
        print(f"| {f['question']} | {f['confidence']:.4f} | {f['threshold']} | {f['bypassed']} | False | {root_cause} |")

if __name__ == "__main__":
    main()
