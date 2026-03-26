from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory
from app.core.config import settings
from app.core.logger import get_logger
from typing import List

logger = get_logger(__name__)

class InMemoryHistory(BaseChatMessageHistory):
    """Simple in-memory fallback for chat history."""
    def __init__(self):
        self.messages: List[BaseMessage] = []

    def add_messages(self, messages: List[BaseMessage]) -> None:
        self.messages.extend(messages)

    def clear(self) -> None:
        self.messages = []

# Simple global dict to store in-memory histories for the session
_in_memory_stores = {}

def get_chat_history(session_id: str) -> BaseChatMessageHistory:
    """
    Returns a Redis-backed ChatMessageHistory for the given session ID.
    Falls back to In-Memory history if Redis is unavailable.
    """
    try:
        url = settings.REDIS_URL or "redis://localhost:6379/0"
        history = RedisChatMessageHistory(
            session_id=session_id,
            url=url,
            key_prefix="astra_mem:",
            ttl=86400  # 24 hour expiry
        )
        # Force an eager connection test — the constructor doesn't actually
        # connect to Redis; it only connects when .messages is accessed.
        _ = history.messages
        return history
    except Exception as e:
        logger.warning(f"Redis memory unavailable, falling back to in-memory: {e}")
        if session_id not in _in_memory_stores:
            _in_memory_stores[session_id] = InMemoryHistory()
        return _in_memory_stores[session_id]
