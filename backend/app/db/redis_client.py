import redis.asyncio as redis
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

redis_client = None

async def init_redis():
    global redis_client
    if settings.REDIS_URL:
        try:
            redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await redis_client.ping()
            logger.info("Successfully connected to Redis.")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            redis_client = None

async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
