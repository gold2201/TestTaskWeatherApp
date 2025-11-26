from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'weather/queries', views.WeatherQueryViewSet, basename='weatherquery')

urlpatterns = [
    # API Routes
    path('api/', include(router.urls)),
    path('api/health/', views.HealthCheckView.as_view(), name='health-check'),

    # Web Interface Routes
    path('', views.WeatherFormView.as_view(), name='weather-form'),
    path('history/', views.WeatherHistoryView.as_view(), name='weather-history'),
    path('api/weather/data/', views.WeatherDataAPIView.as_view(), name='weather-data-api'),
]