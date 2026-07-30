import json
import os

path = "backend/scripts/ground_truth_100_v2.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

for item in data:
    q = item["question"].lower()
    if "fortis" in q or "medanta" in q or "paras" in q or "health first" in q or "delhi medical council" in q or "rajasthan medical council" in q or "cope trial" in q or "diabetic ketoacidosis" in q or "chief resident" in q or "headshot" in q or "website" in q or "social media" in q or "npi" in q or "board certif" in q:
        item["expected_document"] = "knowledge_boundaries.txt"
    else:
        item["expected_document"] = "complete_verified_profile.txt"

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)
print("Updated ground truth expected documents.")
