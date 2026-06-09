from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import OnlineClassViewSet


app_name = 'classes'

router = DefaultRouter()
router.register(r'', OnlineClassViewSet, basename='class')

urlpatterns = [
    path('', include(router.urls)),
]

