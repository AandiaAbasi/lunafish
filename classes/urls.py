from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .guest_views import GuestClassCreateAPIView, GuestClassJoinAPIView
from .views import OnlineClassViewSet


app_name = 'classes'

router = DefaultRouter()
router.register(r'', OnlineClassViewSet, basename='class')

urlpatterns = [
    path('guest/create/', GuestClassCreateAPIView.as_view(), name='guest-class-create'),
    path('guest/join/', GuestClassJoinAPIView.as_view(), name='guest-class-join'),
    path('', include(router.urls)),
]

