import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.api.dependencies import require_admin
from backend.core.config import settings
from backend.database.database import get_db
from backend.database.models import Document, User
from backend.database.schemas import (
    DocumentResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
)
from backend.services.document_pipeline import (
    get_stage_label,
    get_stage_progress,
    run_document_pipeline,
)

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@router.get("/history", response_model=list[DocumentResponse])
def upload_history(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(Document).order_by(Document.upload_date.desc()).all()


@router.get("/status/{document_id}", response_model=DocumentStatusResponse)
def get_upload_status(
    document_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    stage = document.processing_stage or document.status
    return DocumentStatusResponse(
        document_id=document.id,
        filename=document.filename,
        status=document.status,
        processing_stage=stage,
        stage_label=get_stage_label(stage),
        progress=get_stage_progress(stage),
        chunks_count=document.chunks_count,
        error_message=document.error_message,
    )


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX, and TXT files are supported",
        )

    allowed_mimes = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    }
    if file.content_type not in allowed_mimes:
        raise HTTPException(status_code=400, detail="Invalid content type")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    original_name = Path(file.filename).name
    stored_name = f"{uuid.uuid4().hex[:12]}_{original_name}"
    filepath = os.path.join(settings.UPLOAD_DIR, stored_name)

    import asyncio
    from backend.services.s3_service import s3_client, upload_file_to_s3
    
    if s3_client:
        # Upload directly to S3
        def save_file():
            pass # S3 upload handles the stream
        s3_path = await upload_file_to_s3(file.file, stored_name)
        if s3_path:
            filepath = s3_path
        else:
            # Fallback to local if S3 upload failed
            def save_file_local():
                file.file.seek(0)
                with open(filepath, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
            await asyncio.to_thread(save_file_local)
    else:
        # Local upload
        def save_file():
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        await asyncio.to_thread(save_file)

    document = Document(
        filename=original_name,
        filepath=filepath,
        filetype=suffix.lstrip("."),
        status="processing",
        processing_stage="extracting_text",
        uploaded_by_id=admin.id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    background_tasks.add_task(run_document_pipeline, document.id)

    return DocumentUploadResponse(
        document_id=document.id,
        filename=document.filename,
        status=document.status,
        processing_stage=document.processing_stage,
        message="File uploaded. Processing started.",
    )
