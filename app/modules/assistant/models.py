import uuid
from typing import Optional, List

from sqlalchemy import String, Text, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.common.models import BaseModel

class AssistantDocument(BaseModel):
    """جدول المستندات واللوائح المصدرية للنقل الجامعي"""
    __tablename__ = "assistant_documents"

    title: Mapped[str] = mapped_column(
        String(255), 
        nullable=False, 
        comment="عنوان الوثيقة أو اللائحة"
    )
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500), 
        nullable=True, 
        comment="مسار الملف الأصلي أو رابط التخزين"
    )
    doc_type: Mapped[str] = mapped_column(
        String(50), 
        default="regulation", 
        nullable=False, 
        comment="نوع المستند: لائحة، جدول مواعيد، سياسة اشتراكات"
    )

    # العلاقة مع مقاطع المستند
    chunks: Mapped[List["AssistantDocumentChunk"]] = relationship(
        "AssistantDocumentChunk", 
        back_populates="document", 
        cascade="all, delete-orphan"
    )

class AssistantDocumentChunk(BaseModel):
    """جدول مقاطع المستندات ومتجهات التضمين للبحث الدلالي (RAG)"""
    __tablename__ = "assistant_document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assistant_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="معرف المستند الأصلي"
    )
    chunk_text: Mapped[str] = mapped_column(
        Text, 
        nullable=False, 
        comment="نص المقطع المستخرج"
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        comment="ترتيب المقطع داخل المستند"
    )
    embedding = mapped_column(
        Vector(1024), 
        nullable=True, 
        comment="متجه التضمين الدلالي بأبعاد 1024"
    )

    # العلاقة العكسية مع المستند
    document: Mapped["AssistantDocument"] = relationship(
        "AssistantDocument", 
        back_populates="chunks"
    )

    # فهرس HNSW لتسريع استعلامات التشابه الدلالي عبر pgvector
    __table_args__ = (
        Index(
            "ix_assistant_chunks_embedding_hnsw",
            embedding,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"}
        ),
    )

class ChatSession(BaseModel):
    """جلسات المحادثة للمستخدمين مع المساعد الذكي"""
    __tablename__ = "chat_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        nullable=False, 
        index=True, 
        comment="معرف المستخدم صاحب الجلسة"
    )
    title: Mapped[str] = mapped_column(
        String(255), 
        default="محادثة جديدة", 
        nullable=False, 
        comment="عنوان الجلسة التلقائي"
    )

    # العلاقة مع رسائل المحادثة
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )

class ChatMessage(BaseModel):
    """رسائل المحادثة الفردية وسياق الاسترجاع"""
    __tablename__ = "chat_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="معرف جلسة المحادثة"
    )
    role: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        comment="صاحب الرسالة: user أو assistant أو system"
    )
    content: Mapped[str] = mapped_column(
        Text, 
        nullable=False, 
        comment="نص الرسالة"
    )
    sources: Mapped[Optional[dict]] = mapped_column(
        JSONB, 
        nullable=True, 
        comment="المصادر المسترجعة والمقاطع الداعمة للإجابة"
    )

    # العلاقة العكسية مع الجلسة
    session: Mapped["ChatSession"] = relationship(
        "ChatSession", 
        back_populates="messages"
    )