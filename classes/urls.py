from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import OnlineClassViewSet, InternalRTCEventAPIView


app_name = 'classes'

router = DefaultRouter()
router.register(r'', OnlineClassViewSet, basename='class')

urlpatterns = [
    path('', include(router.urls)),
    # Internal RTC events endpoint for mediasoup callbacks
    path('internal/rtc-events/', InternalRTCEventAPIView.as_view(), name='internal_rtc_events'),
]

