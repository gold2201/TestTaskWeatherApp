from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch

from ..models import Location, WeatherData, WeatherQuery


class ViewTests(APITestCase):
    def setUp(self):
        self.location = Location.objects.create(city="Paris", country_code="FR")
        self.weather_data = WeatherData.objects.create(
            temperature=22.0,
            main_weather="Clear",
            description="clear sky"
        )

        for i in range(15):
            WeatherQuery.objects.create(
                location=self.location,
                weather_data=self.weather_data,
                units='C',
                ip_address=f'127.0.0.{i}'
            )

    def test_health_check(self):
        url = reverse('health-check')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')
        self.assertEqual(response.data['components']['database'], 'healthy')

    @patch('weather_api.views.get_weather_for_city')
    def test_weather_query_create_success(self, mock_get_weather):
        mock_query = WeatherQuery(
            id=1,
            location=self.location,
            weather_data=self.weather_data,
            units='C',
            served_from_cache=False
        )
        mock_get_weather.return_value = mock_query

        url = reverse('weatherquery-list')
        data = {'city': 'Paris', 'units': 'C'}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        mock_get_weather.assert_called_once()

        call_args = mock_get_weather.call_args
        self.assertEqual(call_args.kwargs['city_name'], 'paris')
        self.assertEqual(call_args.kwargs['units'], 'C')
        self.assertEqual(call_args.kwargs['ip_address'], '127.0.0.1')

    @patch('weather_api.views.get_weather_for_city')
    def test_weather_query_city_not_found(self, mock_get_weather):
        mock_get_weather.side_effect = ValueError("City not found")

        url = reverse('weatherquery-list')
        data = {'city': 'NonexistentCity', 'units': 'C'}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('City not found', response.data['error'])

    def test_weather_query_list_pagination(self):
        url = reverse('weatherquery-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(len(response.data['results']), 10)  # Default page size
        self.assertEqual(response.data['count'], 15)  # Total count

    def test_weather_query_list_filter_by_city(self):
        url = reverse('weatherquery-list') + '?city=Paris'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data['results']:
            self.assertEqual(item['city'], 'Paris')

    def test_weather_query_list_filter_by_date(self):
        url = reverse('weatherquery-list') + '?date_from=2025-01-01&date_to=2025-12-31'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)

    def test_export_csv(self):
        url = reverse('weatherquery-export-csv')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])

        content = response.content.decode('utf-8')
        self.assertIn('City,Country,Temperature', content)
        self.assertIn('Paris,FR,22.0', content)

    def test_export_csv_with_filters(self):
        url = reverse('weatherquery-export-csv') + '?city=Paris'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = response.content.decode('utf-8')
        paris_count = content.count('Paris,FR')
        self.assertEqual(paris_count, 15)