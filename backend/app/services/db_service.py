from app.db.client import supabase_client
from app.core.logger import get_logger
from app.schemas.db_schemas import ChatMessageCreate

logger = get_logger(__name__)

def log_chat_interaction(chat_data: ChatMessageCreate):
    """
    Logs a Q&A interaction into the 'chat_messages' table.
    """
    if not supabase_client:
        logger.warning("Supabase client not initialized. Skipping DB log.")
        return None
        
    try:
        response = supabase_client.table("chat_messages").insert({
            "user_id": chat_data.user_id,
            "subject": chat_data.subject,
            "question": chat_data.question,
            "answer": chat_data.answer
        }).execute()
        return response.data
    except Exception as e:
        logger.error(f"Failed to log chat interaction: {e}")
        return None

def record_document_upload(filename: str, subject: str, chunks: int):
    """
    Records a successful PDF upload into the 'documents' table.
    """
    if not supabase_client:
        return None
        
    try:
        response = supabase_client.table("documents").insert({
            "filename": filename,
            "subject": subject,
            "chunks_created": chunks
        }).execute()
        return response.data
    except Exception as e:
        logger.error(f"Failed to record document upload: {e}")
        return None


def get_chat_history(user_id: str, subject: str = None, limit: int = 50, offset: int = 0):
    """
    Retrieves chat history for a user, optionally filtered by subject.
    Returns paginated results ordered by newest first.
    """
    if not supabase_client:
        logger.warning("Supabase client not initialized.")
        return []
    
    try:
        query = supabase_client.table("chat_messages") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .range(offset, offset + limit - 1)
        
        if subject:
            query = query.eq("subject", subject)
        
        response = query.execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Failed to fetch chat history: {e}")
        return []


def get_chat_count(user_id: str, subject: str = None):
    """
    Returns the total count of chat messages for a user.
    """
    if not supabase_client:
        return 0
    
    try:
        query = supabase_client.table("chat_messages") \
            .select("id", count="exact") \
            .eq("user_id", user_id)
        
        if subject:
            query = query.eq("subject", subject)
        
        response = query.execute()
        return response.count if response.count else 0
    except Exception as e:
        logger.error(f"Failed to count chat messages: {e}")
        return 0
