from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
import logging
import pickle

from ..models import WeatherQuery, Location, WeatherData
from .weather_api_service import OpenWeatherAPI
from .rate_limiter import check_rate_limit, RateLimitExceeded

logger = logging.getLogger("weather")
CACHE_TTL = timedelta(minutes=5)


def get_weather_for_city(city_name: str, units: str = "C", ip_address: str = None) -> WeatherQuery:
    """
    Main weather data retrieval with multi-layer caching strategy:
    1. Redis cache (fast, in-memory) - 5 minutes
    2. Database cache (persistent) - 5 minutes
    3. External API (fresh data) - with automatic cache update
    """
    check_rate_limit(ip_address)

    now = timezone.now()
    normalized_city = city_name.strip().lower()

    redis_cache_key = f"weather:{normalized_city}:{units}"

    logger.info(
        "Checking cache for city",
        extra={
            'ip': ip_address or 'unknown',
            'event': 'cache_check',
            'city': normalized_city,
            'units': units,
        }
    )

    cached_data = cache.get(redis_cache_key)
    if cached_data:
        logger.info(
            "Redis cache hit - using cached data",
            extra={
                'ip': ip_address or 'unknown',
                'event': 'redis_cache_hit',
                'city': normalized_city,
                'units': units,
            }
        )
        location, weather_data = pickle.loads(cached_data)

        new_query = WeatherQuery.objects.create(
            location=location,
            weather_data=weather_data,
            units=units,
            ip_address=ip_address,
            served_from_cache=True,
            raw_response=None,
        )
        return new_query

    logger.info(
        "Redis cache miss - checking database cache",
        extra={
            'ip': ip_address or 'unknown',
            'event': 'redis_cache_miss',
            'city': normalized_city,
            'units': units,
        }
    )

    last_query = WeatherQuery.objects.filter(
        location__city__iexact=normalized_city,
        units=units,
        timestamp__gte=now - CACHE_TTL
    ).select_related('location', 'weather_data').order_by('-timestamp').first()

    if last_query and last_query.weather_data:
        logger.info(
            "Database cache hit - using cached data",
            extra={
                'ip': ip_address or 'unknown',
                'event': 'db_cache_hit',
                'city': normalized_city,
                'units': units,
            }
        )

        cache_data = pickle.dumps((last_query.location, last_query.weather_data))
        cache.set(redis_cache_key, cache_data, timeout=300)

        new_query = WeatherQuery.objects.create(
            location=last_query.location,
            weather_data=last_query.weather_data,
            units=units,
            ip_address=ip_address,
            served_from_cache=True,
            raw_response=last_query.raw_response,
        )
        return new_query

    logger.info(
        "All cache miss - fetching from external API",
        extra={
            'ip': ip_address or 'unknown',
            'event': 'api_fetch',
            'city': normalized_city,
            'units': units,
        }
    )

    try:
        raw_data = OpenWeatherAPI.fetch_weather(city_name, units)

        logger.info(
            "External API response received successfully",
            extra={
                'ip': ip_address or 'unknown',
                'event': 'api_success',
                'city': normalized_city,
                'units': units,
            }
        )

        location_data = OpenWeatherAPI.normalize_location_data(raw_data)
        weather_data_dict = OpenWeatherAPI.normalize_weather_data(raw_data)

        with transaction.atomic():
            location_city = location_data["city"].lower().strip() if location_data.get("city") else normalized_city

            location, created = Location.objects.get_or_create(
                city=location_city,
                country_code=location_data.get("country_code", ""),
                defaults={
                    "city": location_city,
                    "country_code": location_data.get("country_code", ""),
                    "latitude": location_data.get("latitude"),
                    "longitude": location_data.get("longitude"),
                }
            )

            weather_data = WeatherData.objects.create(**weather_data_dict)

            new_query = WeatherQuery.objects.create(
                location=location,
                weather_data=weather_data,
                units=units,
                ip_address=ip_address,
                served_from_cache=False,
                raw_response=raw_data,
            )

            cache_data = pickle.dumps((location, weather_data))
            cache.set(redis_cache_key, cache_data, timeout=300)

            logger.info(
                "Data successfully saved to cache",
                extra={
                    'ip': ip_address or 'unknown',
                    'event': 'cache_update',
                    'city': normalized_city,
                    'units': units,
                }
            )

        return new_query

    except Exception as e:
        logger.error(
            "Error fetching weather data from external API",
            extra={
                'ip': ip_address or 'unknown',
                'event': 'api_error',
                'city': normalized_city,
                'units': units,
                'error': str(e),
            }
        )
        raise