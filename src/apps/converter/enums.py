from enum import Enum


class PricingRule(Enum):
    BASE = "base"
    DIRECT = "direct"
    PERMANENT = "permanent"


class ShortenResult(Enum):
    CREATED = "created"
    EXISTS = "exists"


class AnonymousLimitExceeded(Exception):
    pass


ANONYMOUS_DAILY_LIMIT = 3