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


class WeatherQueryListSerializer(serializers.ModelSerializer):
    city = serializers.CharField(source='location.city')
    country_code = serializers.CharField(source='location.country_code')
    temperature = serializers.FloatField(source='weather_data.temperature')
    main_weather = serializers.CharField(source='weather_data.main_weather')
    description = serializers.CharField(source='weather_data.description')

    class Meta:
        model = WeatherQuery
        fields = [
            "id",
            "city",
            "country_code",
            "temperature",
            "main_weather",
            "description",
            "timestamp",
            "units",
            "served_from_cache",
        ]


class WeatherQueryCreateSerializer(serializers.Serializer):
    city = serializers.CharField(max_length=100)
    units = serializers.ChoiceField(choices=["C", "F"], default="C")

    def validate_city(self, value):
        return value.strip().lower()
