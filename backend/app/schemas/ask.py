from pydantic import BaseModel, Field
from typing import List, Optional

class ConversationTurn(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class AskRequest(BaseModel):
    subject: str = Field(..., description="Subject: biology, chemistry, or physics")
    question: str = Field(..., description="The student's question")
    top_k: int = Field(5, description="Number of chunks to retrieve")
    stream: bool = Field(False, description="Whether to stream the answer using Server-Sent Events (SSE)")
    conversation_history: Optional[List[ConversationTurn]] = Field(None, description="Previous conversation turns for context")

class Citation(BaseModel):
    source_name: str
    chunk_index: int
    text_snippet: str

class AskResponse(BaseModel):
    subject: str
    question: str
    answer: str
    citations: List[Citation]
    agent: Optional[str] = None
    difficulty: Optional[str] = None
