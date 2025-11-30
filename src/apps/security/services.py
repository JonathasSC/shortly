import time

import redis
from django.conf import settings



BASE_DELAY = 15


def get_redis_client():
    url = getattr(settings, "REDIS_URL", None) or "redis://localhost:6379/0"
    return redis.Redis.from_url(url)

class ExponentialBanService:
    @staticmethod
    def register_lockout(username):
        key = f"ban:{username}:count"

        client = get_redis_client()
        count = client.incr(key)

        delay = BASE_DELAY * (2 ** (count - 1))

        ban_key = f"ban:{username}:until"
        client.setex(ban_key, delay, int(time.time()) + delay)

        return delay

@staticmethod
def get_ban_remaining(username):
        client = get_redis_client()
        ban_key = f"ban:{username}:until"
        ts = client.get(ban_key)
        if not ts:
            return 0
        now = int(time.time())
        return max(0, int(ts) - now)
