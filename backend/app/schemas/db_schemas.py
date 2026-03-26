from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- Auth Schemas ---

class UserSignup(BaseModel):
    username: str
    email: str
    password: str
    admin_code: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class ForgotPassword(BaseModel):
    email: str

class ResetPassword(BaseModel):
    token: str
    new_password: str

# --- User Schemas ---

class UserCreate(BaseModel):
    username: str
    email: str
    role: str = "student"

class UserResponse(UserCreate):
    id: str
    created_at: datetime

# --- Chat Schemas ---

class ChatMessageCreate(BaseModel):
    user_id: Optional[str] = "anonymous"
    subject: str
    question: str
    answer: str

class ChatMessageResponse(ChatMessageCreate):
    id: int
    created_at: datetime

class ChatHistoryResponse(BaseModel):
    messages: List[dict]
    total_count: int

# --- Progress Schemas ---

class ProgressUpdate(BaseModel):
    user_id: str
    subject: str
    weak_topic: str

