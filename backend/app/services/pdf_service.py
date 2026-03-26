import os
import shutil
from fastapi import UploadFile
from pypdf import PdfReader
import pypdf.filters

# Increase decompression limits for large PDFs
pypdf.filters.MIN_LZW_DECODE_PREDICTOR = 1 # Not required but safe
pypdf.filters.MAX_DECLARED_STREAM_LENGTH = 500_000_000
pypdf.filters.MAX_ARRAY_BASED_STREAM_OUTPUT_LENGTH = 500_000_000
pypdf.filters.ZLIB_MAX_OUTPUT_LENGTH = 500_000_000
pypdf.filters.LZW_MAX_OUTPUT_LENGTH = 500_000_000

from app.core.logger import get_logger

logger = get_logger(__name__)

async def save_upload_file(upload_file: UploadFile, destination_path: str) -> str:
    """
    Saves an uploaded file to a specific destination.
    """
    try:
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        with open(destination_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        logger.info(f"Saved file to {destination_path}")
        return destination_path
    except Exception as e:
        logger.error(f"Error saving PDF: {str(e)}")
        raise e
    finally:
        upload_file.file.close()

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts raw text from a PDF file.
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path}: {e}")
        raise e
