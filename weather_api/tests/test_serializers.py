from django.test import TestCase
from ..serializers import WeatherQueryCreateSerializer


class SerializerTests(TestCase):
    def test_weather_query_create_serializer_valid(self):
        data = {'city': ' London ', 'units': 'C'}
        serializer = WeatherQueryCreateSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['city'], 'london')  # Normalized
        self.assertEqual(serializer.validated_data['units'], 'C')

    def test_weather_query_create_serializer_invalid_city(self):
        data = {'city': '', 'units': 'C'}
        serializer = WeatherQueryCreateSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('city', serializer.errors)

    def test_weather_query_create_serializer_invalid_units(self):
        data = {'city': 'London', 'units': 'K'}
        serializer = WeatherQueryCreateSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('units', serializer.errors)

    def test_city_normalization(self):
        test_cases = [
            ('  London  ', 'london'),
            ('New York', 'new york'),
            ('PARIS', 'paris'),
            ('  San Francisco  ', 'san francisco')
        ]

        for input_city, expected_city in test_cases:
            data = {'city': input_city, 'units': 'C'}
            serializer = WeatherQueryCreateSerializer(data=data)
            self.assertTrue(serializer.is_valid())
            self.assertEqual(serializer.validated_data['city'], expected_city)