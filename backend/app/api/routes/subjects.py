from fastapi import APIRouter
from app.schemas.common import SubjectResponse
from app.services.subject_service import ALLOWED_SUBJECTS

router = APIRouter()

@router.get("/", response_model=SubjectResponse)
def list_subjects():
    """
    Returns the supported subjects.
    """
    return SubjectResponse(available_subjects=list(ALLOWED_SUBJECTS))
