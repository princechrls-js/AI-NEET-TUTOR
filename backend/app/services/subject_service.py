import os
from fastapi import HTTPException
from app.core.logger import get_logger

logger = get_logger(__name__)

ALLOWED_SUBJECTS = {"biology", "chemistry", "physics"}

def validate_subject(subject: str) -> str:
    subject = subject.lower().strip()
    if subject not in ALLOWED_SUBJECTS:
        logger.error(f"Invalid subject requested: {subject}")
        raise HTTPException(status_code=400, detail=f"Invalid subject. Allowed: {ALLOWED_SUBJECTS}")
    return subject

def get_subject_paths(subject: str):
    """
    Returns the paths for raw, processed, and vector_store for a subject.
    """
    base = os.path.join("app", "data")
    return {
        "raw": os.path.join(base, "raw", subject),
        "processed": os.path.join(base, "processed", subject),
        "vector_store": os.path.join(base, "vector_store", subject),
    }
