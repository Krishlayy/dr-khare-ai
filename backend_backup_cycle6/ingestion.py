import fitz
import os

def process_document(file_path):
    # Ensure the directory exists
    os.makedirs("backend/static/images", exist_ok=True)
    
    doc = fitz.open(file_path)
    print(f"Starting ingestion of {len(doc)} pages...")
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # 1. Extract Text (Save this to a text file for your AI brain)
        text = page.get_text()
        text_path = f"backend/static/text/page_{page_num+1}.txt"
        os.makedirs("backend/static/text", exist_ok=True)
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)
        
        # 2. Extract Images
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            try:
                # Handle images with various color spaces safely
                pix = fitz.Pixmap(doc, xref)
                if pix.colorspace and pix.colorspace.n > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                
                save_path = f"backend/static/images/page_{page_num+1}_img_{img_index+1}.png"
                pix.save(save_path)
            except Exception as e:
                print(f"Could not extract image on page {page_num+1}: {e}")
            
        print(f"Page {page_num+1} processed successfully.")

    doc.close()
    return "Ingestion Complete"
