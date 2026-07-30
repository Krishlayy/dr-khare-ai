import os

def split_profile():
    with open("cv_raw.txt", "r", encoding="utf-8") as f:
        text = f.read()

    # Define boundaries (indices)
    sections = {
        "PERSONAL DETAILS:": "biography",
        "Education": "education_training",
        "Membership and Honorary/Professional Societies": "memberships_leadership",
        "Medical School Awards": "awards",
        "Medical Student Performance Evaluation": "biography",
        "Volunteer Experience": "volunteer_community_service",
        "Work Experience": "employment",
        "Research Experience": "research",
        "Publications": "publications",
        "Language Proficiency": "biography",
        "Other Awards/Accomplishments": "awards",
        "Hobbies & Interests": "biography",
        "Appendix 1": "certifications"
    }

    # Find the indices of each section header
    indices = []
    for header, category in sections.items():
        idx = text.find(header)
        if idx != -1:
            indices.append((idx, header, category))
    
    # Sort by index
    indices.sort(key=lambda x: x[0])
    
    # Extract blocks
    blocks = {}
    for i in range(len(indices)):
        start = indices[i][0]
        end = indices[i+1][0] if i + 1 < len(indices) else len(text)
        
        category = indices[i][2]
        content = text[start:end].strip()
        
        if category not in blocks:
            blocks[category] = []
        blocks[category].append(content)
        
    # Remove existing files
    upload_dir = "storage/uploads"
    for file in os.listdir(upload_dir):
        if file.endswith(".txt") and file != "knowledge_boundaries.txt":
            os.remove(os.path.join(upload_dir, file))
            
    # Write new files
    for category, contents in blocks.items():
        filepath = os.path.join(upload_dir, f"{category}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {category.upper().replace('_', ' ')}\n\n")
            f.write("\n\n".join(contents))
            
    # Also add the missing current roles to employment.txt since CV raw might not have the very latest 2025 ones prominently.
    # Actually, they are in cv_raw.txt (Lompoc Valley, Signify, CMBH). Let's make sure.
    
    print("Successfully split the profile into categorised files.")

if __name__ == "__main__":
    split_profile()
