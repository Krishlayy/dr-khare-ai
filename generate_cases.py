import json

test_cases = [
    # --- Category 1: Real Chatbot Queries (20) ---
    {
        "q": "What is Dr. Khare's full name?", 
        "required_keywords": ["supreet", "khare"], 
        "forbidden_keywords": ["cannot", "not available"],
        "expected_sources": ["biography.txt"],
        "type": "basic"
    },
    {
        "q": "From which medical college did Dr. Khare graduate?", 
        "required_keywords": ["afmc", "armed forces medical college"], 
        "forbidden_keywords": [],
        "expected_sources": ["education_training.txt"],
        "type": "basic"
    },
    {
        "q": "Where did Dr. Khare complete his Internal Medicine residency?", 
        "required_keywords": ["lompoc", "valley"], 
        "forbidden_keywords": [],
        "expected_sources": ["education_training.txt"],
        "type": "basic"
    },
    {
        "q": "What is his role at Signify Health?", 
        "required_keywords": ["managing director"], 
        "forbidden_keywords": [],
        "expected_sources": ["employment.txt"],
        "type": "basic"
    },
    {
        "q": "Has Dr. Khare published any research?", 
        "required_keywords": ["yes", "published", "journal", "research"], 
        "forbidden_keywords": ["no", "has not"],
        "expected_sources": ["publications.txt"],
        "type": "basic"
    },
    {
        "q": "What certifications does he hold?", 
        "required_keywords": ["bls", "acls", "board", "certified"], 
        "forbidden_keywords": [],
        "expected_sources": ["certifications.txt"],
        "type": "basic"
    },
    {
        "q": "When did he graduate MBBS?", 
        "required_keywords": ["2018"], 
        "forbidden_keywords": [],
        "expected_sources": ["education_training.txt"],
        "type": "basic"
    },
    {
        "q": "Is he a member of the American College of Physicians?", 
        "required_keywords": ["yes", "acp", "american college of physicians"], 
        "forbidden_keywords": ["no", "not a member"],
        "expected_sources": ["memberships_leadership.txt"],
        "type": "basic"
    },
    {
        "q": "What are all of his publications?", 
        "required_keywords": ["journal", "cureus"], 
        "forbidden_keywords": [],
        "expected_sources": ["publications.txt"],
        "type": "formatting"
    },
    {
        "q": "List his memberships.", 
        "required_keywords": ["american college of physicians", "acp", "ama", "ifmsa"], 
        "forbidden_keywords": [],
        "expected_sources": ["memberships_leadership.txt"],
        "type": "formatting"
    },
    {
        "q": "Where is his present mailing address?", 
        "required_keywords": ["street", "avenue", "road", "apt"], 
        "forbidden_keywords": [],
        "expected_sources": ["biography.txt"],
        "type": "formatting"
    },
    {
        "q": "List his employment history chronologically.", 
        "required_keywords": ["signify health", "lompoc"], 
        "forbidden_keywords": [],
        "expected_sources": ["employment.txt"],
        "type": "formatting"
    },
    {
        "q": "What volunteering has he done?", 
        "required_keywords": ["deep griha society", "prayas"], 
        "forbidden_keywords": [],
        "expected_sources": ["volunteer_community_service.txt"],
        "type": "formatting"
    },
    {
        "q": "Did he volunteer at Prayas?", 
        "required_keywords": ["yes", "prayas", "health camp"], 
        "forbidden_keywords": ["no"],
        "expected_sources": ["volunteer_community_service.txt"],
        "type": "basic"
    },
    {
        "q": "Is he board certified in internal medicine?", 
        "required_keywords": ["yes", "board", "certified"], 
        "forbidden_keywords": ["no"],
        "expected_sources": ["certifications.txt"],
        "type": "basic"
    },
    {
        "q": "Did he do a clerkship at Johns Hopkins?", 
        "required_keywords": ["yes", "johns hopkins", "clerkship"], 
        "forbidden_keywords": ["no"],
        "expected_sources": ["education_training.txt"],
        "type": "basic"
    },
    {
        "q": "What languages does he speak?", 
        "required_keywords": ["english", "hindi"], 
        "forbidden_keywords": ["not available"],
        "expected_sources": ["biography.txt"],
        "type": "basic"
    },
    {
        "q": "When did he work at Lompoc Valley Medical Center?", 
        "required_keywords": ["2022", "2025"], 
        "forbidden_keywords": ["not available"],
        "expected_sources": ["employment.txt"],
        "type": "basic"
    },
    {
        "q": "What awards has he won?", 
        "required_keywords": ["quiz", "winner"], 
        "forbidden_keywords": ["not available"],
        "expected_sources": ["awards.txt"],
        "type": "basic"
    },
    {
        "q": "Where did he work as a primary care physician?", 
        "required_keywords": ["joshua", "medical"], 
        "forbidden_keywords": ["not available"],
        "expected_sources": ["employment.txt"],
        "type": "basic"
    },

    # --- Category 2: Out of Domain / Refusal (10) ---
    {
        "q": "What is the capital of France?", 
        "required_keywords": ["discuss it with him"], 
        "forbidden_keywords": ["paris", "capital"],
        "expected_sources": [],
        "type": "out_of_domain"
    },
    {
        "q": "Who won the World Cup in 2022?", 
        "required_keywords": ["discuss it with him"], 
        "forbidden_keywords": ["argentina", "messi"],
        "expected_sources": [],
        "type": "out_of_domain"
    },
    {
        "q": "How do you treat diabetes?", 
        "required_keywords": ["discuss it with him"], 
        "forbidden_keywords": ["insulin", "metformin", "diet"],
        "expected_sources": [],
        "type": "out_of_domain"
    },
    {
        "q": "Can Dr. Khare prescribe me adderall?", 
        "required_keywords": ["discuss it with him"], 
        "forbidden_keywords": ["yes", "prescription"],
        "expected_sources": [],
        "type": "out_of_domain"
    },
    {
        "q": "Write a python script for a calculator.", 
        "required_keywords": ["discuss it with him"], 
        "forbidden_keywords": ["def", "python", "import"],
        "expected_sources": [],
        "type": "out_of_domain"
    },
    {
        "q": "Who is Dr. Khare's favorite actor?", 
        "required_keywords": ["discuss it with him"], 
        "forbidden_keywords": ["actor", "movie"],
        "expected_sources": [],
        "type": "out_of_domain"
    },
    {
        "q": "How do I fix a flat tire?", 
        "required_keywords": ["discuss it with him"], 
        "forbidden_keywords": ["tire", "car"],
        "expected_sources": [],
        "type": "out_of_domain"
    },
    {
        "q": "What is the meaning of life?", 
        "required_keywords": ["discuss it with him"], 
        "forbidden_keywords": ["42", "meaning"],
        "expected_sources": [],
        "type": "out_of_domain"
    },
    {
        "q": "Translate hello to Spanish.", 
        "required_keywords": ["discuss it with him"], 
        "forbidden_keywords": ["hola"],
        "expected_sources": [],
        "type": "out_of_domain"
    },
    {
        "q": "What is Einstein's theory of relativity?", 
        "required_keywords": ["discuss it with him"], 
        "forbidden_keywords": ["einstein", "physics", "e=mc2"],
        "expected_sources": [],
        "type": "out_of_domain"
    },

    # --- Category 3: Conversation Memory (5) ---
    {
        "q": "Who is Dr. Khare?", 
        "required_keywords": ["doctor", "physician", "supreet"], 
        "forbidden_keywords": ["not available"],
        "expected_sources": ["biography.txt"],
        "type": "memory_1",
        "session_group": "A"
    },
    {
        "q": "Where did he study?", 
        "required_keywords": ["afmc", "armed forces", "lompoc"], 
        "forbidden_keywords": ["who"],
        "expected_sources": ["education_training.txt"],
        "type": "memory_2",
        "session_group": "A"
    },
    {
        "q": "What degree did he earn there?", 
        "required_keywords": ["mbbs", "medicine", "bachelor"], 
        "forbidden_keywords": [],
        "expected_sources": ["education_training.txt"],
        "type": "memory_3",
        "session_group": "A"
    },
    {
        "q": "Who is he currently working for?", 
        "required_keywords": ["signify", "health"], 
        "forbidden_keywords": [],
        "expected_sources": ["employment.txt"],
        "type": "memory_4",
        "session_group": "B"
    },
    {
        "q": "What is his role there?", 
        "required_keywords": ["managing director"], 
        "forbidden_keywords": [],
        "expected_sources": ["employment.txt"],
        "type": "memory_5",
        "session_group": "B"
    }
]

with open("e2e_test_cases.json", "w") as f:
    json.dump(test_cases, f, indent=4)
print("Updated test cases generated.")
