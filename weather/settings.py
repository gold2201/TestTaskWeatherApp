from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", 'django-insecure-fallback-key-for-dev')

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

DEBUG = os.getenv("DEBUG", False).lower()=='true'

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',

    'weather_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'weather.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'weather.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'weather',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "structured": {
            "format": 'timestamp=%(asctime)s level=%(levelname)s module=%(name)s message="%(message)s" ip=%(ip)s user=%(user)s event=%(event)s city=%(city)s units=%(units)s served_from_cache=%(served_from_cache)s latency=%(latency)s error=%(error)s',
            "style": "%",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": """
                {
                    "timestamp": "%(asctime)s",
                    "level": "%(levelname)s",
                    "module": "%(name)s", 
                    "message": "%(message)s",
                    "ip": "%(ip)s",
                    "user": "%(user)s",
                    "event": "%(event)s",
                    "city": "%(city)s",
                    "units": "%(units)s",
                    "served_from_cache": "%(served_from_cache)s",
                    "latency": "%(latency)s",
                    "error": "%(error)s"
                }
            """,
        },
    },

    "filters": {
        "add_extra_fields": {
            "()": "weather_api.logging_filters.ExtraFieldsFilter",
        },
    },

    "handlers": {
        "console_structured": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
            "filters": ["add_extra_fields"],
        },

        "file_structured": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "structured_weather.log",
            "formatter": "structured",
            "filters": ["add_extra_fields"],
        },

        "file_json": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "json_weather.log",
            "formatter": "json",
            "filters": ["add_extra_fields"],
        },

        "errors_structured": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "errors_structured.log",
            "formatter": "structured",
            "level": "ERROR",
            "filters": ["add_extra_fields"],
        },
    },

    "loggers": {
        "django": {
            "handlers": ["console_structured"],
            "level": "INFO",
            "propagate": False,
        },

        "weather": {
            "handlers": ["console_structured", "file_structured", "file_json", "errors_structured"],
            "level": "INFO",
            "propagate": False,
        },

        "django.request": {
            "handlers": ["errors_structured", "console_structured"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

