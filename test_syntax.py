import sys
from pathlib import Path
sys.path.append(str(Path("c:/Users/hello/dr_khare_ai").resolve()))

import asyncio
from backend.main import app
from backend.rag.embeddings import encode_text_async
from backend.api.routes.chat import chat_endpoint
from backend.api.routes.ingestion import upload_document

print("Phase 1 syntax checks passed!")
