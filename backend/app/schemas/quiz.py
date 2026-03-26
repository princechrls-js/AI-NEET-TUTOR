from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class QuizRequest(BaseModel):
    subject: str
    topic: str
    num_questions: int = Field(25, ge=25, le=75)
    top_k: int = 5
    difficulty: Literal["Easy", "Medium", "Hard"] = "Medium"
    previous_questions: Optional[List[str]] = None


class QuizOption(BaseModel):
    label: str  # A, B, C, D
    text: str


class QuizQuestion(BaseModel):
    question_number: int
    question: str
    options: List[QuizOption]
    correct_answer: str  # A, B, C, or D
    explanation: str
    difficulty: str  # Easy, Medium, Hard


class QuizResponse(BaseModel):
    subject: str
    topic: str
    num_questions: int
    questions: List[QuizQuestion]
