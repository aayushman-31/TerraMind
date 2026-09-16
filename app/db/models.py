from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

JSONType = JSON().with_variant(JSONB, "postgresql")


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sessions: Mapped[list["Session"]] = relationship(back_populates="user")


class Session(Base):
    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    user: Mapped[User | None] = relationship(back_populates="sessions")
    messages: Mapped[list["Message"]] = relationship(back_populates="session")
    environmental_state: Mapped["EnvironmentalStateRecord | None"] = relationship(
        back_populates="session"
    )


class Message(Base):
    __tablename__ = "messages"

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.session_id"))
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    session: Mapped[Session] = relationship(back_populates="messages")


class EnvironmentalStateRecord(Base):
    __tablename__ = "environmental_states"

    state_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.session_id"), unique=True)
    state_json: Mapped[dict[str, Any]] = mapped_column(JSONType)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    session: Mapped[Session] = relationship(back_populates="environmental_state")
    observations: Mapped[list["EnvironmentalObservation"]] = relationship(
        back_populates="state_record"
    )


class EnvironmentalObservation(Base):
    __tablename__ = "environmental_observations"

    observation_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state_id: Mapped[int] = mapped_column(ForeignKey("environmental_states.state_id"))
    path: Mapped[str] = mapped_column(String(128))
    value_json: Mapped[dict[str, Any]] = mapped_column(JSONType)
    state_record: Mapped[EnvironmentalStateRecord] = relationship(back_populates="observations")


class Document(Base):
    __tablename__ = "documents"

    document_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(512))
    authors: Mapped[list[Any] | None] = mapped_column(JSONType, nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_type: Mapped[str] = mapped_column(String(64))
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[list[Any] | None] = mapped_column(JSONType, nullable=True)
    region: Mapped[list[Any] | None] = mapped_column(JSONType, nullable=True)
    methodology: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    chunk_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.document_id"))
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[Any] | None] = mapped_column(JSONType, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    document: Mapped[Document] = relationship(back_populates="chunks")


class EnvironmentalRelationship(Base):
    __tablename__ = "environmental_relationships"

    relationship_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_variable: Mapped[str] = mapped_column(String(128))
    relationship: Mapped[str] = mapped_column(String(64))
    target_variable: Mapped[str] = mapped_column(String(128))
    direction: Mapped[str] = mapped_column(String(32))
    evidence_required: Mapped[int] = mapped_column(Integer, default=1)


class RecommendationRecord(Base):
    __tablename__ = "recommendations"

    recommendation_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.session_id"))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONType)


class EvidenceLink(Base):
    __tablename__ = "evidence_links"

    link_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recommendation_id: Mapped[int] = mapped_column(ForeignKey("recommendations.recommendation_id"))
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.document_id"))
    chunk_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class EvaluationCase(Base):
    __tablename__ = "evaluation_cases"

    case_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONType)
