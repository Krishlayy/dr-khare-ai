# FIX PLAN — Dr. Khare AI Assistant
_Plan Date: June 7, 2026_

## Priority Order

### P0 — Critical (breaks core functionality)
1. Fix `models.py` — add `uploaded_by` relationship to `Document`
2. Fix `App.jsx` — duplicate message bug in `sendMessage`
3. Fix `chat_service.py` — error handling in `stream_chat` for Ollama failures

### P1 — High (broken UX / runtime errors)
4. Fix `App.jsx` — retry logic and stale closure
5. Fix `App.jsx` — typing indicator visibility
6. Improve `Login.jsx` — loading state + production-grade UI

### P2 — Medium (quality / polish)
7. Fix `index.html` — correct page title
8. Fix `vite.config.js` — add API proxy
9. Fix `Admin.jsx` — stage index mapping
10. Fix `index.css` — remove conflicting `#root` width override

### P3 — Production Hardening
11. Add `.env.example` with all required env vars
12. Improve `web_search.py` — better DuckDuckGo parsing
13. Add `START_PROJECT.md` with complete run instructions
14. Update `PROJECT_STATUS.md`

## Files Modified
- `backend/database/models.py`
- `backend/services/chat_service.py`
- `frontend/src/App.jsx`
- `frontend/src/Login.jsx`
- `frontend/src/index.css`
- `frontend/index.html`
- `frontend/vite.config.js`
- `frontend/src/Admin.jsx`
- `backend/services/web_search.py`
- `PROJECT_STATUS.md`
- `START_PROJECT.md`
