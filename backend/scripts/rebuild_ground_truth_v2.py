import json
import os
import sys

# Hand-curated 25 base questions entirely supported by the corpus files.
BASE_QUESTIONS = [
    # Biography (3 questions)
    {
        "category": "Biography",
        "question": "Who is Dr. Supreet Khare?",
        "expected_facts": [
            "physician",
            "Managing Director",
            "CEO",
            "Compendious Med Works"
        ],
        "expected_document": "doctor_profile.txt"
    },
    {
        "category": "Biography",
        "question": "Has Dr. Khare published any fiction novels?",
        "expected_facts": [
            "fiction novel",
            "Tales of Enkanto",
            "A Paradoxical Beginning"
        ],
        "expected_document": "doctor_profile.txt"
    },
    {
        "category": "Biography",
        "question": "What languages does Dr. Khare speak?",
        "expected_facts": [
            "English",
            "Hindi",
            "Urdu",
            "Punjabi",
            "Marathi",
            "Spanish"
        ],
        "expected_document": "doctor_profile.txt"
    },
    
    # Education (3 questions)
    {
        "category": "Education",
        "question": "Where did Dr. Khare complete his residency?",
        "expected_facts": [
            "University of Arizona",
            "Tucson",
            "Internal Medicine Residency"
        ],
        "expected_document": "clinic_info.txt"
    },
    {
        "category": "Education",
        "question": "What medical school did Dr. Khare attend for MBBS?",
        "expected_facts": [
            "Armed Forces Medical College",
            "AFMC",
            "Pune",
            "India"
        ],
        "expected_document": "clinic_info.txt"
    },
    {
        "category": "Education",
        "question": "What professional certificates does Dr. Khare hold?",
        "expected_facts": [
            "Professional Diploma in Clinical Research",
            "PDCR",
            "Professional Certificate in Pharmacovigilance",
            "PCPV"
        ],
        "expected_document": "clinic_info.txt"
    },
    
    # Clinical Experience (3 questions)
    {
        "category": "Clinical Experience",
        "question": "Where did Dr. Khare work before moving to the USA?",
        "expected_facts": [
            "Fortis Memorial Research Institute",
            "Medanta",
            "Paras Hospital"
        ],
        "expected_document": "career_timeline.txt"
    },
    {
        "category": "Clinical Experience",
        "question": "Did he have a role at Lompoc Valley Medical Center?",
        "expected_facts": [
            "Medical Director",
            "Occupational",
            "Environmental Medicine"
        ],
        "expected_document": "doctor_profile.txt"
    },
    {
        "category": "Clinical Experience",
        "question": "Where did he work as an Occupational Medicine Resident?",
        "expected_facts": [
            "University of Cincinnati",
            "Ohio"
        ],
        "expected_document": "doctor_profile.txt"
    },
    
    # Clinic Information (2 questions)
    {
        "category": "Clinic Information",
        "question": "Where is Compendious Med Works located?",
        "expected_facts": [
            "Tucson",
            "Arizona",
            "United States"
        ],
        "expected_document": "clinic_info.txt"
    },
    {
        "category": "Clinic Information",
        "question": "Where is Health First Multi Specialty Clinic located?",
        "expected_facts": [
            "Dwarka",
            "New Delhi"
        ],
        "expected_document": "career_timeline.txt"
    },
    
    # Research (3 questions)
    {
        "category": "Research",
        "question": "What clinical trials has Dr. Khare been involved in?",
        "expected_facts": [
            "Principal Investigator",
            "COPE Trial",
            "University of Arizona"
        ],
        "expected_document": "research_publications.txt"
    },
    {
        "category": "Research",
        "question": "Did Dr. Khare do any quality improvement research in the ICU?",
        "expected_facts": [
            "Diabetic Ketoacidosis",
            "Banner University Medical Center"
        ],
        "expected_document": "research_publications.txt"
    },
    {
        "category": "Research",
        "question": "Where was he a Research Fellow?",
        "expected_facts": [
            "Institute of Bioinformatics",
            "Johns Hopkins University"
        ],
        "expected_document": "publications.txt"
    },
    
    # Publications (2 questions)
    {
        "category": "Publications",
        "question": "What journal did he publish in regarding COVID-19?",
        "expected_facts": [
            "Cureus",
            "COVID-19 pulmonary complications",
            "steroids"
        ],
        "expected_document": "research_publications.txt"
    },
    {
        "category": "Publications",
        "question": "What was the topic of his paper 'Pseudodementia'?",
        "expected_facts": [
            "Pseudodementia",
            "peer-reviewed"
        ],
        "expected_document": "publications.txt"
    },
    
    # Awards (4 questions)
    {
        "category": "Awards",
        "question": "Did he receive the ICMR Research Scholarship?",
        "expected_facts": [
            "ICMR",
            "five consecutive years",
            "first and only undergraduate"
        ],
        "expected_document": "publications.txt"
    },
    {
        "category": "Awards",
        "question": "Who awarded him the Champion's Trophy?",
        "expected_facts": [
            "Nobel Laureate",
            "Dr. Robin Warren"
        ],
        "expected_document": "publications.txt"
    },
    {
        "category": "Awards",
        "question": "Has Dr. Khare received any academic gold medals?",
        "expected_facts": [
            "Gold Medals",
            "Pathology",
            "Microbiology",
            "MBBS"
        ],
        "expected_document": "awards_honors.txt"
    },
    {
        "category": "Awards",
        "question": "Was he nominated for a Young Scientist award?",
        "expected_facts": [
            "Brigadier S.K. Mazumdar",
            "Young Scientist Award"
        ],
        "expected_document": "doctor_profile.txt"
    },
    
    # Memberships (2 questions)
    {
        "category": "Memberships",
        "question": "What professional organizations is Dr. Khare a member of in the US?",
        "expected_facts": [
            "American College of Physicians",
            "ACP"
        ],
        "expected_document": "professional_memberships.txt"
    },
    {
        "category": "Memberships",
        "question": "Is Dr. Khare registered with any medical councils in India?",
        "expected_facts": [
            "Delhi Medical Council",
            "Rajasthan Medical Council",
            "Indian Medical Association"
        ],
        "expected_document": "professional_memberships.txt"
    },
    
    # Leadership (3 questions)
    {
        "category": "Leadership",
        "question": "What was his role during his residency at South Campus?",
        "expected_facts": [
            "Chief Resident",
            "South Campus",
            "University of Arizona"
        ],
        "expected_document": "career_timeline.txt"
    },
    {
        "category": "Leadership",
        "question": "Has he held any leadership positions at medical student associations?",
        "expected_facts": [
            "State President",
            "Medical Students Association of India",
            "MSAI"
        ],
        "expected_document": "doctor_profile.txt"
    },
    {
        "category": "Leadership",
        "question": "Did he have a leadership role at California Medical Behavioral Health?",
        "expected_facts": [
            "Chief Executive Officer",
            "CMBH"
        ],
        "expected_document": "doctor_profile.txt"
    }
]

variations_map = [
    lambda q: q, # Original
    lambda q: f"Can you tell me: {q}", # Variation 1
    lambda q: f"I want to know {q.lower().rstrip('?')}?", # Variation 2
    lambda q: f"Regarding Dr. Khare, {q.lower().rstrip('?')}?" # Variation 3
]

def main():
    if len(BASE_QUESTIONS) != 25:
        print(f"Error: Expected 25 base questions, got {len(BASE_QUESTIONS)}")
        sys.exit(1)
        
    new_suite = []
    
    # Generate exactly 100 questions
    for i in range(100):
        base_item = BASE_QUESTIONS[i % len(BASE_QUESTIONS)]
        variation_func = variations_map[i // len(BASE_QUESTIONS)]
        
        new_item = base_item.copy()
        new_item["question"] = variation_func(base_item["question"])
        new_suite.append(new_item)
        
    out_path = os.path.join(os.path.dirname(__file__), "ground_truth_100_v2.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(new_suite, f, indent=2)
        
    print(f"Generated {len(new_suite)} questions at {out_path}")

if __name__ == "__main__":
    main()
