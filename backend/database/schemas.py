from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=6)
    role_id: int


class UserResponse(UserBase):
    id: int
    role_id: int
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class RoleResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: int
    filename: str
    filepath: str
    filetype: str
    status: str
    processing_stage: str
    chunks_count: int
    upload_date: datetime | None = None
    error_message: str | None = None

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    status: str
    processing_stage: str
    message: str


class DocumentStatusResponse(BaseModel):
    document_id: int
    filename: str
    status: str
    processing_stage: str
    stage_label: str
    progress: int
    chunks_count: int
    error_message: str | None = None


class KnowledgeEntryCreate(BaseModel):
    title: str
    category: str = "general"
    content: str


class KnowledgeEntryResponse(KnowledgeEntryCreate):
    id: int
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    text: str
    session_id: str | None = None
    stream: bool = False
    mode: str = "doctor"  # "doctor" | "research"


class ChatResponse(BaseModel):
    response: str
    sources: list[dict[str, Any]] = []
    session_id: str | None = None
    answer_source: str = "Knowledge Base"
    confidence: float = 0.0
    response_time_ms: int = 0
    model: str | None = None
    bypassed_llm: bool | None = False


class ChatHistoryResponse(BaseModel):
    id: int
    session_id: str
    role: str
    message: str
    sources: list[dict[str, Any]] = []
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class AnalyticsResponse(BaseModel):
    total_documents: int
    total_users: int
    total_chat_messages: int
    system_status: str


class SampleChunk(BaseModel):
    document: str
    chunk: str


class DebugChromaResponse(BaseModel):
    collection_name: str
    documents_count: int
    chunks_count: int
    embedding_dimension: int
    sample_chunks: list[SampleChunk]


class DebugSearchRequest(BaseModel):
    query: str


class DebugSearchMatch(BaseModel):
    score: float
    document: str
    chunk: str


class DebugSearchResponse(BaseModel):
    matches: list[DebugSearchMatch]


class DebugRetrieveRequest(BaseModel):
    query: str


class DebugRetrieveResponse(BaseModel):
    query: str
    confidence: float
    use_web_fallback: bool
    context_preview: str
    matches: list[DebugSearchMatch]


class OllamaStatusResponse(BaseModel):
    reachable: bool
    selected_model: str | None
    models: list[str]
    priority: list[str]


class DashboardResponse(BaseModel):
    documents_indexed: int
    chunks_indexed: int
    storage_used_mb: float
    queries_today: int
    average_response_time_ms: float
    knowledge_base_health: str
    ollama_reachable: bool
    ollama_model: str | None
    chroma_documents: int
    chroma_chunks: int


class DocumentChunkResponse(BaseModel):
    document: str
    chunk: str
