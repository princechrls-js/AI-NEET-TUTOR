from fastapi import APIRouter, HTTPException, Depends, Query
from app.schemas.db_schemas import ChatHistoryResponse
from app.services.db_service import get_chat_history, get_chat_count
from app.core.auth import get_current_user
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=ChatHistoryResponse)
def get_history(
    limit: int = Query(default=50, ge=1, le=100, description="Number of messages to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns paginated chat history for the authenticated user.
    Requires JWT authentication.
    """
    user_id = current_user["user_id"]
    
    messages = get_chat_history(user_id, limit=limit, offset=offset)
    total = get_chat_count(user_id)
    
    return ChatHistoryResponse(messages=messages, total_count=total)


@router.get("/{subject}", response_model=ChatHistoryResponse)
def get_history_by_subject(
    subject: str,
    limit: int = Query(default=50, ge=1, le=100, description="Number of messages to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns paginated chat history filtered by subject for the authenticated user.
    Requires JWT authentication.
    """
    from app.services.subject_service import validate_subject
    subject = validate_subject(subject)
    user_id = current_user["user_id"]
    
    messages = get_chat_history(user_id, subject=subject, limit=limit, offset=offset)
    total = get_chat_count(user_id, subject=subject)
    
    return ChatHistoryResponse(messages=messages, total_count=total)
