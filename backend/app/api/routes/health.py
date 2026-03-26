from fastapi import APIRouter
from app.schemas.common import HealthResponse

router = APIRouter()

@router.get("/", response_model=HealthResponse)
def health_check():
    """
    Health check endpoint.
    """
    return HealthResponse(status="ok")
