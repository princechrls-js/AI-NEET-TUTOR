from typing import List
from app.core.logger import get_logger

logger = get_logger(__name__)

def split_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """
    Simple naive chunking by character length with overlap.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - chunk_overlap
    return chunks

def chunk_biology(text: str) -> List[str]:
    """
    Biology: larger conceptual chunks, 700-900 chars, overlap 120-150.
    """
    logger.info("Chunking text using Biology rules")
    return split_text(text, chunk_size=800, chunk_overlap=130)

def chunk_chemistry(text: str) -> List[str]:
    """
    Chemistry: reaction aware chunks, 600-800 chars, overlap 100-120.
    """
    logger.info("Chunking text using Chemistry rules")
    return split_text(text, chunk_size=700, chunk_overlap=110)

def chunk_physics(text: str) -> List[str]:
    """
    Physics: smaller precise chunks, 500-700 chars, overlap 80-100.
    """
    logger.info("Chunking text using Physics rules")
    return split_text(text, chunk_size=600, chunk_overlap=90)

def chunk_text_by_subject(subject: str, text: str) -> List[str]:
    """
    Route to the correct chunking logic.
    """
    if subject == "biology":
        return chunk_biology(text)
    elif subject == "chemistry":
        return chunk_chemistry(text)
    elif subject == "physics":
        return chunk_physics(text)
    else:
        logger.warning(f"Unknown subject {subject}, using default chunking")
        return split_text(text, chunk_size=700, chunk_overlap=100)
