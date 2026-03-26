from pydantic import BaseModel

class IngestResponse(BaseModel):
    subject: str
    filename: str
    chunks_created: int
    vector_store_path: str
    status: str = "success"
