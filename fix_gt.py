import json

def fix_gt():
    path = "backend/scripts/ground_truth_100_v2.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for item in data:
        q = item["question"].lower()
        if "fortis" in q or "medanta" in q or "paras" in q or "health first" in q or "delhi medical council" in q or "rajasthan medical council" in q or "cope trial" in q or "diabetic ketoacidosis" in q or "chief resident" in q or "headshot" in q or "website" in q or "social media" in q or "npi" in q or "board certif" in q:
            item["expected_document"] = "knowledge_boundaries.txt"
        elif any(w in q for w in ["award", "honor", "prize", "medal", "scholarship"]):
            item["expected_document"] = "awards.txt"
        elif any(w in q for w in ["publish", "publication", "article", "journal", "paper"]):
            item["expected_document"] = "publications.txt"
        elif any(w in q for w in ["member", "society", "association"]):
            item["expected_document"] = "memberships_leadership.txt"
        elif any(w in q for w in ["education", "degree", "college", "university", "medical school", "residency", "mbbs"]):
            item["expected_document"] = "education_training.txt"
        elif any(w in q for w in ["leader", "director", "chair", "head", "work", "employ", "ceo"]):
            item["expected_document"] = "employment.txt"
        elif any(w in q for w in ["volunteer"]):
            item["expected_document"] = "volunteer_community_service.txt"
        elif any(w in q for w in ["research"]):
            item["expected_document"] = "research.txt"
        elif any(w in q for w in ["certificat", "course"]):
            item["expected_document"] = "certifications.txt"
        else:
            item["expected_document"] = "biography.txt"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print("Fixed ground truth.")

if __name__ == "__main__":
    fix_gt()
