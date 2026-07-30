# PROJECT AUDIT — Dr. Khare AI Assistant
_Audited: June 7, 2026 | Engineer: Principal AI Architect_

---

## SYSTEM STATUS: MOSTLY FUNCTIONAL — BUGS IDENTIFIED

### Backend: ✅ Starts and Responds
### Frontend: ⚠️ Logic Bugs Present
### Auth: ✅ JWT + bcrypt working
### RAG Pipeline: ✅ ChromaDB + SentenceTransformer working
### Ollama: ✅ Integration working
### Streaming: ⚠️ Crashes on Ollama failure mid-stream

---

## CRITICAL BUGS

### BUG-001: App.jsx — Duplicate User Message
**File:** `frontend/src/App.jsx`, `sendMessage` function  
**Severity:** CRITICAL — causes every user message to appear twice  
**Root Cause:**  
The function both pushes `userMessage` into prev state AND conditionally includes it in the replacement spread. The logic is contradictory: it adds the user message, then in the same setState call it re-adds it unless `isRetry`. On first send, the user message is added TWICE.

```js
// WRONG — adds userMessage to prev, then also spreads it in
setMessages((prev) => [
  ...prev.slice(0, isRetry ? prev.length - 1 : prev.length),
  ...(isRetry ? [] : [userMessage]),  // userMessage added again
  { role: "assistant", content: "", streaming: true },
]);
```

**Also:** `assistantIdx` is computed but never used (dead code).

### BUG-002: App.jsx — Stale Closure in sendMessage
**File:** `frontend/src/App.jsx`  
**Severity:** HIGH — retry sends wrong content  
**Root Cause:** `messages.length` is in the `useCallback` dependency array. The callback is recreated on every message, which is fine, but the retry path (`isRetry=true`) slices `prev.length - 1` to remove the last assistant message and re-add it — but the slice logic in the first `setMessages` call runs on stale prev when the user message was added in the immediately prior call in the same tick.

### BUG-003: chat_service.py — stream_chat Crashes on Ollama Failure
**File:** `backend/services/chat_service.py`, `stream_chat`  
**Severity:** HIGH — unhandled RuntimeError breaks SSE stream  
**Root Cause:** `stream_response()` raises `RuntimeError` when Ollama is down. This exception propagates out of the async generator with no `try/except`, leaving the client hanging with a broken stream.

### BUG-004: chat_service.py — stream_chat Crashes on Ollama Stream Error  
**File:** `backend/services/chat_service.py`, `stream_chat`  
**Severity:** HIGH — mid-stream Ollama failures crash the generator  
**Root Cause:** The `async for token in stream_response(...)` loop has no error handling. If Ollama drops the connection mid-stream, the exception propagates unhandled.

### BUG-005: models.py — Document.uploaded_by Relationship Missing
**File:** `backend/database/models.py`  
**Severity:** MEDIUM — admin route accessing uploaded_by will fail  
**Root Cause:** `User` model has `documents = relationship("Document", back_populates="uploaded_by")` but `Document` model has no `uploaded_by` relationship attribute — only `uploaded_by_id` FK column. SQLAlchemy will raise `InvalidRequestError` on any admin operation that navigates this relationship.

### BUG-006: index.html — Wrong Page Title
**File:** `frontend/index.html`  
**Severity:** LOW — UX/branding issue  
**Root Cause:** Title is "frontend" not "Dr. Supreet Khare AI Assistant".

### BUG-007: Login.jsx — No Loading State, Bare Styling
**File:** `frontend/src/Login.jsx`  
**Severity:** MEDIUM — poor UX, no feedback during login  
**Root Cause:** No loading state during API call; inline styles instead of proper CSS class.

### BUG-008: vite.config.js — No API Proxy
**File:** `frontend/vite.config.js`  
**Severity:** LOW — hardcoded localhost URLs work but are not portable  
**Root Cause:** All API calls hardcode `http://127.0.0.1:8000`. A proxy would allow relative `/api/...` paths and simplify deployment.

### BUG-009: App.jsx — Typing Indicator Only Shows When content=""
**File:** `frontend/src/App.jsx`  
**Severity:** MEDIUM — typing indicator disappears immediately on first token  
**Root Cause:** `isLoading && messages[messages.length - 1]?.content === ""` — once the first streaming token arrives, content is non-empty and the indicator hides. But the streaming cursor (`▋`) is already visible, so this is a minor cosmetic issue. The bigger issue is the indicator never shows for non-empty streaming responses.

### BUG-010: Admin.jsx — getStageIndex Broken Mapping
**File:** `frontend/src/Admin.jsx`  
**Severity:** LOW — stage pills don't highlight correctly during upload  
**Root Cause:** `currentStage` holds the label string (e.g. "Extracting text..."), but `getStageIndex` tries to match it as a key. The `PIPELINE_STAGES.find((s) => s.label === currentStage)?.key` lookup works for poll-driven labels but breaks for "Uploading..." because the condition `currentStage === "Uploading..."` maps to `"uploading"` key — this actually works, but when `currentStage` comes from `stage_label` (e.g. "Extracting text..."), `getStageIndex` receives the label not the key.

---

## MINOR ISSUES

| ID | File | Issue |
|----|------|-------|
| M-001 | `backend/ingestion.py` | Legacy standalone script not connected to pipeline |
| M-002 | `backend/core/config.py` | `SECRET_KEY` is hardcoded default — must use env var in production |
| M-003 | `backend/services/web_search.py` | DuckDuckGo instant answer API returns empty for most queries — fallback needed |
| M-004 | `frontend/src/index.css` | Overrides `#root` width to 1126px which conflicts with App.css |
| M-005 | `backend/requirements.txt` | No pinned exact versions — could break on fresh install |
| M-006 | `frontend/package.json` | `lucide-react@^1.17.0` is version `1.17.0` — icon name changes may break |

---

## WHAT IS WORKING

- ✅ Backend starts with zero errors
- ✅ JWT authentication (login, token creation, protected routes)
- ✅ Document upload and background pipeline (PDF/DOCX/TXT)
- ✅ ChromaDB storage and cosine similarity retrieval
- ✅ SentenceTransformer embeddings (all-MiniLM-L6-v2)
- ✅ Ollama model auto-detection and selection
- ✅ Streaming SSE chat endpoint
- ✅ Conversation memory (last 6 messages)
- ✅ Web search fallback (DuckDuckGo)
- ✅ Rate limiting (SlowAPI)
- ✅ Admin dashboard with stats
- ✅ Upload history and status polling
- ✅ Document deletion with vector cleanup
- ✅ Re-index endpoint
- ✅ CORS configured for frontend dev ports
- ✅ Database migrations on startup
- ✅ Source citations in responses
- ✅ Dark mode in chat UI
- ✅ Responsive layout
