"""
Production settings for fofofish.app
Imports base settings and overrides for Docker deployment.
"""
from .settings import *  # noqa
import os

DEBUG = False
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
ALLOWED_HOSTS = ['fofofish.app', 'www.fofofish.app']
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

# Centrifugo
CENTRIFUGO_API_URL = os.environ.get('CENTRIFUGO_API_URL', 'http://centrifugo:8000/api')
CENTRIFUGO_API_KEY = os.environ.get('CENTRIFUGO_API_KEY', '')
CENTRIFUGO_TOKEN_SECRET = os.environ.get('CENTRIFUGO_TOKEN_SECRET', '')
CENTRIFUGO_WS_URL = os.environ.get('CENTRIFUGO_WS_URL', 'wss://fofofish.app/realtime/connection/websocket')

# RTC
RTC_JWT_SECRET = os.environ.get('RTC_JWT_SECRET', '')
RTC_WS_URL = os.environ.get('RTC_WS_URL', 'wss://fofofish.app/rtc/ws')

# Redis cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/0'),
    }
}

# Security
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True