import fitz  # PyMuPDF

def process_large_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    print(f"Total pages: {len(doc)}")
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        # Extract images
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            # Save images to /static/images/
            pix = fitz.Pixmap(doc, xref)
            pix.save(f"backend/static/images/page_{page_num}_img_{img_index}.png")
            
        print(f"Processed page {page_num + 1}")

# Run this once on your 521-page doc
# process_large_pdf("path_to_your_521_page_doc.pdf")
