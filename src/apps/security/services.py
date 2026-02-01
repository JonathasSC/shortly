import time
from urllib.parse import urlparse

import redis
from django.conf import settings

BASE_DELAY = 15


class RedisConnectionService:
    @staticmethod
    def get_redis_client():
        url = getattr(settings, "REDIS_URL",
                      None) or "redis://localhost:6379/0"
        return redis.Redis.from_url(url)


class ExponentialBanService:
    @staticmethod
    def register_lockout(username):
        key = f"ban:{username}:count"

        client = RedisConnectionService.get_redis_client()
        count = client.incr(key)

        delay = BASE_DELAY * (2 ** (count - 1))

        ban_key = f"ban:{username}:until"
        client.setex(ban_key, delay, int(time.time()) + delay)

        return delay

    @staticmethod
    def get_ban_remaining(username):
        client = RedisConnectionService.get_redis_client()
        ban_key = f"ban:{username}:until"
        ts = client.get(ban_key)
        if not ts:
            return 0
        now = int(time.time())
        return max(0, int(ts) - now)


class WebSocketOriginService:

    @staticmethod
    def _normalized_allowed_origins() -> set[str]:
        return {
            origin.lower().rstrip("/")
            for origin in getattr(settings, "ALLOWED_WS_ORIGINS", [])
        }

    @staticmethod
    def extract_base_origin(origin: str) -> str | None:
        try:
            parsed = urlparse(origin)
            if not parsed.scheme or not parsed.netloc:
                return None
            return f"{parsed.scheme}://{parsed.netloc}".lower()
        except Exception:
            return None

    @staticmethod
    def is_allowed(origin: str | None) -> bool:
        if not origin:
            return False

        base_origin = WebSocketOriginService.extract_base_origin(origin)
        if not base_origin:
            return False

        return base_origin in WebSocketOriginService._normalized_allowed_origins()
