from django.test import TestCase
from django.utils import timezone
from ..models import Location, WeatherData, WeatherQuery


class ModelTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(
            city="London",
            country_code="GB",
            latitude=51.5074,
            longitude=-0.1278
        )

        self.weather_data = WeatherData.objects.create(
            temperature=15.5,
            feels_like=14.0,
            pressure=1013,
            humidity=65,
            wind_speed=3.5,
            wind_direction=180,
            visibility=10000,
            main_weather="Clouds",
            description="overcast clouds",
            icon="04d"
        )

        self.weather_query = WeatherQuery.objects.create(
            location=self.location,
            weather_data=self.weather_data,
            units='C',
            ip_address='127.0.0.1'
        )

    def test_location_creation(self):
        self.assertEqual(str(self.location), "London, GB")
        self.assertEqual(self.location.city, "London")
        self.assertEqual(self.location.country_code, "GB")

    def test_weather_data_creation(self):
        self.assertEqual(str(self.weather_data), "15.5° — overcast clouds")
        self.assertEqual(self.weather_data.temperature, 15.5)
        self.assertEqual(self.weather_data.main_weather, "Clouds")

    def test_weather_query_creation(self):
        self.assertIn("London @", str(self.weather_query))
        self.assertEqual(self.weather_query.units, 'C')
        self.assertFalse(self.weather_query.served_from_cache)

    def test_location_unique_constraint(self):
        with self.assertRaises(Exception):
            Location.objects.create(
                city="London",
                country_code="GB",
                latitude=51.5074,
                longitude=-0.1278
            )

    def test_weather_query_ordering(self):
        WeatherQuery.objects.create(
            location=self.location,
            weather_data=self.weather_data,
            units='F',
            ip_address='127.0.0.2'
        )

        queries = WeatherQuery.objects.all()
        self.assertEqual(queries.count(), 2)
        self.assertGreater(queries[0].timestamp, queries[1].timestamp)