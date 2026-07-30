import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.dependencies import require_admin
from backend.database.database import get_db
from backend.database.models import Document
from backend.database.schemas import DocumentResponse
from backend.rag.ingestion import delete_document_vectors

router = APIRouter()


@router.get("/", response_model=list[DocumentResponse])
def list_documents(
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(Document).order_by(Document.upload_date.desc()).all()


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_document_vectors(document.filename)

    if os.path.exists(document.filepath):
        os.remove(document.filepath)

    db.delete(document)
    db.commit()
    return {"message": f"Deleted {document.filename}"}
