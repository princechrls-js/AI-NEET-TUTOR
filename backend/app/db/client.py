from supabase import create_client, Client
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

supabase_client: Client = None

if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    try:
        supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("Successfully connected to Supabase.")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
else:
    logger.warning("SUPABASE_URL and SUPABASE_KEY are not set in environment variables.")
