from datetime import timedelta
from django.utils import timezone
from ..models  import WeatherQuery, Location, WeatherData
from .weather_api_service import OpenWeatherAPI
from .rate_limiter import check_rate_limit, RateLimitExceeded
from django.db import transaction

CACHE_TTL = timedelta(minutes=5)

def get_weather_for_city(city_name: str, units: str = "C", ip_address: str = None) -> WeatherQuery:
    check_rate_limit(ip_address)

    now = timezone.now()

    last_query = WeatherQuery.objects.filter(
        location__city__iexact=city_name.strip(),
        units=units,
        timestamp__gte=now - CACHE_TTL
    ).order_by('-timestamp').first()

    if last_query:
        new_query = WeatherQuery.objects.create(
            location=last_query.location,
            weather_data=last_query.weather_data,
            units=units,
            ip_address=ip_address,
            served_from_cache=True,
            raw_response=last_query.raw_response,
        )
        return new_query

    raw_data = OpenWeatherAPI.fetch_weather(city_name, units)
    location_data = OpenWeatherAPI.normalize_location_data(raw_data)
    weather_data_dict = OpenWeatherAPI.normalize_weather_data(raw_data)

    with transaction.atomic():
        location, _ = Location.objects.get_or_create(
            city=location_data["city"],
            country_code=location_data.get("country_code"),
            defaults=location_data
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

    return new_query
