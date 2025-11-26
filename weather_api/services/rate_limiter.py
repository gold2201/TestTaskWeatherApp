from datetime import timedelta
from django.core.cache import cache
from django.utils import timezone

RATE_LIMIT = 30
WINDOW = timedelta(minutes=1)


class RateLimitExceeded(Exception):
    pass


def check_rate_limit(ip: str):
    if not ip:
        raise RateLimitExceeded("IP address missing")

    cache_key = f"rate_limit:{ip}"

    current_count = cache.get(cache_key, 0)

    if current_count >= RATE_LIMIT:
        raise RateLimitExceeded(f"Rate limit exceeded: {RATE_LIMIT} req/min")

    if current_count == 0:
        cache.set(cache_key, 1, timeout=60)
    else:
        cache.incr(cache_key)