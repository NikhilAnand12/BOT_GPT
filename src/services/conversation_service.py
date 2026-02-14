"""Conversation Service for managing conversations and messages."""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from src.models.models import Conversation, Message, User
from src.services.llm_service import LLMService
from src.services.document_service import DocumentService


class ConversationService:
    """Service for conversation management."""

    def __init__(self, db: Session):
        """Initialize conversation service."""
        self.db = db
        self.llm_service = LLMService()
        self.document_service = DocumentService()

    def create_conversation(
        self,
        user_id: str,
        title: str,
        mode: str = "open_chat",
        document_ids: List[str] = None
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            user_id=user_id,
            title=title,
            mode=mode
        )

        if document_ids:
            conversation.set_document_ids(document_ids)

        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        return conversation

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def list_conversations(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        mode: str = None
    ) -> tuple:
        """List conversations for a user."""
        query = self.db.query(Conversation).filter(Conversation.user_id == user_id)

        if mode:
            query = query.filter(Conversation.mode == mode)

        total = query.count()
        conversations = query.order_by(Conversation.updated_at.desc()).offset(offset).limit(limit).all()

        return conversations, total

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False

        self.db.delete(conversation)
        self.db.commit()
        return True

    def get_messages(self, conversation_id: str) -> List[Message]:
        """Get all messages for a conversation."""
        return self.db.query(Message)\
            .filter(Message.conversation_id == conversation_id)\
            .order_by(Message.sequence_number)\
            .all()

    def get_next_sequence_number(self, conversation_id: str) -> int:
        """Get next sequence number for a conversation."""
        last_message = self.db.query(Message)\
            .filter(Message.conversation_id == conversation_id)\
            .order_by(Message.sequence_number.desc())\
            .first()

        return (last_message.sequence_number + 1) if last_message else 0

    async def add_message_and_get_response(
        self,
        conversation_id: str,
        user_message_content: str
    ) -> Dict:
        """Add user message and generate assistant response."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError("Conversation not found")

        # Get conversation history
        messages = self.get_messages(conversation_id)

        # Get next sequence numbers
        user_seq = self.get_next_sequence_number(conversation_id)
        assistant_seq = user_seq + 1

        # Count tokens in user message
        user_tokens = self.llm_service.count_tokens(user_message_content)

        # Create user message
        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=user_message_content,
            tokens=user_tokens,
            sequence_number=user_seq
        )
        self.db.add(user_message)
        self.db.flush()

        # Handle RAG if in grounded mode
        retrieved_context = []
        rag_context_str = None

        if conversation.mode == "grounded":
            document_ids = conversation.get_document_ids()
            if document_ids:
                retrieved_context = await self.document_service.retrieve_relevant_chunks(
                    user_message_content,
                    document_ids
                )
                if retrieved_context:
                    rag_context_str = self.document_service.format_rag_context(retrieved_context)

        # Get LLM response
        all_messages = messages + [user_message]
        llm_response = await self.llm_service.generate_response(
            all_messages,
            rag_context=rag_context_str
        )

        # Create assistant message
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=llm_response['content'],
            tokens=llm_response['output_tokens'],
            sequence_number=assistant_seq
        )

        # Store RAG context in metadata if available
        if retrieved_context:
            assistant_message.set_metadata({
                "rag_chunks_used": len(retrieved_context),
                "rag_similarity_scores": [c['similarity_score'] for c in retrieved_context]
            })

        self.db.add(assistant_message)

        # Update conversation totals
        conversation.total_tokens += user_tokens + llm_response['output_tokens']
        conversation.updated_at = user_message.created_at

        self.db.commit()
        self.db.refresh(user_message)
        self.db.refresh(assistant_message)

        return {
            "user_message": user_message,
            "assistant_message": assistant_message,
            "conversation": conversation,
            "retrieved_context": retrieved_context if conversation.mode == "grounded" else None
        }
