import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.database.models import ChatHistory, Document
from backend.rag.retrieval import get_chroma_stats
from backend.services.llm_service import get_ollama_status


def _dir_size_mb(path: str) -> float:
    total = 0
    p = Path(path)
    if not p.exists():
        return 0.0
    for f in p.rglob("*"):
        if f.is_file():
            total += f.stat().st_size
    return round(total / (1024 * 1024), 2)


import asyncio

async def get_dashboard_stats(db: Session) -> dict:
    chroma = get_chroma_stats()
    ollama = await get_ollama_status()

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    queries_today = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.role == "user",
            ChatHistory.created_at >= today_start,
        )
        .count()
    )

    assistant_sources = (
        db.query(ChatHistory.sources)
        .filter(ChatHistory.role == "assistant")
        .all()
    )
    response_times = []
    for (srcs,) in assistant_sources:
        if isinstance(srcs, dict) and srcs.get("response_time_ms"):
            response_times.append(srcs["response_time_ms"])

    avg_response = (
        round(sum(response_times) / len(response_times), 1)
        if response_times
        else 0.0
    )

    loop = asyncio.get_running_loop()
    upload_size = await loop.run_in_executor(None, _dir_size_mb, settings.UPLOAD_DIR)
    chroma_size = await loop.run_in_executor(None, _dir_size_mb, settings.CHROMA_PATH)
    storage_mb = upload_size + chroma_size
    
    chunks = chroma["chunks_count"]
    health = "Healthy" if chunks > 0 and ollama["reachable"] else "Degraded"

    return {
        "documents_indexed": db.query(Document).filter(Document.status == "completed").count(),
        "chunks_indexed": chunks,
        "storage_used_mb": storage_mb,
        "queries_today": queries_today,
        "average_response_time_ms": avg_response,
        "knowledge_base_health": health,
        "ollama_reachable": ollama["reachable"],
        "ollama_model": ollama["selected_model"],
        "chroma_documents": chroma["documents_count"],
        "chroma_chunks": chroma["chunks_count"],
    }
