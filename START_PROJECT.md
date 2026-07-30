# START PROJECT — Dr. Supreet Khare AI Assistant
_Complete startup guide — updated June 7, 2026_

---

## PREREQUISITES

| Tool | Required Version | Check |
|------|-----------------|-------|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| Ollama | Latest | `ollama --version` |
| Git | Any | `git --version` |

---

## ONE-TIME SETUP

### 1. Pull an Ollama Model (required)
```bash
ollama pull qwen2.5:7b
# OR (if you prefer lighter models)
ollama pull llama3:latest
ollama pull phi3:mini
```

### 2. Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies
```bash
cd frontend
npm install
```

### 4. Initialize Database + Admin User
```bash
# From project root
python init_db.py
```
This creates:
- SQLite database at `backend/app.db`
- Admin user: `admin@khare.ai` / `admin123`
- Roles: "Super Admin", "User"

---

## STARTING THE PROJECT

### Terminal 1 — Backend
```bash
# From project root
python -m uvicorn backend.main:app --reload

# Or with explicit host/port
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Backend runs at: http://127.0.0.1:8000
API docs at: http://127.0.0.1:8000/docs

### Terminal 2 — Frontend
```bash
cd frontend
npm run dev
```
Frontend runs at: http://localhost:5173

### Terminal 3 — Ollama (if not already running)
```bash
ollama serve
```

---

## DEFAULT CREDENTIALS

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@khare.ai | admin123 |

**Change these in production.**

---

## APPLICATION URLS

| Page | URL | Notes |
|------|-----|-------|
| Chat Interface | http://localhost:5173/ | Public — no login required |
| Admin Login | http://localhost:5173/login | Use admin credentials |
| Admin Panel | http://localhost:5173/admin | Redirects to /login if not authenticated |
| API Root | http://127.0.0.1:8000/ | Health check |
| API Docs (Swagger) | http://127.0.0.1:8000/docs | FastAPI auto-docs |

---

## UPLOADING DOCUMENTS

1. Go to http://localhost:5173/login
2. Login with `admin@khare.ai` / `admin123`
3. You land on the Admin Panel
4. Click **Browse Files** and select a PDF, DOCX, or TXT
5. Watch the pipeline progress: Upload → Extract → Chunk → Embed → Index
6. Once "Completed", the document is available for chat queries

---

## KNOWLEDGE BASE PIPELINE

```
Upload File
    ↓
Save to storage/uploads/
    ↓
Extract Text (PyMuPDF / python-docx / plain text)
    ↓
Clean Text (remove control chars, normalize whitespace)
    ↓
Chunk Text (800 chars / 120 char overlap)
    ↓
Generate Embeddings (sentence-transformers all-MiniLM-L6-v2, 384 dims)
    ↓
Store in ChromaDB (cosine similarity index)
    ↓
Update Document Status → "completed"
    ↓
Available for Semantic Retrieval
```

---

## RAG RESPONSE STRATEGY

| KB Confidence | Action |
|--------------|--------|
| ≥ 0.40 | Use Knowledge Base context |
| < 0.40 | Try DuckDuckGo web search fallback |
| Web search empty | Answer from general AI knowledge |

---

## PRODUCTION CHECKLIST

- [ ] Change `SECRET_KEY` in `backend/core/config.py` or set `SECRET_KEY` env var
- [ ] Change admin password via DB or re-run `init_db.py` with updated password
- [ ] Set `CORS_ORIGINS` to your production frontend URL
- [ ] Use PostgreSQL instead of SQLite for production
- [ ] Set up persistent ChromaDB storage path
- [ ] Enable HTTPS (nginx/caddy reverse proxy)
- [ ] Set resource limits on Ollama
- [ ] Configure log rotation

---

## ENVIRONMENT VARIABLES

Create `backend/.env` from `backend/.env.example`:

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your values
```

---

## TROUBLESHOOTING

### Backend won't start
```bash
# Check imports
python -c "import backend.main; print('OK')"
# Re-init DB
python init_db.py
```

### Chat returns errors
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags
# Check model is available
ollama list
```

### Upload fails
```bash
# Check storage directory exists
mkdir -p storage/uploads
```

### ChromaDB is empty
```bash
# Check chroma_db directory
python -c "from backend.rag.retrieval import get_chroma_stats; print(get_chroma_stats())"
```

### Frontend white screen
```bash
# Clear browser cache / storage
# Check browser console for errors
# Ensure backend is running on :8000
```
