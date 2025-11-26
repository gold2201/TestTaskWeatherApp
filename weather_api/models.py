from django.db import models
from django.utils import timezone


class Location(models.Model):
    city = models.CharField(max_length=100, db_index=True)
    country_code = models.CharField(max_length=2, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'locations'
        constraints = [
            models.UniqueConstraint(
                fields=['city', 'country_code'],
                name='unique_city_country'
            )
        ]

    def __str__(self):
        return f"{self.city}, {self.country_code}".strip(", ")


class WeatherData(models.Model):
    temperature = models.FloatField()
    feels_like = models.FloatField(null=True, blank=True)
    pressure = models.IntegerField(null=True, blank=True)
    humidity = models.IntegerField(null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)
    wind_direction = models.IntegerField(null=True, blank=True)
    visibility = models.IntegerField(null=True, blank=True)

    main_weather = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    icon = models.CharField(max_length=10, blank=True)

    class Meta:
        db_table = 'weather_data'

    def __str__(self):
        return f"{self.temperature}° — {self.description}"


class WeatherQuery(models.Model):
    UNIT_CHOICES = [
        ('C', 'Celsius'),
        ('F', 'Fahrenheit'),
    ]

    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    weather_data = models.ForeignKey(
        WeatherData,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    units = models.CharField(max_length=1, choices=UNIT_CHOICES, default='C')
    served_from_cache = models.BooleanField(default=False)

    raw_response = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'weather_queries'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['location', 'timestamp']),
            models.Index(fields=['timestamp', 'served_from_cache']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.location.city} @ {self.timestamp:%Y-%m-%d %H:%M}"
