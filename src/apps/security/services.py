import time

import redis
from django.conf import settings

client = redis.Redis.from_url(settings.REDIS_URL)

BASE_DELAY = 15


class ExponentialBanService:
    @staticmethod
    def register_lockout(username):
        key = f"ban:{username}:count"

        count = client.incr(key)

        delay = BASE_DELAY * (2 ** (count - 1))

        ban_key = f"ban:{username}:until"
        client.setex(ban_key, delay, int(time.time()) + delay)

        return delay

    @staticmethod
    def get_ban_remaining(username):
        ban_key = f"ban:{username}:until"
        ts = client.get(ban_key)
        if not ts:
            return 0
        now = int(time.time())
        return max(0, int(ts) - now)
