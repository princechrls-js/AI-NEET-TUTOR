from fastapi import APIRouter, HTTPException, Depends
from app.schemas.quiz import QuizRequest, QuizResponse
from app.services.subject_service import validate_subject
from app.services.quiz_service import generate_quiz
from app.core.auth import get_current_user
from app.core.logger import get_logger
from app.core.rate_limit import rate_limit

logger = get_logger(__name__)
router = APIRouter()


@router.post("/generate", response_model=QuizResponse)
async def generate_quiz_endpoint(
    request: QuizRequest,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(rate_limit(requests=2, window=60))
):
    """
    Generate NEET-style MCQ quiz questions for a given subject and topic.
    Requires JWT authentication.
    Uses RAG to retrieve relevant context from ingested PDFs, then
    asks the LLM to generate structured MCQs.
    """
    subject = validate_subject(request.subject)

    if request.num_questions < 25 or request.num_questions > 75:
        raise HTTPException(status_code=400, detail="num_questions must be between 25 and 75")

    try:
        questions = await generate_quiz(
            subject=subject,
            topic=request.topic,
            num_questions=request.num_questions,
            top_k=request.top_k,
            difficulty=request.difficulty,
            previous_questions=request.previous_questions
        )

        return QuizResponse(
            subject=subject,
            topic=request.topic,
            num_questions=len(questions),
            questions=questions
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Quiz generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")
