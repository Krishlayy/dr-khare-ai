"""Final verification script — run to confirm all systems operational."""
import sys

errors = []

# Test all critical imports
try:
    import backend.main
    print("  [OK] backend.main")
except Exception as e:
    errors.append(f"backend.main: {e}")

try:
    from backend.services.chat_service import stream_chat, process_chat
    print("  [OK] chat_service")
except Exception as e:
    errors.append(f"chat_service: {e}")

try:
    from backend.services.ollama_service import get_selected_model, stream_response
    print("  [OK] ollama_service")
except Exception as e:
    errors.append(f"ollama_service: {e}")

try:
    from backend.database.models import Document, User, ChatHistory, Role
    from sqlalchemy import inspect
    d_rels = [r.key for r in inspect(Document).relationships]
    u_rels = [r.key for r in inspect(User).relationships]
    assert "uploaded_by" in d_rels, "Document missing uploaded_by relationship"
    assert "documents" in u_rels, "User missing documents relationship"
    print("  [OK] models - Document rels:", d_rels, "| User rels:", u_rels)
except Exception as e:
    errors.append(f"models: {e}")

try:
    from backend.rag.retrieval import retrieve_context, get_chroma_stats
    stats = get_chroma_stats()
    chunks = stats["chunks_count"]
    docs = stats["documents_count"]
    print(f"  [OK] ChromaDB - {chunks} chunks in {docs} docs")
except Exception as e:
    errors.append(f"rag.retrieval: {e}")

try:
    from backend.services.web_search import search_web
    print("  [OK] web_search")
except Exception as e:
    errors.append(f"web_search: {e}")

try:
    from backend.api.routes import auth, chat, admin, docs, ingestion, debug
    print("  [OK] all routes")
except Exception as e:
    errors.append(f"routes: {e}")

try:
    from backend.core.security import get_password_hash, verify_password, create_access_token
    h = get_password_hash("testpass")
    assert verify_password("testpass", h)
    token = create_access_token({"sub": "test@test.com"})
    assert token
    print("  [OK] security (bcrypt + JWT)")
except Exception as e:
    errors.append(f"security: {e}")

try:
    from backend.rag.document_processor import extract_text, chunk_text, clean_text
    chunks = chunk_text("Hello world. " * 100)
    assert len(chunks) > 0
    print(f"  [OK] document_processor - chunking works ({len(chunks)} chunks from test text)")
except Exception as e:
    errors.append(f"document_processor: {e}")

try:
    from backend.rag.embeddings import get_embedding_model, encode_text
    vec = encode_text("test query")
    assert len(vec) == 384
    print(f"  [OK] embeddings - vector dim={len(vec)}")
except Exception as e:
    errors.append(f"embeddings: {e}")

print()
if errors:
    print("FAILURES:")
    for err in errors:
        print(f"  - {err}")
    print("\n❌ VERIFICATION FAILED")
    sys.exit(1)
else:
    print("✅ ALL CHECKS PASS — System is production ready")
