from fastapi import APIRouter, Depends

from backend.api.dependencies import require_admin
from backend.database.schemas import (
    DebugChromaResponse,
    DebugRetrieveRequest,
    DebugRetrieveResponse,
    DebugSearchMatch,
    DebugSearchRequest,
    DebugSearchResponse,
    OllamaStatusResponse,
    SampleChunk,
)
from backend.rag.embeddings import EMBEDDING_DIMENSION
from backend.rag.retrieval import COLLECTION_NAME, debug_search, get_chroma_stats, retrieve_context
from backend.services.llm_service import get_ollama_status

router = APIRouter()


@router.get("/chroma", response_model=DebugChromaResponse)
def chroma_status(admin=Depends(require_admin)):
    stats = get_chroma_stats(sample_size=5)
    return DebugChromaResponse(
        collection_name=COLLECTION_NAME,
        documents_count=stats["documents_count"],
        chunks_count=stats["chunks_count"],
        embedding_dimension=EMBEDDING_DIMENSION,
        sample_chunks=[SampleChunk(**chunk) for chunk in stats["sample_chunks"]],
    )


@router.post("/search", response_model=DebugSearchResponse)
def search_knowledge_base(
    request: DebugSearchRequest,
    admin=Depends(require_admin),
):
    matches = debug_search(request.query, limit=10)
    return DebugSearchResponse(matches=matches)


@router.post("/retrieve", response_model=DebugRetrieveResponse)
def debug_retrieve(
    request: DebugRetrieveRequest,
    admin=Depends(require_admin),
):
    result = retrieve_context(request.query)
    return DebugRetrieveResponse(
        query=request.query,
        confidence=result.confidence,
        use_web_fallback=result.use_web_fallback,
        context_preview=(result.context or "")[:500],
        matches=[
            DebugSearchMatch(
                score=m.score,
                document=m.document,
                chunk=m.chunk,
            )
            for m in result.matches
        ],
    )


@router.get("/ollama", response_model=OllamaStatusResponse)
async def ollama_status(admin=Depends(require_admin)):
    status = await get_ollama_status()
    return OllamaStatusResponse(**status)
