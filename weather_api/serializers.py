from rest_framework import serializers
from .models import Location, WeatherData, WeatherQuery


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["city", "country_code", "latitude", "longitude"]

class WeatherDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherData
        fields = [
            "temperature",
            "feels_like",
            "pressure",
            "humidity",
            "wind_speed",
            "wind_direction",
            "visibility",
            "main_weather",
            "description",
            "icon",
        ]

class WeatherQuerySerializer(serializers.ModelSerializer):
    location = LocationSerializer()
    weather_data = WeatherDataSerializer()

    class Meta:
        model = WeatherQuery
        fields = [
            "id",
            "timestamp",
            "units",
            "served_from_cache",
            "ip_address",
            "raw_response",
            "location",
            "weather_data",
        ]

class WeatherQueryCreateSerializer(serializers.Serializer):
    """
    Для POST-запроса: пользователь вводит только city и units.
    WeatherData и Location создаются автоматически.
    """
    city: str = serializers.CharField(max_length=100)
    units: str = serializers.ChoiceField(choices=["C", "F"], default="C")

    def validate_city(self, value):
        return value.strip().lower()  # нормализуем
