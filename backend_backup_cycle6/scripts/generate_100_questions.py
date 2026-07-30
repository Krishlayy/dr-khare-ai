import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.scripts.eval_suite import GROUND_TRUTH

variations_map = [
    lambda q: q, # Original
    lambda q: f"Can you tell me: {q}", # Variation 1
    lambda q: f"I want to know {q.lower()}", # Variation 2
    lambda q: f"Regarding Dr. Khare, {q.lower()}" # Variation 3
]

def main():
    new_suite = []
    
    # Generate exactly 100 questions
    for i in range(100):
        base_item = GROUND_TRUTH[i % len(GROUND_TRUTH)]
        variation_func = variations_map[i // len(GROUND_TRUTH)]
        
        new_item = base_item.copy()
        new_item["question"] = variation_func(base_item["question"])
        new_suite.append(new_item)
        
    out_path = os.path.join(os.path.dirname(__file__), "ground_truth_100.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(new_suite, f, indent=2)
        
    print(f"Generated {len(new_suite)} questions at {out_path}")

if __name__ == "__main__":
    main()
