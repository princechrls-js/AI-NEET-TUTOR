from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str = "ok"

class SubjectResponse(BaseModel):
    available_subjects: list[str] = ["biology", "chemistry", "physics"]
