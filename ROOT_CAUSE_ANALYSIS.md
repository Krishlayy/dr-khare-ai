# Root Cause Analysis — Chatbot Not Retrieving Knowledge

## Request Flow Audited

```
Frontend (App.jsx)
    ↓ POST /api/chat/stream { text }
Chat API (chat.py)
    ↓ get_strict_context()
Retriever (retrieval.py)
    ↓ ChromaDB query + threshold filter
Retrieved Chunks
    ↓ (empty if filtered)
Prompt Builder (chat.py inline)
    ↓ NO_CONTEXT_MESSAGE returned early
Ollama (never called)
    ↓
Frontend displays "I could not find information"
```

## Primary Root Cause: Overly Aggressive Similarity Threshold

| Setting | Value | Impact |
|---------|-------|--------|
| `SIMILARITY_THRESHOLD` | **0.75** | Discarded all chunks scoring below 75% |
| `TOP_K` | 4 | Too few chunks considered |

### Evidence (pre-fix diagnostic)

| Query | Top Score | Strict Context Returned |
|-------|-----------|------------------------|
| "What are Dr Khare office hours?" | 0.8509 | ✅ YES |
| "Who is Dr Khare?" | 0.5627 | ❌ NO (filtered) |
| "What education does Dr Khare have?" | 0.4891 | ❌ NO (filtered) |

**Conclusion:** ChromaDB contained valid data and `POST /api/debug/search` returned matches, but `get_strict_context()` filtered them out before the LLM ever saw them.

---

## Secondary Root Causes

### 1. Wrong Ollama Model Name
- Config: `OLLAMA_MODEL = "qwen2"`
- Installed: `qwen2.5:7b`, `llama3:latest`, `phi3:mini`
- **Impact:** Even when context was retrieved, Ollama returned 503/404

### 2. No Web Fallback
- Low-confidence or zero-match queries had no alternative retrieval path

### 3. No Conversation Memory
- Follow-up questions lacked prior context in the prompt

### 4. Frontend Gaps
- No `session_id` persisted → memory could not work across turns
- No streaming, citations detail, confidence, or response time display
- Generic error message masked 503 vs no-context failures

### 5. Insufficient Pipeline Logging
- Silent failures in retrieval (`print` only, no structured logs)

---

## Failure Classification

| Category | Status (Pre-Fix) | Fix Applied |
|----------|------------------|-------------|
| Retrieval failures | **CRITICAL** — threshold too high | Lowered to 0.40, top-5 always searched |
| LLM failures | **HIGH** — wrong model name | Auto-detect with priority list |
| Context injection failures | **CRITICAL** — empty context returned early | `retrieve_context()` always builds context when score ≥ threshold |
| Frontend display failures | **MEDIUM** — no metadata shown | Streaming UI + citations + confidence |
| Authentication issues | **LOW** — OAuth2 fixed previously | No change needed |
| ChromaDB issues | **NONE** — data present | Verified via `/api/debug/chroma` |

---

## Fixes Implemented

1. **`retrieve_context()`** — top-5 chunks, threshold 0.40, structured logging
2. **`chat_service.py`** — full pipeline with memory, web fallback, stage logging
3. **`ollama_service.py`** — auto model selection (`qwen2.5:7b` → `llama3` → `phi3`)
4. **`web_search.py`** — DuckDuckGo fallback when confidence < 0.40
5. **Debug endpoints** — `/api/debug/retrieve`, `/api/debug/ollama`
6. **Frontend** — SSE streaming, dark mode, citations, confidence badge, retry/copy
7. **Admin dashboard** — KB health, storage, query metrics
