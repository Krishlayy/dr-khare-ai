import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.database.database import SessionLocal
from backend.database.models import Document
from backend.services.document_pipeline import run_document_pipeline

db = SessionLocal()
folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../storage/uploads"))
print(f"Scanning folder: {folder}")

for filename in os.listdir(folder):
    if filename.endswith(".txt") or filename.endswith(".pdf"):
        existing = db.query(Document).filter(Document.filename == filename).first()
        if existing and existing.status == "completed":
            print(f"Skipping {filename} (already completed)")
            continue
            
        print(f"Ingesting {filename}...")
        if not existing:
            doc = Document(
                filename=filename,
                filepath=os.path.join(folder, filename),
                filetype=filename.split(".")[-1],
                status="processing",
                processing_stage="extracting_text",
                uploaded_by_id=1
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            doc_id = doc.id
        else:
            doc_id = existing.id
            
        try:
            run_document_pipeline(doc_id)
            print(f"Done {filename}")
        except Exception as e:
            print(f"Failed {filename}: {e}")
