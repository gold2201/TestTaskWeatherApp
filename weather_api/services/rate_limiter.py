from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from ..models import WeatherQuery

RATE_LIMIT = 30
WINDOW = timedelta(minutes=1)

class RateLimitExceeded(Exception):
    pass

def check_rate_limit(ip: str):
    if not ip:
        raise RateLimitExceeded("IP address missing")

    now = timezone.now()

    count = WeatherQuery.objects.filter(
        ip_address=ip,
        timestamp__gte=now - WINDOW
    ).count()

    if count >= RATE_LIMIT:
        raise RateLimitExceeded(f"Rate limit exceeded: {RATE_LIMIT} req/min")
