import chromadb
from chromadb.config import Settings as ChromaSettings
from dataclasses import dataclass, field
import asyncio

from backend.core.config import settings
from backend.core.logging_config import get_logger
from backend.rag.embeddings import encode_text

logger = get_logger("rag.retrieval")

COLLECTION_NAME = "dr_khare_docs"

_chroma_client: chromadb.ClientAPI | None = None
_collection = None

from sentence_transformers import CrossEncoder
from rank_bm25 import BM25Okapi

_cross_encoder = None
def get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        _cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    return _cross_encoder

_bm25_corpus = None
_bm25_index = None
_bm25_count = -1

def get_bm25_index():
    global _bm25_corpus, _bm25_index, _bm25_count
    collection = get_chroma_collection()
    count = collection.count()

    if _bm25_index is not None and count == _bm25_count:
        return _bm25_index, _bm25_corpus

    logger.info("Building BM25 index over %d docs...", count)
    if count == 0:
        return None, []

    results = collection.get(include=["documents", "metadatas"])
    docs = results.get("documents", [])
    metas = results.get("metadatas", [])

    _bm25_corpus = [{"chunk": d, "metadata": m} for d, m in zip(docs, metas) if d]
    tokenized = [d["chunk"].lower().split() for d in _bm25_corpus]
    _bm25_index = BM25Okapi(tokenized)
    _bm25_count = count

    logger.info("BM25 index built with %d chunks.", len(_bm25_corpus))
    return _bm25_index, _bm25_corpus

def rebuild_sparse_index():
    """Forces a rebuild of the BM25 index on the next call to get_bm25_index()."""
    global _bm25_index, _bm25_count
    _bm25_index = None
    _bm25_count = -1
    logger.info("BM25 index cache invalidated.")

SOURCE_PRIORITY = {
    "biography.txt": 1.0,
    "employment.txt": 1.0,
    "education_training.txt": 0.95,
    "awards.txt": 0.95,
    "publications.txt": 0.90,
    "research.txt": 0.90,
    "memberships_leadership.txt": 0.85,
    "volunteer_community_service.txt": 0.80,
    "certifications.txt": 0.50,
}

# ---------------------------------------------------------------------------
# Soft metadata boosting
# ---------------------------------------------------------------------------
# Related categories that receive a partial boost when the primary category
# matches. Never used to *exclude* any chunk.
CATEGORY_RELATIONS: dict[str, list[str]] = {
    "employment": ["education", "biography"],
    "education": ["employment", "research"],
    "research": ["publication"],
    "publication": ["research"],
    "membership": ["volunteer"],
    "volunteer": ["membership"],
    "awards": ["publication"],
    "certification": ["education", "employment"],
    "biography": ["employment", "education"],
}

SOFT_BOOST_SAME: float = 0.10      # chunk category == predicted category
SOFT_BOOST_RELATED: float = 0.05  # chunk category is a related category
SOFT_BOOST_NONE: float = 0.00     # unrelated


def classify_query(query: str) -> str | None:
    """Predict the most likely knowledge-base category for a query.
    Returns None when no strong signal is detected."""
    ql = query.lower()

    if "acls" in ql or "bls" in ql or "certifi" in ql or "dea" in ql or "license" in ql or "course" in ql:
        return "certification"
    if "research" in ql or "icmr" in ql or "study" in ql or "project" in ql or "trial" in ql or "lab" in ql:
        return "research"
    if "member" in ql or "society" in ql or "association" in ql or "ifmsa" in ql or "acp" in ql or "ama" in ql:
        return "membership"
    if "publish" in ql or "publication" in ql or "article" in ql or "journal" in ql or "paper" in ql or "author" in ql:
        return "publication"
    if "volunteer" in ql or "community" in ql or "service" in ql or "ngo" in ql or "prayas" in ql or "deep griha" in ql:
        return "volunteer"
    if "award" in ql or "honor" in ql or "prize" in ql or "recognition" in ql or "medal" in ql or "scholarship" in ql or "won" in ql or "quiz" in ql:
        return "awards"
    if "education" in ql or "degree" in ql or "college" in ql or "university" in ql or "school" in ql or "residency" in ql or "mbbs" in ql or "graduate" in ql:
        return "education"
    if "employment" in ql or "work" in ql or "position" in ql or "job" in ql or "clinic" in ql or "hospital" in ql or "director" in ql or "ceo" in ql or "role" in ql:
        return "employment"
    if "who" in ql or "background" in ql or "born" in ql or "profile" in ql or "about" in ql or "language" in ql or "speak" in ql or "hobby" in ql:
        return "biography"

    return None


def get_metadata_boost(predicted_category: str | None, chunk_category: str | None) -> float:
    """Return a soft boost value based on category alignment.
    Never returns a negative value — no chunk is ever penalised."""
    if predicted_category is None or chunk_category is None:
        return SOFT_BOOST_NONE
    if chunk_category == predicted_category:
        return SOFT_BOOST_SAME
    related = CATEGORY_RELATIONS.get(predicted_category, [])
    if chunk_category in related:
        return SOFT_BOOST_RELATED
    return SOFT_BOOST_NONE


def get_query_boosts(query: str) -> dict[str, float]:
    """Return source-priority multipliers for the given query."""
    ql = query.lower()
    boosts: dict[str, float] = {}

    # Biography intent override — kept for strong priors only
    if "who is" in ql or "tell me about" in ql or "introduce" in ql:
        boosts["biography.txt"] = 1.5
        boosts["employment.txt"] = 1.3

    return boosts


@dataclass
class RetrievedChunk:
    document: str
    chunk: str
    score: float
    raw_logit: float = 0.0
    sigmoid_score: float = 0.0
    retrieval_agreement: float = 0.0
    source_quality: float = 0.0


@dataclass
class RetrievalResult:
    query: str
    matches: list[RetrievedChunk] = field(default_factory=list)
    context: str | None = None
    confidence: float = 0.0
    use_web_fallback: bool = False

    @property
    def sources(self) -> list[dict]:
        return [
            {
                "filename": m.document,
                "document": m.document,
                "score": round(m.score, 4),
                "chunk_preview": m.chunk[:200],
            }
            for m in self.matches
        ]


def get_chroma_collection():
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PATH,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _score_from_distance(distance: float) -> float:
    return round(max(0.0, 1.0 - distance), 4)


def _expand_query(query: str) -> list[str]:
    """
    Generate 3 rewritten versions of the query for multi-query retrieval.
    Rules-based — no LLM call, zero latency.
    Each version targets a different semantic angle of the same question.
    """
    q = query.strip()
    variants = [q]  # always include original

    ql = q.lower()

    # Strip question marks / filler for a keyword variant
    keyword = (
        q.replace("?", "")
         .replace("!", "")
         .replace("Can you tell me", "")
         .replace("Please tell me", "")
         .replace("I want to know", "")
         .replace("What is", "")
         .replace("What are", "")
         .replace("Who is", "")
         .replace("Where did", "")
         .replace("How did", "")
         .strip()
    )
    if keyword and keyword.lower() != ql:
        variants.append(keyword)

    # Add a "Dr. Khare" contextualiser if not already present
    if "khare" not in ql and "supreet" not in ql:
        variants.append(f"Dr. Khare {q}")
    else:
        # Add a "background and experience" suffix for identity queries
        if any(w in ql for w in ["who", "what", "background", "about", "profile"]):
            variants.append(f"{q} qualifications credentials education biography aamc id personal details")

    # Always have exactly 3 variants (pad with rephrasing if needed)
    if len(variants) < 3:
        variants.append(f"{q} details information")

    return variants[:3]


def search_chunks(query: str, limit: int | None = None) -> list[RetrievedChunk]:
    """Single-query search. Returns deduplicated chunks sorted by score."""
    limit = limit or settings.TOP_K_CHUNKS
    collection = get_chroma_collection()

    if collection.count() == 0 or not query.strip():
        logger.warning("ChromaDB empty or blank query")
        return []

    query_vector = encode_text(query)
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=min(limit, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    matches: list[RetrievedChunk] = []
    seen_chunks: set[str] = set()

    for text, metadata, distance in zip(documents, metadatas, distances):
        chunk = (text or "").strip()
        if not chunk or chunk in seen_chunks:
            continue
        seen_chunks.add(chunk)
        matches.append(
            RetrievedChunk(
                document=(metadata or {}).get("filename", "Unknown"),
                chunk=chunk,
                score=_score_from_distance(distance),
            )
        )

    logger.info(
        "ChromaDB search query=%r results=%d top_score=%s",
        query[:80],
        len(matches),
        matches[0].score if matches else None,
    )
    return matches


async def search_chunks_multi(query: str, limit: int | None = None) -> list[RetrievedChunk]:
    limit = limit or settings.TOP_K_CHUNKS
    collection = get_chroma_collection()
    
    if collection.count() == 0 or not query.strip():
        logger.warning("ChromaDB empty or blank query (multi)")
        return []

    from backend.rag.embeddings import encode_text_async
    variants = _expand_query(query)
    logger.info("Multi-query variants: %s", [v[:60] for v in variants])

    query_vectors = await asyncio.gather(*[encode_text_async(v) for v in variants])
    
    loop = asyncio.get_running_loop()
    
    # ── Soft metadata boosting: NO hard where= filter. Search ALL chunks. ──────
    predicted_category = classify_query(query)

    def _do_vector():
        return collection.query(
            query_embeddings=query_vectors,
            n_results=min(limit + 40, collection.count()),
            include=["documents", "metadatas", "distances"],
            # No where= filter — soft boosting applied during reranking
        )

    vector_results = await loop.run_in_executor(None, _do_vector)

    rrf_scores: dict[str, float] = {}
    chunk_data: dict[str, dict] = {}
    k = 60

    all_docs = vector_results.get("documents", [])
    all_meta = vector_results.get("metadatas", [])
    for docs, metas in zip(all_docs, all_meta):
        for rank, (text, meta) in enumerate(zip(docs, metas)):
            if not text:
                continue
            text = text.strip()
            chunk_data[text] = meta
            rrf_scores[text] = rrf_scores.get(text, 0) + 1.0 / (k + rank + 1)

    def _do_bm25():
        bm25, corpus = get_bm25_index()
        if not bm25:
            return []
        results = []
        for v in variants:
            tokenized = v.lower().split()
            scores = bm25.get_scores(tokenized)
            # Search ALL corpus entries — no hard category exclusion
            top_n = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit + 40]
            results.append([corpus[i] for i in top_n])
        return results

    bm25_results = await loop.run_in_executor(None, _do_bm25)
    for res_list in bm25_results:
        for rank, item in enumerate(res_list):
            text = item["chunk"].strip()
            if not text: continue
            chunk_data[text] = item["metadata"]
            rrf_scores[text] = rrf_scores.get(text, 0) + 1.0 / (k + rank + 1)
            
    if not rrf_scores:
        return []
        
    boosts = get_query_boosts(query)
    for text in list(rrf_scores.keys()):
        meta = chunk_data.get(text, {})
        filename = (meta or {}).get("filename", "Unknown")
        cat_boost = boosts.get(filename, 1.0)
        rrf_scores[text] *= cat_boost
        
    # Phase 4: Cap CrossEncoder candidate pool to 20
    top_rrf = sorted(rrf_scores.keys(), key=lambda t: rrf_scores[t], reverse=True)[:20]
    
    def _do_rerank():
        encoder = get_cross_encoder()
        pairs = [[query, text] for text in top_rrf]
        return encoder.predict(pairs).tolist()
        
    rerank_scores = await loop.run_in_executor(None, _do_rerank)
    
    final_chunks = []
    import math

    # Retrieval agreement — proportion of CrossEncoder-positive chunks
    positive_chunks = sum(1 for s in rerank_scores if s > 0.0)
    retrieval_agreement = positive_chunks / len(rerank_scores) if rerank_scores else 0.0

    for text, ce_score in zip(top_rrf, rerank_scores):
        meta = chunk_data.get(text, {})
        filename = (meta or {}).get("filename", "Unknown")
        chunk_category = (meta or {}).get("category", None)
        priority = SOURCE_PRIORITY.get(filename, 0.6)
        source_boost = boosts.get(filename, 1.0)   # biography/employment intent boost

        try:
            sigmoid_score = 1.0 / (1.0 + math.exp(-ce_score))
        except OverflowError:
            sigmoid_score = 0.0 if ce_score < 0 else 1.0

        base_rrf = rrf_scores.get(text, 0.0)

        # ── Soft Metadata Boosting formula ────────────────────────────────────
        # semantic_score  = CrossEncoder sigmoid * source quality priority
        # crossencoder    = scaled RRF (approximation of retrieval consensus)
        # metadata_boost  = +0.10 same, +0.05 related, +0.00 unrelated
        metadata_boost = get_metadata_boost(predicted_category, chunk_category)
        semantic_score = sigmoid_score * priority * source_boost
        cross_component = base_rrf * 5.0
        final_score = (
            semantic_score * 0.6
            + cross_component * 0.3
            + metadata_boost * 0.1
            + retrieval_agreement * 0.05  # kept as minor tie-breaker
        )

        final_chunks.append(RetrievedChunk(
            document=filename,
            chunk=text,
            score=final_score,
            raw_logit=ce_score,
            sigmoid_score=sigmoid_score,
            retrieval_agreement=retrieval_agreement,
            source_quality=priority,
        ))
        
    merged = sorted(final_chunks, key=lambda x: x.score, reverse=True)[:limit]
    
    logger.info("Hybrid search: variants=%d top_score=%s", len(variants), merged[0].score if merged else None)
    return merged


async def retrieve_context(query: str, top_k: int | None = None) -> RetrievalResult:
    """
    Full retrieval pipeline with multi-query expansion and re-ranking.
    Uses web fallback only when best score < WEB_FALLBACK_THRESHOLD.
    """
    top_k = top_k or settings.TOP_K_CHUNKS

    # Use multi-query for better recall
    matches = await search_chunks_multi(query, limit=top_k)

    result = RetrievalResult(query=query, matches=matches)

    if not matches:
        result.use_web_fallback = True
        result.confidence = 0.0
        logger.info("No matches found. Enabling web fallback.")
        return result

    best_score = matches[0].score
    result.confidence = best_score

    if best_score < settings.WEB_FALLBACK_THRESHOLD:
        result.use_web_fallback = True
        logger.info(
            "Best score %.4f below threshold %.2f",
            best_score,
            settings.WEB_FALLBACK_THRESHOLD,
        )
        return result

    # Phase 5: Take top K, deduplicate by content key
    usable = matches[:settings.TOP_K_CHUNKS]
    seen: set[str] = set()
    unique: list[RetrievedChunk] = []
    for m in usable:
        key = m.document + "_" + m.chunk[:80].strip().lower()
        if key not in seen:
            seen.add(key)
            unique.append(m)

    if not unique:
        unique = matches[:1]

    result.matches = unique
    result.context = "\n\n---\n\n".join(
        f"[DOCUMENT]\nFilename: {m.document}\nRelevance: {m.score:.2f}\n\nCONTENT:\n{m.chunk}".strip()
        for m in unique
    )

    logger.info("Retrieved %d chunks (confidence %.4f)", len(unique), best_score)
    return result


async def get_strict_context(query_text: str) -> tuple[str | None, list[dict]]:
    """Backward-compatible wrapper."""
    result = await retrieve_context(query_text)
    if not result.context:
        return None, []
    return result.context, result.sources


def get_chroma_stats(sample_size: int = 5) -> dict:
    collection = get_chroma_collection()
    chunks_count = collection.count()

    if chunks_count == 0:
        return {"documents_count": 0, "chunks_count": 0, "sample_chunks": []}

    data = collection.get(include=["documents", "metadatas"])
    metadatas = data.get("metadatas") or []
    documents = data.get("documents") or []

    filenames = {
        (meta or {}).get("filename")
        for meta in metadatas
        if meta and meta.get("filename")
    }

    sample_chunks = [
        {
            "document": (meta or {}).get("filename", "Unknown"),
            "chunk": text or "",
        }
        for text, meta in zip(documents[:sample_size], metadatas[:sample_size])
    ]

    return {
        "documents_count": len(filenames),
        "chunks_count": chunks_count,
        "sample_chunks": sample_chunks,
    }


async def debug_search(query: str, limit: int = 10) -> list[dict]:
    matches = await search_chunks_multi(query, limit=limit)
    return [
        {"score": m.score, "document": m.document, "chunk": m.chunk}
        for m in matches
    ]


def get_document_chunks(filename: str, limit: int = 20) -> list[dict]:
    collection = get_chroma_collection()
    data = collection.get(
        where={"filename": filename},
        include=["documents", "metadatas"],
        limit=limit,
    )
    documents = data.get("documents") or []
    metadatas = data.get("metadatas") or []
    return [
        {
            "document": (meta or {}).get("filename", filename),
            "chunk": doc or "",
        }
        for doc, meta in zip(documents, metadatas)
    ]
