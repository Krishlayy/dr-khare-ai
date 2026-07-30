import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.dependencies import require_admin
from backend.database.database import get_db
from backend.database.models import ChatHistory, Document, User
from backend.database.schemas import (
    AnalyticsResponse,
    ChatHistoryResponse,
    DashboardResponse,
    DocumentChunkResponse,
    UserResponse,
)
from backend.rag.ingestion import delete_document_vectors
from backend.rag.retrieval import get_document_chunks
from backend.services.admin_service import get_dashboard_stats
from backend.services.document_pipeline import run_document_pipeline

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return DashboardResponse(**await get_dashboard_stats(db))


@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return AnalyticsResponse(
        total_documents=db.query(Document).count(),
        total_users=db.query(User).count(),
        total_chat_messages=db.query(ChatHistory).count(),
        system_status="Healthy",
    )


@router.get("/users", response_model=list[UserResponse])
def list_users(
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.get("/chat-logs", response_model=list[ChatHistoryResponse])
def list_chat_logs(
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = 100,
):
    return (
        db.query(ChatHistory)
        .order_by(ChatHistory.created_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/documents/{document_id}/chunks", response_model=list[DocumentChunkResponse])
def view_document_chunks(
    document_id: int,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = get_document_chunks(document.filename)
    return [DocumentChunkResponse(**c) for c in chunks]


@router.post("/documents/{document_id}/reindex")
def reindex_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_document_vectors(document.filename)
    document.status = "processing"
    document.processing_stage = "extracting_text"
    document.chunks_count = 0
    db.commit()

    background_tasks.add_task(run_document_pipeline, document.id)
    return {"message": f"Re-indexing started for {document.filename}"}
