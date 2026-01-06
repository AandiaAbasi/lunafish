"""
Classroom URLs

Router setup برای API ViewSet‌ها
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# ایجاد router برای ViewSet‌ها
router = DefaultRouter()
router.register(r'packages', views.PackageViewSet, basename='package')
router.register(r'enrollments', views.StudentPackageEnrollmentViewSet, basename='enrollment')
router.register(r'payments', views.StudentPackagePaymentViewSet, basename='payment')

# URL patterns
app_name = 'classroom'

urlpatterns = [
    path('', include(router.urls)),
]

