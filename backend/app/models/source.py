import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Text, Float, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Source(Base):
    """A retrieved external/internal source used as evidence backing."""
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("research_sessions.id"))
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source_type: Mapped[str] = mapped_column(String(50), default="web")  # web|internal_doc|api
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    reliability_score: Mapped[float] = mapped_column(Float, default=0.5)

    session = relationship("ResearchSession", back_populates="sources")
    evidence_items = relationship("Evidence", back_populates="source", cascade="all, delete-orphan")
