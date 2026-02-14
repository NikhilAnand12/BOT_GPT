"""LLM Service for interacting with Gemini via LangChain."""

from typing import List, Dict
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from src.config import settings
from src.models.models import Message


class LLMService:
    """Service for LLM interactions."""

    def __init__(self):
        """Initialize LLM service."""
        self.llm = ChatGroq(
            model=settings.llm_model,
            groq_api_key=settings.groq_api_key,
            temperature=0,
            max_tokens=settings.max_response_tokens,
        )

    def count_tokens(self, text: str) -> int:
        """Count tokens in text (approximate: 1 token ≈ 4 characters)."""
        return len(text) // 4

    def format_messages_for_llm(self, messages: List[Message], system_prompt: str = None) -> List:
        """Convert database messages to LangChain format."""
        langchain_messages = []

        # Add system prompt
        if system_prompt:
            langchain_messages.append(SystemMessage(content=system_prompt))

        # Add conversation messages
        for msg in messages:
            if msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_messages.append(AIMessage(content=msg.content))
            elif msg.role == "system":
                langchain_messages.append(SystemMessage(content=msg.content))

        return langchain_messages

    def get_context_window(self, messages: List[Message], max_tokens: int = None) -> List[Message]:
        """Get messages that fit within token budget."""
        if max_tokens is None:
            max_tokens = settings.max_context_tokens

        # Reverse to process most recent first
        reversed_messages = list(reversed(messages))
        selected_messages = []
        token_count = 0

        for msg in reversed_messages:
            if token_count + msg.tokens > max_tokens:
                break
            selected_messages.insert(0, msg)  # Prepend to maintain chronological order
            token_count += msg.tokens

        return selected_messages

    async def generate_response(
        self,
        messages: List[Message],
        rag_context: str = None,
        system_prompt: str = None
    ) -> Dict[str, any]:
        """Generate LLM response."""
        # Default system prompt
        if system_prompt is None:
            system_prompt = "You are BOT GPT, a helpful AI assistant. Provide direct, concise answers without showing your reasoning process or thinking steps. Never include internal thought processes like 'Okay, let me think' or 'I should'. Just give the final answer directly."

        # Add RAG context to system prompt if provided
        if rag_context:
            system_prompt = """You are BOT GPT. You MUST answer questions STRICTLY based on the provided document context ONLY.

CRITICAL RULES:
1. Use ONLY information from the provided context below
2. DO NOT use your general knowledge or training data
3. If the answer is not in the context, say "I don't have that information in the uploaded documents"
4. Never make assumptions or infer information not explicitly stated in the context
5. Provide direct answers without showing reasoning

Context from documents:
""" + rag_context

        # Get messages within context window
        context_messages = self.get_context_window(messages)

        # Format for LLM
        langchain_messages = self.format_messages_for_llm(context_messages, system_prompt)

        # Generate response
        response = await self.llm.agenerate([langchain_messages])
        assistant_message = response.generations[0][0].text

        # Count tokens
        input_tokens = sum(msg.tokens for msg in context_messages)
        output_tokens = self.count_tokens(assistant_message)

        return {
            "content": assistant_message,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens
        }

    async def generate_title(self, first_message: str) -> str:
        """Generate conversation title from first message."""
        prompt = f"Generate a short, concise title (max 6 words) for a conversation that starts with: '{first_message}'. Return only the title, nothing else."

        messages = [HumanMessage(content=prompt)]
        response = await self.llm.agenerate([messages])
        title = response.generations[0][0].text.strip().strip('"').strip("'")

        # Limit length
        if len(title) > 60:
            title = title[:57] + "..."

        return title
