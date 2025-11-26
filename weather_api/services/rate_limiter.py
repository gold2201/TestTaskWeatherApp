from datetime import timedelta
from django.core.cache import cache
from django.utils import timezone
import logging

RATE_LIMIT = 30
WINDOW = timedelta(minutes=1)

logger = logging.getLogger('weather')

class RateLimitExceeded(Exception):
    pass

def check_rate_limit(ip: str):
    """
    Redis-based rate limiting: 30 requests per minute per IP.
    Uses atomic Redis operations to ensure thread safety.
    """
    if not ip:
        logger.warning(
            "Rate limit check failed - missing IP address",
            extra={
                'event': 'rate_limit_missing_ip',
                'error': 'IP address missing',
            }
        )
        raise RateLimitExceeded("IP address missing")

    cache_key = f"rate_limit:{ip}"
    current_count = cache.get(cache_key, 0)

    if current_count >= RATE_LIMIT:
        logger.warning(
            "Rate limit exceeded",
            extra={
                'ip': ip,
                'event': 'rate_limit_exceeded',
                'current_count': current_count,
                'limit': RATE_LIMIT,
            }
        )
        raise RateLimitExceeded(f"Rate limit exceeded: {RATE_LIMIT} req/min")

    if current_count == 0:
        cache.set(cache_key, 1, timeout=60)
    else:
        cache.incr(cache_key)

    logger.debug(
        "Rate limit check passed",
        extra={
            'ip': ip,
            'event': 'rate_limit_check',
            'current_count': current_count + 1,
            'limit': RATE_LIMIT,
        }
    )