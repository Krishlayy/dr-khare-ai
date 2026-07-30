import uuid
from typing import Callable

from backend.rag.document_processor import chunk_text, clean_text, extract_text
from backend.rag.embeddings import get_embedding_model
from backend.rag.retrieval import get_chroma_collection

StageCallback = Callable[[str], None]


def index_document_chunks(
    file_path: str,
    filename: str,
    chunks: list[str],
    on_stage: StageCallback | None = None,
) -> int:
    if not chunks:
        return 0

    if on_stage:
        on_stage("generating_embeddings")

    embeddings = get_embedding_model().encode(chunks).tolist()

    if on_stage:
        on_stage("indexing_knowledge")

    collection = get_chroma_collection()
    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [
        {"filename": filename, "source_path": file_path} for _ in chunks
    ]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )
    return len(chunks)


def build_chunks_from_file(
    file_path: str,
    on_stage: StageCallback | None = None,
) -> list[str]:
    if on_stage:
        on_stage("extracting_text")

    raw_text = extract_text(file_path)
    cleaned = clean_text(raw_text)

    if on_stage:
        on_stage("creating_chunks")

    return chunk_text(cleaned)


def delete_document_vectors(filename: str) -> None:
    collection = get_chroma_collection()
    existing = collection.get(where={"filename": filename})
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
