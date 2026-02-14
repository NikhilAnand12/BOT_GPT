"""Pydantic schemas for API request/response validation."""

from typing import List, Optional
from pydantic import BaseModel


# User schemas
class UserCreate(BaseModel):
    username: str
    email: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: str

    class Config:
        from_attributes = True


# Conversation schemas
class ConversationCreate(BaseModel):
    user_id: str
    title: str
    mode: str = "open_chat"
    document_ids: List[str] = []
    first_message: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    tokens: int
    created_at: str
    sequence_number: int

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    mode: str
    document_ids: str
    created_at: str
    updated_at: str
    total_tokens: int

    class Config:
        from_attributes = True


class ConversationDetailResponse(BaseModel):
    id: str
    title: str
    mode: str
    messages: List[MessageResponse]
    total_tokens: int


class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int
    limit: int
    offset: int


# Message schemas
class MessageCreate(BaseModel):
    content: str


class MessageAddResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    conversation: ConversationResponse
    retrieved_context: Optional[List[dict]] = None


# Document schemas
class DocumentResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    file_size: int
    file_type: str
    chunk_count: int
    created_at: str

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    limit: int
    offset: int


# Error schema
class ErrorResponse(BaseModel):
    error: dict
