"""FastAPI routes for BOT GPT API."""

import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from src.models import get_db, User, Conversation, Message, Document
from src.api.schemas import (
    UserCreate, UserResponse,
    ConversationCreate, ConversationResponse, ConversationDetailResponse,
    ConversationListResponse, MessageCreate, MessageAddResponse, MessageResponse,
    DocumentResponse, DocumentListResponse
)
from src.services import ConversationService, DocumentService
from src.config import settings

router = APIRouter()


# User endpoints
@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    # Check if user exists
    existing_user = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email or username already exists")

    # Create user
    db_user = User(username=user.username, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Conversation endpoints
@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db)
):
    """Create a new conversation."""
    # Verify user exists
    user = db.query(User).filter(User.id == conversation.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify documents exist if grounded mode
    if conversation.mode == "grounded" and conversation.document_ids:
        for doc_id in conversation.document_ids:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if not doc:
                raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    # Create conversation
    service = ConversationService(db)
    db_conversation = service.create_conversation(
        user_id=conversation.user_id,
        title=conversation.title,
        mode=conversation.mode,
        document_ids=conversation.document_ids
    )

    # If first_message provided, add it and get response
    if conversation.first_message:
        result = await service.add_message_and_get_response(
            db_conversation.id,
            conversation.first_message
        )
        # Return conversation with messages
        return {
            **ConversationResponse.from_orm(result['conversation']).dict(),
            "messages": [
                MessageResponse.from_orm(result['user_message']),
                MessageResponse.from_orm(result['assistant_message'])
            ]
        }

    return db_conversation


@router.get("/conversations", response_model=ConversationListResponse)
def list_conversations(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    mode: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List conversations for a user."""
    # Verify user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    service = ConversationService(db)
    conversations, total = service.list_conversations(user_id, limit, offset, mode)

    return {
        "conversations": conversations,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Get conversation details with messages."""
    service = ConversationService(db)
    conversation = service.get_conversation(conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = service.get_messages(conversation_id)

    return {
        "id": conversation.id,
        "title": conversation.title,
        "mode": conversation.mode,
        "messages": messages,
        "total_tokens": conversation.total_tokens
    }


@router.post("/conversations/{conversation_id}/messages", response_model=MessageAddResponse, status_code=201)
async def add_message(
    conversation_id: str,
    message: MessageCreate,
    db: Session = Depends(get_db)
):
    """Add a message to a conversation and get response."""
    service = ConversationService(db)

    try:
        result = await service.add_message_and_get_response(conversation_id, message.content)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Delete a conversation."""
    service = ConversationService(db)
    success = service.delete_conversation(conversation_id)

    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"message": "Conversation deleted successfully", "conversation_id": conversation_id}


# Document endpoints
@router.post("/documents", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """Upload and process a document."""
    # Verify user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Validate file size
    if file.size and file.size > settings.max_file_size:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {settings.max_file_size} bytes")

    try:
        # Save file
        document_service = DocumentService()
        file_path, file_size = await document_service.save_uploaded_file(file, user_id)

        # Create document record
        document = Document(
            user_id=user_id,
            filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type="application/pdf"
        )
        db.add(document)
        db.flush()

        # Process document
        chunk_count = await document_service.process_document(file_path, document)
        document.chunk_count = chunk_count

        db.commit()
        db.refresh(document)

        return document

    except Exception as e:
        db.rollback()
        # Clean up file if exists
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@router.get("/documents", response_model=DocumentListResponse)
def list_documents(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List documents for a user."""
    # Verify user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    query = db.query(Document).filter(Document.user_id == user_id)
    total = query.count()
    documents = query.order_by(Document.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "documents": documents,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get document by ID."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    # Delete from ChromaDB
    document_service = DocumentService()
    await document_service.delete_document_chunks(document_id)

    # Delete from database
    db.delete(document)
    db.commit()

    return {"message": "Document deleted successfully", "document_id": document_id}
