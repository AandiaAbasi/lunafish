"""Skyroom App URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ServiceViewSet, RoomViewSet, SkyroomUserViewSet,
    RoomUserAccessViewSet, LoginUrlViewSet
)

app_name = 'skyroom'

router = DefaultRouter()
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'users', SkyroomUserViewSet, basename='skyroom-user')
router.register(r'access', RoomUserAccessViewSet, basename='room-user-access')
router.register(r'login-urls', LoginUrlViewSet, basename='login-url')

urlpatterns = [
    path('', include(router.urls)),
]
