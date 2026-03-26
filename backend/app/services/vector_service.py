import os
from typing import List, Dict, Any, Tuple
from app.core.logger import get_logger
from app.db.client import supabase_client

logger = get_logger(__name__)

def add_to_vector_store(document_id: int, subject: str, embeddings: List[List[float]], metadata_list: List[Dict[str, Any]]):
    """
    Inserts embeddings and text chunks into the Supabase 'document_chunks' table.
    """
    if not supabase_client:
        raise ValueError("Supabase client is not initialized.")
        
    records = []
    for emb, meta in zip(embeddings, metadata_list):
        records.append({
            "document_id": document_id,
            "subject": subject,
            "chunk_index": meta.get("chunk_index"),
            "text_content": meta.get("text"),
            "filename": meta.get("filename"),
            "embedding": emb
        })
        
    try:
        # We can batch insert if needed, but for typical PDFs a single bulk insert works
        response = supabase_client.table("document_chunks").insert(records).execute()
        logger.info(f"Inserted {len(records)} chunks into Supabase pgvector.")
        return len(records)
    except Exception as e:
        logger.error(f"Failed to insert vectors into Supabase: {e}")
        raise e

def search_vector_store(subject: str, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Searches the Supabase pgvector index using the match_document_chunks RPC.
    """
    if not supabase_client:
        logger.error("Supabase client not initialized for search.")
        return []

    try:
        response = supabase_client.rpc(
            "match_document_chunks",
            {
                "query_embedding": query_embedding,
                "match_count": top_k,
                "filter_subject": subject
            }
        ).execute()
        
        # Format the response to match the old FAISS structure for compatibility with rag_service
        results = []
        for row in response.data:
            results.append({
                "document_id": row["document_id"],
                "subject": row["subject"],
                "chunk_index": row["chunk_index"],
                "text": row["text_content"],
                "filename": row["filename"],
                "distance": row["similarity"]
            })
            
        return results
    except Exception as e:
        logger.error(f"Failed to search Supabase vector store: {e}")
        return []
