import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
from app.schemas.ingest import IngestResponse
from app.services.subject_service import validate_subject, get_subject_paths
from app.services.pdf_service import save_upload_file, extract_text_from_pdf
from app.services.chunk_service import chunk_text_by_subject
from app.services.embedding_service import get_embeddings
from app.services.vector_service import add_to_vector_store
from app.utils.text_cleaner import clean_text
from app.core.logger import get_logger
from app.services.db_service import record_document_upload
from app.core.auth import require_admin

logger = get_logger(__name__)
router = APIRouter()

@router.post("/upload", response_model=IngestResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    subject: str = Form(...),
    chapter: Optional[str] = Form(None),
    source_name: Optional[str] = Form(None),
    current_user: dict = Depends(require_admin)
):
    """
    Ingests a PDF into a specific subject's vector store.
    """
    subject = validate_subject(subject)
    paths = get_subject_paths(subject)
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    actual_source_name = source_name or file.filename
    safe_filename = file.filename.replace(" ", "_").replace("/", "_")
    
    # 1. Save PDF
    pdf_path = os.path.join(paths["raw"], safe_filename)
    await save_upload_file(file, pdf_path)
    
    try:
        # 2. Extract and clean text
        raw_text = extract_text_from_pdf(pdf_path)
        cleaned_text = clean_text(raw_text)
        
        if not cleaned_text:
            raise ValueError("No text extracted from PDF.")
            
        # 3. Chunk by subject strategy
        chunks = chunk_text_by_subject(subject, cleaned_text)
        
        # 4. Generate embeddings
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = get_embeddings(chunks)
        
        # 5. Save metadata locally (Removed, now everything is in Supabase pgvector)
        metadata_list = []
        for i, chunk_text in enumerate(chunks):
            meta = {
                "chunk_index": i,
                "text": chunk_text,
                "filename": actual_source_name
            }
            metadata_list.append(meta)
            
        # 6. Log to Supabase documents table first to get document_id
        db_record = record_document_upload(actual_source_name, subject, len(chunks))
        if not db_record:
            raise Exception("Failed to record document upload in Supabase.")
            
        document_id = db_record[0]["id"]
            
        # 7. Save to Supabase vector store
        add_to_vector_store(document_id, subject, embeddings, metadata_list)
        
        return IngestResponse(
            subject=subject,
            filename=actual_source_name,
            chunks_created=len(chunks),
            vector_store_path="Supabase pgvector"
        )
        
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ingestion pipeline failed: {str(e)}")
