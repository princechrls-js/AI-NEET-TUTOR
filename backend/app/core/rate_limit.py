import time
import logging
from fastapi import HTTPException, status, Request
from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)

# Redis token bucket rate limiting script
# KEYS[1] = key
# ARGV[1] = capacity
# ARGV[2] = window in seconds
# ARGV[3] = current timestamp in seconds

RATE_LIMIT_LUA_SCRIPT = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local fill_time = window / capacity

-- get current bucket data
local bucket = redis.call("HMGET", key, "tokens", "last_update")
local tokens = tonumber(bucket[1])
local last_update = tonumber(bucket[2])

if tokens == nil then
    tokens = capacity
    last_update = now
else
    -- calculate how many tokens have generated since last update
    local elapsed = now - last_update
    local generated = math.floor(elapsed / fill_time)
    
    tokens = math.min(capacity, tokens + generated)
    if generated > 0 then
        -- we only move last_update forward by the discrete amount of generated tokens
        last_update = last_update + (generated * fill_time)
    end
end

if tokens >= 1 then
    tokens = tokens - 1
    redis.call("HMSET", key, "tokens", tokens, "last_update", last_update)
    redis.call("EXPIRE", key, window)
    return 1 -- Allowed
else
    return 0 -- Denied
end
"""


class RateLimiter:
    def __init__(self, requests: int, window: int):
        self.capacity = requests
        self.window = window
        self._script = None

    async def __call__(self, request: Request):

        if not redis_client:
            # If Redis is disabled/unavailable, bypass rate limiting

            return True

        if not hasattr(request.state, "user_id"):
            # We attempt to get user id from auth context, otherwise use client IP
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                from app.core.auth import decode_access_token
                token = auth_header.split(" ")[1]
                payload = decode_access_token(token)
                identifier = payload.get("sub") if payload else request.client.host
            else:
                identifier = request.client.host
        else:
            identifier = request.state.user_id

        key = f"rate_limit:{request.url.path}:{identifier}"
        now = int(time.time())

        # Register script if needed
        if not self._script:
            self._script = redis_client.register_script(RATE_LIMIT_LUA_SCRIPT)
            
        try:
            allowed = await self._script(keys=[key], args=[self.capacity, self.window, now])
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {self.window} seconds."
                )
            return True
        except Exception as e:
            # Failsafe open pattern - if Redis crashes, allow the request
            logger.warning(f"Rate Limiter Redis Error: {e}")
            return True


def rate_limit(requests: int, window: int = 60):
    """
    FastAPI Dependency to apply a token-bucket rate limit per user (or IP) per route.
    Usage: Depends(rate_limit(requests=5, window=60))
    """
    return RateLimiter(requests, window)
