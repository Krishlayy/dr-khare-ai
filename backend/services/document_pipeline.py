from backend.database.database import SessionLocal
from backend.database.models import Document
from backend.rag.ingestion import build_chunks_from_file, index_document_chunks

STAGE_LABELS: dict[str, str] = {
    "uploading": "Uploading...",
    "extracting_text": "Extracting text...",
    "creating_chunks": "Creating chunks...",
    "generating_embeddings": "Generating embeddings...",
    "indexing_knowledge": "Indexing knowledge...",
    "completed": "Completed",
    "failed": "Failed to process document",
}

STAGE_PROGRESS: dict[str, int] = {
    "uploading": 10,
    "extracting_text": 30,
    "creating_chunks": 50,
    "generating_embeddings": 70,
    "indexing_knowledge": 90,
    "completed": 100,
    "failed": 0,
}


def get_stage_label(stage: str) -> str:
    return STAGE_LABELS.get(stage, stage.replace("_", " ").title())


def get_stage_progress(stage: str) -> int:
    return STAGE_PROGRESS.get(stage, 0)


def _update_stage(db, document: Document, stage: str) -> None:
    document.processing_stage = stage
    document.status = "processing"
    db.commit()


def run_document_pipeline(document_id: int) -> None:
    db = SessionLocal()
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        db.close()
        return

    def on_stage(stage: str) -> None:
        _update_stage(db, document, stage)

    try:
        chunks = build_chunks_from_file(document.filepath, on_stage=on_stage)

        if not chunks:
            raise ValueError("No extractable text found in document")

        chunk_count = index_document_chunks(
            document.filepath,
            document.filename,
            chunks,
            on_stage=on_stage,
        )

        from backend.rag.retrieval import rebuild_sparse_index
        rebuild_sparse_index()
        
        document.chunks_count = chunk_count
        document.status = "completed"
        document.processing_stage = "completed"
        document.error_message = None
        db.commit()
    except Exception as exc:
        document.status = "failed"
        document.processing_stage = "failed"
        document.error_message = str(exc)
        db.commit()
    finally:
        db.close()
