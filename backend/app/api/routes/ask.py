from fastapi import APIRouter, HTTPException, Depends
from app.schemas.ask import AskRequest, AskResponse
from app.services.subject_service import validate_subject, get_subject_paths
from app.services.rag_service import ask_question, ask_question_stream
from app.core.logger import get_logger
from app.core.auth import get_current_user
from app.core.rate_limit import rate_limit

logger = get_logger(__name__)
router = APIRouter()

@router.post("/")
async def ask_endpoint(
    request: AskRequest, 
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(rate_limit(requests=5, window=60))
):
    """
    Ask a question against a specific subject's ingested knowledge.
    Requires JWT authentication.
    Supports both synchronous JSON and Server-Sent Events (SSE) streaming.
    """
    subject = validate_subject(request.subject)
    user_id = current_user.get("user_id", "anonymous")
    history = [turn.model_dump() for turn in request.conversation_history] if request.conversation_history else None
    
    try:
        if request.stream:
            from sse_starlette.sse import EventSourceResponse
            
            stream_generator = ask_question_stream(
                subject=subject,
                question=request.question,
                top_k=request.top_k,
                user_id=user_id,
                conversation_history=history
            )
            return EventSourceResponse(stream_generator)
            
        else:
            result = await ask_question(
                subject=subject,
                question=request.question,
                top_k=request.top_k,
                user_id=user_id,
                conversation_history=history
            )
            
            return AskResponse(
                subject=subject,
                question=request.question,
                answer=result["answer"],
                citations=result["citations"],
                agent=result.get("agent"),
                difficulty=result.get("difficulty")
            )
            
    except Exception as e:
        logger.error(f"Ask endpoint failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")
