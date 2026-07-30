from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from backend.database.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    permissions = Column(JSON, default=dict)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    role = relationship("Role", back_populates="users")
    documents = relationship("Document", back_populates="uploaded_by")
    chat_messages = relationship("ChatHistory", back_populates="user")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(512), nullable=False)
    filepath = Column(String(1024), nullable=False)
    filetype = Column(String(32), nullable=False, default="unknown")
    status = Column(String(32), default="pending")
    processing_stage = Column(String(64), default="uploading")
    chunks_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())

    uploaded_by = relationship("User", back_populates="documents", foreign_keys=[uploaded_by_id])


class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), default="general")
    content = Column(Text, nullable=False)
    source_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(64), index=True, nullable=False)
    role = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    sources = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="chat_messages")


class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True)
    event_type = Column(String(100))
    event_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
