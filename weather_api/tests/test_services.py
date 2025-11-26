from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from django.core.cache import cache

from ..models import Location, WeatherData, WeatherQuery
from ..services.cash_service import get_weather_for_city
from ..services.rate_limiter import check_rate_limit, RateLimitExceeded


class ServiceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.mock_weather_data = {
            'main': {
                'temp': 20.5,
                'feels_like': 19.0,
                'pressure': 1015,
                'humidity': 70
            },
            'wind': {
                'speed': 4.2,
                'deg': 180
            },
            'visibility': 10000,
            'weather': [{
                'main': 'Clouds',
                'description': 'scattered clouds',
                'icon': '03d'
            }],
            'name': 'London',
            'sys': {'country': 'GB'},
            'coord': {'lat': 51.5074, 'lon': -0.1278}
        }

    def tearDown(self):
        cache.clear()

    @patch('weather_api.services.cash_service.OpenWeatherAPI.fetch_weather')
    def test_get_weather_for_city_fresh_fetch(self, mock_fetch):
        mock_fetch.return_value = self.mock_weather_data

        query = get_weather_for_city('london', 'C', '127.0.0.1')

        self.assertFalse(query.served_from_cache)
        self.assertEqual(query.location.city, 'london')
        self.assertEqual(query.weather_data.temperature, 20.5)
        self.assertEqual(query.units, 'C')

        mock_fetch.assert_called_once_with('london', 'C')

    @patch('weather_api.services.cash_service.OpenWeatherAPI.fetch_weather')
    def test_cache_reuse_same_city_same_units(self, mock_fetch):
        mock_fetch.return_value = self.mock_weather_data

        query1 = get_weather_for_city('London', 'C', '127.0.0.1')
        self.assertFalse(query1.served_from_cache)

        query2 = get_weather_for_city('London', 'C', '127.0.0.1')
        self.assertTrue(query2.served_from_cache)

        self.assertEqual(mock_fetch.call_count, 1)

    @patch('weather_api.services.cash_service.OpenWeatherAPI.fetch_weather')
    def test_no_cache_reuse_different_units(self, mock_fetch):
        mock_fetch.return_value = self.mock_weather_data

        query1 = get_weather_for_city('London', 'C', '127.0.0.1')
        self.assertFalse(query1.served_from_cache)

        query2 = get_weather_for_city('London', 'F', '127.0.0.1')
        self.assertFalse(query2.served_from_cache)

        self.assertEqual(mock_fetch.call_count, 2)

    def test_rate_limit_normal_usage(self):
        ip = '127.0.0.1'

        for i in range(29):
            try:
                check_rate_limit(ip)
            except RateLimitExceeded:
                self.fail(f"Rate limit exceeded at request {i + 1}")

    def test_rate_limit_exceeded(self):
        ip = '127.0.0.1'

        for i in range(30):
            check_rate_limit(ip)

        with self.assertRaises(RateLimitExceeded) as context:
            check_rate_limit(ip)

        self.assertIn("Rate limit exceeded", str(context.exception))

    def test_rate_limit_different_ips(self):
        ip1 = '127.0.0.1'
        ip2 = '192.168.1.1'

        for i in range(30):
            check_rate_limit(ip1)

        with self.assertRaises(RateLimitExceeded):
            check_rate_limit(ip1)

        try:
            check_rate_limit(ip2)
        except RateLimitExceeded:
            self.fail("Rate limit should not affect different IP")

    def test_rate_limit_no_ip(self):
        with self.assertRaises(RateLimitExceeded) as context:
            check_rate_limit(None)

        self.assertIn("IP address missing", str(context.exception))

    @patch('weather_api.services.cash_service.OpenWeatherAPI.fetch_weather')
    def test_rate_limit_prevents_db_writes(self, mock_fetch):
        mock_fetch.return_value = self.mock_weather_data
        ip = '127.0.0.1'

        initial_count = WeatherQuery.objects.count()

        for i in range(30):
            check_rate_limit(ip)

        with self.assertRaises(RateLimitExceeded):
            get_weather_for_city('London', 'C', ip)

        final_count = WeatherQuery.objects.count()
        self.assertEqual(final_count, initial_count)

        mock_fetch.assert_not_called()