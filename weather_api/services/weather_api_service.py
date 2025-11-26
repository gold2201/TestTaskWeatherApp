import requests
from django.conf import settings

class OpenWeatherAPI:
    """
    Adapter for OpenWeatherMap API with error handling and data normalization.
    Converts API-specific response format to application domain model.
    """

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    @staticmethod
    def fetch_weather(city: str, units: str = "C") -> dict:
        try:
            units_param = "metric" if units == "C" else "imperial"

            params = {
                "q": city,
                "appid": settings.OPENWEATHER_API_KEY,
                "units": units_param,
                "lang": "en",
            }

            response = requests.get(OpenWeatherAPI.BASE_URL, params=params, timeout=5)

            if response.status_code == 404:
                raise ValueError("City not found")

            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            raise ValueError(f"Weather API error: {str(e)}")

    @staticmethod
    def normalize_weather_data(data: dict) -> dict:

        main = data.get("main", {})
        wind = data.get("wind", {})
        weather = data.get("weather", [{}])[0]

        return {
            "temperature": main.get("temp"),
            "feels_like": main.get("feels_like"),
            "pressure": main.get("pressure"),
            "humidity": main.get("humidity"),
            "wind_speed": wind.get("speed"),
            "wind_direction": wind.get("deg"),
            "visibility": data.get("visibility"),
            "main_weather": weather.get("main"),
            "description": weather.get("description"),
            "icon": weather.get("icon"),
        }

    @staticmethod
    def normalize_location_data(data: dict) -> dict:
        return {
            "city": data.get("name"),
            "country_code": data.get("sys", {}).get("country"),
            "latitude": data.get("coord", {}).get("lat"),
            "longitude": data.get("coord", {}).get("lon"),
        }
