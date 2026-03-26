from fastapi import APIRouter, HTTPException, Depends
from app.schemas.db_schemas import UserCreate, UserResponse, ProgressUpdate
from app.db.client import supabase_client
from app.core.logger import get_logger
from app.core.auth import get_current_user, require_admin

logger = get_logger(__name__)
router = APIRouter()

@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, current_user: dict = Depends(require_admin)):
    """
    Creates a new student user in Supabase (legacy endpoint).
    For new users, prefer /auth/signup which includes password and JWT.
    """
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    try:
        response = supabase_client.table("users").insert({
            "username": user.username,
            "email": user.email
        }).execute()
        
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/progress")
def update_progress(progress: ProgressUpdate, current_user: dict = Depends(get_current_user)):
    """
    Records a student's weak topic for a specific subject.
    Requires JWT authentication.
    """
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    try:
        response = supabase_client.table("progress").insert({
            "user_id": current_user["user_id"],
            "subject": progress.subject,
            "weak_topic": progress.weak_topic
        }).execute()
        return {"status": "success", "recorded": response.data}
    except Exception as e:
        logger.error(f"Error updating progress: {e}")
        raise HTTPException(status_code=400, detail=str(e))
