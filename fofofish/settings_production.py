"""
Production settings for fofofish.app
Imports base settings and overrides for Docker deployment.
"""
from .settings import *  # noqa
import os

DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', os.environ.get('DJANGO_SECRET_KEY', 'fallback-change-me'))
ALLOWED_HOSTS = ['fofofish.app', 'www.fofofish.app', 'django', 'localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = ['https://fofofish.app', 'https://www.fofofish.app']

# Database — PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.environ.get('DB_NAME', 'fofofish'),
        'USER': os.environ.get('DB_USER', 'fofofish'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'postgres'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Static files
STATIC_ROOT = '/app/staticfiles'

# Media files
MEDIA_ROOT = '/app/mediafiles'

# Centrifugo
CENTRIFUGO_API_URL = os.environ.get('CENTRIFUGO_API_URL', 'http://centrifugo:8000/api')
CENTRIFUGO_API_KEY = os.environ.get('CENTRIFUGO_API_KEY', '')
CENTRIFUGO_TOKEN_SECRET = os.environ.get('CENTRIFUGO_TOKEN_SECRET', '')
CENTRIFUGO_WS_URL = os.environ.get('CENTRIFUGO_WS_URL', 'wss://fofofish.app/realtime/connection/websocket')

# RTC
RTC_JWT_SECRET = os.environ.get('RTC_JWT_SECRET', '')
RTC_WS_URL = os.environ.get('RTC_WS_URL', 'wss://fofofish.app/rtc/ws')

# Redis cache (optional — falls back if Redis unavailable)
_redis_password = os.environ.get('REDIS_PASSWORD', '')
_redis_url = f"redis://:{_redis_password}@redis:6379/0" if _redis_password else "redis://redis:6379/0"
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', _redis_url),
    }
}

# Security
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Logging — send errors to stdout so Docker logs capture them
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
