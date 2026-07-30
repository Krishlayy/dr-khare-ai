import fitz

def extract_pdf():
    pdf = fitz.open("storage/uploads/8142248431b7_MASTER CV.pdf")
    text = []
    for page in pdf:
        text.append(page.get_text())
    
    with open("cv_raw.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(text))
    print(f"Extracted {len(text)} pages.")

if __name__ == "__main__":
    extract_pdf()
