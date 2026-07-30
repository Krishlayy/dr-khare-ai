import time
from typing import AsyncIterator

from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.logging_config import get_logger
from backend.database.models import ChatHistory, Analytics
from backend.rag.retrieval import RetrievalResult, retrieve_context, search_chunks_multi
from backend.services.intent_service import detect_intent
from backend.services.llm_service import generate_response, get_selected_model, stream_response
from backend.services.web_search import search_web

logger = get_logger("services.chat")

# ---------------------------------------------------------------------------
# Mode constants
# ---------------------------------------------------------------------------

MODE_DOCTOR = "doctor"      # KB-only: Master CV + uploaded docs. No web. No hallucination.
MODE_RESEARCH = "research"  # Web + Ollama general AI. Anything goes.



# ---------------------------------------------------------------------------
# Special identity queries — force KB retrieval, bypass score threshold
# ---------------------------------------------------------------------------

SPECIAL_QUERIES: list[str] = [
    "who is dr khare",
    "who is dr. khare",
    "who is supreet khare",
    "who is dr supreet khare",
    "who is dr supreet",
    "tell me about dr khare",
    "tell me about dr. khare",
    "tell me about supreet khare",
    "summarize dr khare",
    "summarise dr khare",
    "summary of dr khare",
    "dr khare profile",
    "dr khare biography",
    "dr khare bio",
    "dr. khare profile",
    "dr. khare biography",
    "dr khare background",
    "dr. khare background",
    "about dr khare",
    "about dr. khare",
    "dr khare introduction",
    "introduce dr khare",
    "what is dr khare",
    "what is dr. khare",
    "what does dr khare do",
    "what does dr. khare do",
    "dr khare education",
    "dr. khare education",
    "dr khare qualifications",
    "dr khare experience",
    "dr khare specialty",
    "dr khare speciality",
    "dr khare credentials",
    "dr khare career",
    "dr khare achievements",
    "dr khare awards",
    "dr khare training",
    "dr khare residency",
    "dr khare medical school",
]


def _is_special_query(normalized: str) -> bool:
    """Exact or starts-with match only. No substring-of-pattern matching."""
    for pattern in SPECIAL_QUERIES:
        if normalized == pattern:
            return True
        if (normalized.startswith(pattern + " ") or
                normalized.startswith(pattern + "?") or
                normalized.startswith(pattern + "!") or
                normalized.startswith(pattern + ".")):
            return True
    return False


# ---------------------------------------------------------------------------
# Off-topic redirect (Doctor mode only)
# ---------------------------------------------------------------------------

OFF_TOPIC_REPLY = (
    "I specialize in information related to Dr. Supreet Khare and the documents "
    "available to me. I'm not able to help with that topic here.\n\n"
    "Switch to **Research Mode** if you'd like general web-based information."
)


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

_DOCTOR_PERSONA = """\
You are the official AI assistant for Dr. Supreet Khare.

YOUR KNOWLEDGE SOURCE
- You answer EXCLUSIVELY from the provided retrieved documents.
- Read all retrieved documents carefully, merge information across chunks, and eliminate contradictions.
- Extract every factual detail (names, dates, locations, credentials).
- Do NOT use web search.
- Do NOT use general AI knowledge.
- If the answer is not in the documents, state so clearly and politely.

PRIVACY RULE
- Do NOT expose personal phone numbers, mailing addresses, or AAMC IDs unless the user explicitly requests them in their query.

STRUCTURED FORMATTING REQUIREMENTS
- For Biography / Profile queries: You MUST include his Credentials (e.g. MBBS, MD), Residency location, and Current Role (e.g. Managing Director).
- For Education queries: You MUST explicitly state his Medical School and Residency details.
- For Clinic / Practice queries: You MUST include the exact clinic name, location, and timings if available in context.
- For Awards / Memberships / Publications queries: ALWAYS use bullet points to list them.
- Ensure all facts from multiple documents are aggregated. Do not skip details.

TONE
- Warm, professional, and concise.
- Answer directly.
- NEVER mention "chunks", "RAG", "vector databases", "confidence scores", or how you retrieved the information.
- Speak seamlessly as an intelligent executive assistant.
"""

_RESEARCH_PERSONA = """\
You are an intelligent research assistant with access to web search results and general knowledge.

TONE
- Helpful, accurate, and concise.
- Cite sources when available.
- Be honest when information is uncertain.
- Never mention embeddings, vector databases, chunks, or retrieval systems.
"""


def build_doctor_kb_prompt(question: str, context: str, memory: list[dict]) -> str:
    memory_block = _format_memory(memory)
    return f"""{_DOCTOR_PERSONA}

CONVERSATION HISTORY
{memory_block or "(none)"}

RETRIEVED DOCUMENTS
{context}

USER QUESTION
{question}

Answer from the documents above. Start with the direct answer. Be complete but concise.
"""


def build_doctor_identity_prompt(question: str, context: str, memory: list[dict]) -> str:
    memory_block = _format_memory(memory)
    return f"""{_DOCTOR_PERSONA}

TASK
The user is asking about Dr. Supreet Khare's identity, background, or qualifications.
Provide a warm, professional response. Highlight his most impressive credentials.
Answer EXCLUSIVELY from the documents below.

CONVERSATION HISTORY
{memory_block or "(none)"}

DR. KHARE'S DOCUMENTS
{context}

USER QUESTION
{question}

Give a complete, accurate introduction based only on the documents.
"""


def build_doctor_not_found_prompt(question: str, memory: list[dict]) -> str:
    memory_block = _format_memory(memory)
    return f"""{_DOCTOR_PERSONA}

CONVERSATION HISTORY
{memory_block or "(none)"}

SITUATION
The user asked a question but no relevant information was found in Dr. Khare's documents.

USER QUESTION
{question}

Respond politely that this topic isn't covered in the available documents.
Do NOT attempt to answer from general knowledge.
Suggest they try a more specific question about Dr. Khare, or switch to Research Mode.
Keep it brief — two sentences maximum.
"""


def build_research_web_prompt(question: str, context: str, memory: list[dict]) -> str:
    memory_block = _format_memory(memory)
    return f"""{_RESEARCH_PERSONA}

CONVERSATION HISTORY
{memory_block or "(none)"}

WEB SEARCH RESULTS
{context}

USER QUESTION
{question}

Summarise the web findings clearly. Mention where the information comes from.
"""


def build_research_general_prompt(question: str, memory: list[dict]) -> str:
    memory_block = _format_memory(memory)
    return f"""{_RESEARCH_PERSONA}

CONVERSATION HISTORY
{memory_block or "(none)"}

USER QUESTION
{question}

Answer from your general knowledge. Be accurate and concise.
"""


def _format_memory(memory: list[dict]) -> str:
    return "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in memory[-10:]
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_conversation_memory(db: Session, session_id: str) -> list[dict]:
    rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at.desc())
        .limit(settings.MEMORY_WINDOW)
        .all()
    )
    rows.reverse()
    return [{"role": r.role, "content": r.message} for r in rows]


def _instant_reply(text: str, session_id: str) -> dict:
    return {
        "response": text,
        "sources": [],
        "session_id": session_id,
        "answer_source": "Assistant",
        "confidence": 1.0,
        "response_time_ms": 0,
        "model": None,
    }


async def _force_kb_retrieval(question: str, top_k: int = 6) -> tuple[str, list[dict], float]:
    """Force KB retrieval regardless of confidence threshold. Used for identity queries.
    Directly extracts biography and employment to guarantee they are never drowned out."""
    from backend.rag.retrieval import get_chroma_collection
    collection = get_chroma_collection()
    
    res_bio = collection.get(where={"filename": "biography.txt"})
    res_emp = collection.get(where={"filename": "employment.txt"})
    
    unique = []
    for i, doc in enumerate(res_bio.get("documents", [])):
        if i < 3 and doc.strip():
            unique.append({"document": "biography.txt", "chunk": doc.strip(), "score": 2.0})
            
    for i, doc in enumerate(res_emp.get("documents", [])):
        if i < 3 and doc.strip():
            unique.append({"document": "employment.txt", "chunk": doc.strip(), "score": 1.5})
            
    if not unique:
        return "", [], 0.0

    context = "\n\n---\n\n".join(
        f"[DOCUMENT]\nFilename: {m['document']}\nRelevance: {m['score']:.2f}\n\nCONTENT:\n{m['chunk']}"
        for m in unique
    )
    sources = [
        {
            "filename": m['document'],
            "document": m['document'],
            "score": round(m['score'], 4),
            "chunk_preview": m['chunk'][:200],
        }
        for m in unique
    ]
    confidence = unique[0]['score'] if unique else 0.0
    logger.info("force_kb_retrieval: %d chunks, top_score=%.4f", len(unique), confidence)
    return context, sources, confidence


# ---------------------------------------------------------------------------
# Doctor mode pipeline
# ---------------------------------------------------------------------------

def _build_doctor_prompt(
    question: str,
    context: str,
    memory: list[dict],
    is_identity: bool,
    has_context: bool,
) -> str:
    if not has_context:
        return build_doctor_not_found_prompt(question, memory)
    if is_identity:
        return build_doctor_identity_prompt(question, context, memory)
    return build_doctor_kb_prompt(question, context, memory)


async def _run_doctor_mode(
    question: str,
    session_id: str,
    memory: list[dict],
) -> tuple[str, str, list[dict], float]:
    """
    Doctor mode: KB only.
    Returns (context, answer_source, sources, confidence).
    Never touches web search or general AI.
    """
    normalized = question.strip().lower()
    is_identity = _is_special_query(normalized)

    if is_identity:
        context, sources, confidence = await _force_kb_retrieval(question, top_k=6)
        answer_source = "Knowledge Base" if context else "Knowledge Base"
        logger.info("Doctor/identity: confidence=%.4f chunks=%d", confidence, len(sources))
        return context, answer_source, sources, confidence

    # Standard retrieval (multi-query, with threshold)
    retrieval = await retrieve_context(question)
    logger.info(
        "Doctor/standard: confidence=%.4f web_fallback=%s matches=%d",
        retrieval.confidence,
        retrieval.use_web_fallback,
        len(retrieval.matches),
    )

    if retrieval.context and not retrieval.use_web_fallback:
        return retrieval.context, "Knowledge Base", retrieval.sources, retrieval.confidence

    # No KB match — doctor mode does NOT fall back to web or general AI
    return "", "Knowledge Base", [], retrieval.confidence


# ---------------------------------------------------------------------------
# Research mode pipeline
# ---------------------------------------------------------------------------

async def _run_research_mode(
    question: str,
) -> tuple[str, str, list[dict], float]:
    """
    Research mode: web search first, then general AI.
    Returns (context, answer_source, sources, confidence).
    """
    retrieval = await retrieve_context(question)

    # If KB has a good hit, use it even in research mode
    if retrieval.context and not retrieval.use_web_fallback:
        logger.info("Research/KB hit: confidence=%.4f", retrieval.confidence)
        return retrieval.context, "Knowledge Base", retrieval.sources, retrieval.confidence

    # Try web search
    logger.info("Research/web fallback for: %s", question[:80])
    web_context, web_sources = await search_web(question)
    if web_context:
        formatted = [
            {
                "filename": s.get("title", "Web"),
                "document": s.get("title", "Web"),
                "score": 0.0,
                "url": s.get("url", ""),
                "chunk_preview": s.get("snippet", "")[:200],
            }
            for s in web_sources
        ]
        return web_context, "Web Search", formatted, retrieval.confidence

    # General AI fallback
    return "", "General AI", [], retrieval.confidence


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


# verify_grounding (secondary LLM call) removed in Optimization Cycle 7.
# Hallucination protection is now achieved purely through the
# confidence-threshold hard guard (SIMILARITY_THRESHOLD) combined with
# the soft-boosted retrieval ranking. This halves response latency.

def log_intent(db: Session, intent_type: str, session_id: str):
    try:
        analytics = Analytics(
            event_type="intent_matched",
            event_data={"intent": intent_type, "session_id": session_id}
        )
        db.add(analytics)
        db.commit()
    except Exception as e:
        logger.error("Failed to log intent: %s", e)


async def process_chat(
    db: Session,
    question: str,
    session_id: str,
    user_id: int | None = None,
    mode: str = MODE_DOCTOR,
) -> dict:
    start = time.perf_counter()
    
    # ── Fast-path: Intent Recognition (Greetings & Small Talk) ───────────────
    intent, intent_response = detect_intent(question)
    if intent:
        logger.info("Intent matched (%s) — instant", intent)
        log_intent(db, intent, session_id)
        return _instant_reply(intent_response, session_id)

    log_intent(db, "Knowledge Question", session_id)
    normalized = question.strip().lower()

    logger.info("=== CHAT [mode=%s] session=%s ===", mode, session_id)
    
    from backend.services.cache_service import get_cached_answer, set_cached_answer
    
    cached = await get_cached_answer(question)
    if cached:
        cached["session_id"] = session_id
        cached["response_time_ms"] = int((time.perf_counter() - start) * 1000)
        return cached

    memory = load_conversation_memory(db, session_id)

    if mode == MODE_RESEARCH:
        context, answer_source, sources, confidence = await _run_research_mode(question)
        if answer_source == "Knowledge Base":
            prompt = build_doctor_kb_prompt(question, context, memory)
        elif answer_source == "Web Search":
            prompt = build_research_web_prompt(question, context, memory)
        else:
            prompt = build_research_general_prompt(question, memory)
    else:
        # Doctor mode (default)
        context, answer_source, sources, confidence = await _run_doctor_mode(
            question, session_id, memory
        )
        is_identity = _is_special_query(normalized)
        has_context = bool(context)
        
        # ── Fast-path: LLM Bypass & Hard Grounding (Doctor Mode only) ────────────────
        if not has_context or confidence < settings.SIMILARITY_THRESHOLD:
            logger.info("HARD GROUNDING TRIGGERED! Confidence: %.4f", confidence)
            elapsed = int((time.perf_counter() - start) * 1000)
            return {
                "response": "I could not find verified information about this topic in Dr. Khare's available documents. You may discuss it with him during your next meeting.",
                "sources": sources,
                "session_id": session_id,
                "answer_source": "System (Hard Grounding)",
                "confidence": confidence,
                "response_time_ms": elapsed,
                "model": "bypass",
                "bypassed_llm": True
            }
            
        if settings.ENABLE_LLM_BYPASS and confidence >= settings.BYPASS_CONFIDENCE_THRESHOLD and has_context:
            logger.info("LLM BYPASSED! Confidence: %.4f", confidence)
            # Extract ALL chunks from context
            chunks_text = []
            for block in context.split("[DOCUMENT]"):
                if "CONTENT:\n" in block:
                    chunk = block.split("CONTENT:\n")[-1].strip()
                    if chunk:
                        chunks_text.append(f"• {chunk}")
            
            combined_chunks = "\n\n".join(chunks_text) if chunks_text else "No data."
            reply = f"According to Dr. Khare's verified documents:\n\n{combined_chunks}"
            elapsed = int((time.perf_counter() - start) * 1000)
            return {
                "response": reply,
                "sources": sources,
                "session_id": session_id,
                "answer_source": answer_source,
                "confidence": confidence,
                "response_time_ms": elapsed,
                "model": "bypass",
                "bypassed_llm": True
            }
            
        prompt = _build_doctor_prompt(question, context, memory, is_identity, has_context)
        if confidence < settings.SIMILARITY_THRESHOLD_CAUTIOUS:
            prompt += "\n\nCRITICAL INSTRUCTION: Your retrieval confidence is MEDIUM. Answer cautiously. Explicitly state that limited information was found. Do not infer missing details."

    model = await get_selected_model()
    answer = await generate_response(prompt, model=model)
    # Secondary LLM grounding verification removed (Cycle 7).
    # The confidence-threshold guard above (SIMILARITY_THRESHOLD) ensures
    # we never call the LLM when retrieval is insufficient.

    elapsed = int((time.perf_counter() - start) * 1000)

    logger.info("=== DONE mode=%s source=%s model=%s time=%dms ===",
                mode, answer_source, model, elapsed)

    result = {
        "response": answer or OFF_TOPIC_REPLY,
        "sources": sources,
        "session_id": session_id,
        "answer_source": answer_source,
        "confidence": confidence,
        "response_time_ms": elapsed,
        "model": model,
        "bypassed_llm": False
    }
    
    await set_cached_answer(question, result)
    return result


async def stream_chat(
    db: Session,
    question: str,
    session_id: str,
    user_id: int | None = None,
    mode: str = MODE_DOCTOR,
) -> AsyncIterator[dict]:
    start = time.perf_counter()
    
    # ── Fast-path: Intent Recognition (Greetings & Small Talk) ───────────────
    intent, intent_response = detect_intent(question)
    if intent:
        logger.info("Intent matched (%s) — instant stream", intent)
        log_intent(db, intent, session_id)
        yield {"type": "meta", "sources": [], "session_id": session_id,
               "answer_source": "Assistant", "confidence": 1.0}
        yield {"type": "token", "content": intent_response}
        yield {"type": "done", "response_time_ms": 0, "model": None, "full_response": intent_response}
        return

    log_intent(db, "Knowledge Question", session_id)
    normalized = question.strip().lower()

    logger.info("=== STREAM [mode=%s] session=%s ===", mode, session_id)
    
    from backend.services.cache_service import get_cached_answer, set_cached_answer
    
    cached = await get_cached_answer(question)
    if cached:
        logger.info("Cache hit for stream")
        yield {"type": "meta", "sources": cached["sources"], "session_id": session_id,
               "answer_source": cached["answer_source"], "confidence": cached["confidence"]}
        yield {"type": "token", "content": cached["response"]}
        yield {"type": "done", "response_time_ms": int((time.perf_counter() - start) * 1000), "model": "cache", "full_response": cached["response"]}
        return

    memory = load_conversation_memory(db, session_id)

    if mode == MODE_RESEARCH:
        context, answer_source, sources, confidence = await _run_research_mode(question)
        if answer_source == "Knowledge Base":
            prompt = build_doctor_kb_prompt(question, context, memory)
        elif answer_source == "Web Search":
            prompt = build_research_web_prompt(question, context, memory)
        else:
            prompt = build_research_general_prompt(question, memory)
    else:
        context, answer_source, sources, confidence = await _run_doctor_mode(
            question, session_id, memory
        )
        is_identity = _is_special_query(normalized)
        has_context = bool(context)
        
        # ── Fast-path: LLM Bypass & Hard Grounding (Doctor Mode only) ────────────────
        if not has_context or confidence < settings.SIMILARITY_THRESHOLD:
            logger.info("HARD GROUNDING TRIGGERED (Stream)! Confidence: %.4f", confidence)
            reply = "I could not find verified information about this topic in Dr. Khare's available documents. You may discuss it with him during your next meeting."
            yield {"type": "meta", "sources": sources, "session_id": session_id, "answer_source": "System (Hard Grounding)", "confidence": confidence}
            yield {"type": "token", "content": reply}
            yield {"type": "done", "response_time_ms": int((time.perf_counter() - start) * 1000), "model": "bypass", "full_response": reply}
            return
            
        if settings.ENABLE_LLM_BYPASS and confidence >= settings.BYPASS_CONFIDENCE_THRESHOLD and has_context:
            logger.info("LLM BYPASSED (Stream)! Confidence: %.4f", confidence)
            chunks_text = []
            for block in context.split("[DOCUMENT]"):
                if "CONTENT:\n" in block:
                    chunk = block.split("CONTENT:\n")[-1].strip()
                    if chunk:
                        chunks_text.append(f"• {chunk}")
            
            combined_chunks = "\n\n".join(chunks_text) if chunks_text else "No data."
            reply = f"According to Dr. Khare's verified documents:\n\n{combined_chunks}"
            
            yield {
                "type": "meta",
                "sources": sources,
                "session_id": session_id,
                "answer_source": answer_source,
                "confidence": confidence,
                "bypassed_llm": True,
                "model": "bypass"
            }
            yield {"type": "token", "content": reply}
            yield {
                "type": "done",
                "response_time_ms": int((time.perf_counter() - start) * 1000),
                "model": "bypass",
                "full_response": reply,
            }
            return
            
        prompt = _build_doctor_prompt(question, context, memory, is_identity, has_context)
        if confidence < settings.SIMILARITY_THRESHOLD_CAUTIOUS:
            prompt += "\n\nCRITICAL INSTRUCTION: Your retrieval confidence is MEDIUM. Answer cautiously. Explicitly state that limited information was found. Do not infer missing details."

    yield {
        "type": "meta",
        "sources": sources,
        "session_id": session_id,
        "answer_source": answer_source,
        "confidence": confidence,
        "bypassed_llm": False
    }

    model = await get_selected_model()
    full_response: list[str] = []

    if not model:
        msg = "The AI engine is currently offline. Please try again in a moment."
        yield {"type": "token", "content": msg}
        yield {"type": "done", "response_time_ms": int((time.perf_counter() - start) * 1000),
               "model": None, "full_response": msg}
        return

    try:
        async for token in stream_response(prompt, model=model):
            full_response.append(token)
            yield {"type": "token", "content": token}
    except RuntimeError as exc:
        logger.error("Ollama stream error: %s", exc)
        if not full_response:
            msg = "I'm having trouble reaching the AI engine. Please try again."
            yield {"type": "token", "content": msg}
            full_response.append(msg)
    except Exception as exc:
        logger.error("Unexpected stream error: %s", exc)
        if not full_response:
            msg = "An unexpected error occurred. Please try again."
            yield {"type": "token", "content": msg}
            full_response.append(msg)

    full_answer = "".join(full_response)
    
    result = {
        "response": full_answer,
        "sources": sources,
        "session_id": session_id,
        "answer_source": answer_source,
        "confidence": confidence,
        "response_time_ms": int((time.perf_counter() - start) * 1000),
        "model": model,
        "bypassed_llm": False
    }
    
    # Only cache successful generations that don't have standard errors
    if not full_answer.startswith("I'm having trouble") and not full_answer.startswith("An unexpected error"):
        await set_cached_answer(question, result)

    yield {
        "type": "done",
        "response_time_ms": result["response_time_ms"],
        "model": model,
        "full_response": full_answer,
    }
