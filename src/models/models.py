"""SQLAlchemy database models."""

import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from .database import Base


def generate_uuid():
    """Generate UUID as string."""
    return str(uuid.uuid4())


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String, default=lambda: datetime.utcnow().isoformat(), onupdate=lambda: datetime.utcnow().isoformat())

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    """Conversation model."""

    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    mode = Column(String(20), nullable=False, default="open_chat")
    document_ids = Column(Text, default="[]")  # JSON array
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String, default=lambda: datetime.utcnow().isoformat(), onupdate=lambda: datetime.utcnow().isoformat())
    total_tokens = Column(Integer, default=0)
    extra_data = Column(Text, default="{}")  # JSON object

    __table_args__ = (
        CheckConstraint("mode IN ('open_chat', 'grounded')", name="check_mode"),
    )

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.sequence_number")

    def get_document_ids(self):
        """Get document IDs as list."""
        return json.loads(self.document_ids)

    def set_document_ids(self, doc_ids: list):
        """Set document IDs from list."""
        self.document_ids = json.dumps(doc_ids)

    def get_metadata(self):
        """Get metadata as dict."""
        return json.loads(self.extra_data)

    def set_metadata(self, meta: dict):
        """Set metadata from dict."""
        self.extra_data = json.dumps(meta)


class Message(Base):
    """Message model."""

    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    tokens = Column(Integer, default=0)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    sequence_number = Column(Integer, nullable=False)
    extra_data = Column(Text, default="{}")  # JSON object

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="check_role"),
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def get_metadata(self):
        """Get metadata as dict."""
        return json.loads(self.extra_data)

    def set_metadata(self, meta: dict):
        """Set metadata from dict."""
        self.extra_data = json.dumps(meta)


class Document(Base):
    """Document model."""

    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    chunk_count = Column(Integer, default=0)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    extra_data = Column(Text, default="{}")  # JSON object

    # Relationships
    user = relationship("User", back_populates="documents")

    def get_metadata(self):
        """Get metadata as dict."""
        return json.loads(self.extra_data)

    def set_metadata(self, meta: dict):
        """Set metadata from dict."""
        self.extra_data = json.dumps(meta)
