import csv
import logging
from datetime import datetime

from django.http import HttpResponse
from django.db import connection
from django.views.generic import TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from .models import WeatherQuery
from .serializers import (
    WeatherQuerySerializer,
    WeatherQueryCreateSerializer,
    WeatherQueryListSerializer
)
from .services.cash_service import get_weather_for_city
from .services.rate_limiter import RateLimitExceeded

logger = logging.getLogger("weather")

class StandardResultsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class WeatherQueryFilter(viewsets.GenericViewSet):
    def get_queryset(self):
        queryset = WeatherQuery.objects.select_related(
            'location', 'weather_data'
        ).order_by('-timestamp')

        city = self.request.query_params.get('city', None)
        if city:
            queryset = queryset.filter(location__city__icontains=city)

        date_from = self.request.query_params.get('date_from', None)
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__gte=date_from)
            except ValueError:
                pass

        date_to = self.request.query_params.get('date_to', None)
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__lte=date_to)
            except ValueError:
                pass

        return queryset

# Core weather query processing with structured logging and error handling
class WeatherQueryViewSet(WeatherQueryFilter, viewsets.ModelViewSet):
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend]

    def get_serializer_class(self):
        if self.action == 'create':
            return WeatherQueryCreateSerializer
        elif self.action == 'list':
            return WeatherQueryListSerializer
        return WeatherQuerySerializer

    def create(self, request):
        """
        Main weather data endpoint with comprehensive logging and error handling.
        Implements: request validation -> rate limiting -> caching -> external API call -> response
        """
        serializer = WeatherQueryCreateSerializer(data=request.data)
        if serializer.is_valid():
            city = serializer.validated_data['city']
            units = serializer.validated_data['units']
            ip_address = self.get_client_ip()

            logger.info(
                "Weather request started",
                extra={
                    'ip': ip_address,
                    'user': 'anonymous',
                    'event': 'weather_request_start',
                    'city': city,
                    'units': units,
                }
            )

            try:
                start_time = datetime.now()
                # Main service call - handles caching and external API
                weather_query = get_weather_for_city(
                    city_name=city,
                    units=units,
                    ip_address=ip_address
                )

                api_latency = (datetime.now() - start_time).total_seconds()

                logger.info(
                    "Weather request completed successfully",
                    extra={
                        'ip': ip_address,
                        'user': 'anonymous',
                        'event': 'weather_request_success',
                        'city': city,
                        'units': units,
                        'served_from_cache': str(weather_query.served_from_cache),
                        'latency': f"{api_latency:.3f}",
                    }
                )

                response_serializer = WeatherQuerySerializer(weather_query)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)

            except RateLimitExceeded as e:
                logger.warning(
                    "Rate limit exceeded",
                    extra={
                        'ip': ip_address,
                        'user': 'anonymous',
                        'event': 'rate_limit_exceeded',
                        'city': city,
                        'units': units,
                        'error': str(e),
                    }
                )
                return Response(
                    {"error": "Rate limit exceeded", "message": "Please try again in a minute.", "detail": str(e)},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            except ValueError as e:
                logger.error(
                    "City not found error",
                    extra={
                        'ip': ip_address,
                        'user': 'anonymous',
                        'event': 'city_not_found',
                        'city': city,
                        'units': units,
                        'error': str(e),
                    }
                )
                return Response(
                    {"error": "City not found", "detail": str(e)},
                    status=status.HTTP_404_NOT_FOUND
                )

            except Exception as e:
                logger.error(
                    "Internal server error during weather request",
                    extra={
                        'ip': ip_address,
                        'user': 'anonymous',
                        'event': 'internal_server_error',
                        'city': city,
                        'units': units,
                        'error': str(e),
                    }
                )
                return Response(
                    {"error": "Internal server error", "detail": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        logger.warning(
            "Validation error in weather request",
            extra={
                'ip': self.get_client_ip(),
                'user': 'anonymous',
                'event': 'validation_error',
                'error': str(serializer.errors),
            }
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        queryset = self.get_queryset().select_related('location', 'weather_data')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="weather_history.csv"'

        writer = csv.writer(response)
        writer.writerow(
            ['City', 'Country', 'Temperature', 'Feels Like', 'Weather', 'Description', 'Query Timestamp', 'Units',
             'Served From Cache'])

        for query in queryset:
            writer.writerow([
                query.location.city,
                query.location.country_code,
                query.weather_data.temperature if query.weather_data else 'N/A',
                query.weather_data.feels_like if query.weather_data else 'N/A',
                query.weather_data.main_weather if query.weather_data else 'N/A',
                query.weather_data.description if query.weather_data else 'N/A',
                query.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                query.units,
                'Yes' if query.served_from_cache else 'No'
            ])

        return response

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class HealthCheckView(APIView):
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        api_status = "not_checked"
        try:
            import requests
            from django.conf import settings

            if settings.OPENWEATHER_API_KEY:
                test_response = requests.get(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={
                        "q": "London",
                        "appid": settings.OPENWEATHER_API_KEY,
                        "units": "metric"
                    },
                    timeout=3
                )

                if test_response.status_code == 200:
                    api_status = "healthy"
                elif test_response.status_code == 401:
                    api_status = "unhealthy: invalid API key"
                else:
                    api_status = f"unhealthy: HTTP {test_response.status_code}"
            else:
                api_status = "unhealthy: API key not configured"

        except requests.exceptions.Timeout:
            api_status = "unhealthy: timeout"
        except requests.exceptions.ConnectionError:
            api_status = "unhealthy: connection failed"
        except Exception as e:
            api_status = f"unhealthy: {str(e)}"

        health_data = {
            "status": "healthy" if db_status == "healthy" and api_status == "healthy" else "degraded",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": db_status,
                "external_api": api_status
            }
        }

        status_code = status.HTTP_200_OK if health_data["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

        return Response(health_data, status=status_code)


class WeatherFormView(TemplateView):
    template_name = 'weather/weather_form.html'

class WeatherHistoryView(TemplateView):
    template_name = 'weather/weather_history.html'


class WeatherDataAPIView(APIView):
    def post(self, request):
        serializer = WeatherQueryCreateSerializer(data=request.data)
        if serializer.is_valid():
            city = serializer.validated_data['city']
            units = serializer.validated_data['units']
            ip_address = self.get_client_ip(request)
            try:
                weather_query = get_weather_for_city(
                    city_name=city,
                    units=units,
                    ip_address=ip_address
                )

                response_serializer = WeatherQuerySerializer(weather_query)
                return Response(response_serializer.data)

            except RateLimitExceeded:
                return Response(
                    {"error": "Rate limit exceeded. Please try again later."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            except ValueError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip