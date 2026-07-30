from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.api.routes import admin, auth, chat, debug, docs, ingestion
from backend.core.config import settings
from backend.core.logging_config import setup_logging
from backend.core.rate_limit import limiter
from backend.database.database import Base, engine
from backend.database.migrations import migrate_documents_table
import backend.database.models  # noqa: F401 — register models with Base.metadata

setup_logging()


from backend.core.http_client import close_client, get_client
from backend.rag.retrieval import get_cross_encoder, get_bm25_index, get_chroma_collection
from backend.rag.embeddings import get_embedding_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    migrate_documents_table()
    get_client()  # initialize connection pool
    
    # Phase 2: Preload global models exactly once on startup
    get_embedding_model()
    get_cross_encoder()
    get_chroma_collection()
    get_bm25_index()
    yield
    await close_client()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(docs.router, prefix="/api/docs", tags=["Documents"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(ingestion.router, prefix="/api/upload", tags=["Ingestion"])
app.include_router(debug.router, prefix="/api/debug", tags=["Debug"])


@app.get("/")
def read_root():
    return {"status": "online", "system": settings.PROJECT_NAME}
