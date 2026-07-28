from django.urls import include, path

urlpatterns = [
    path("", include("recommendation.urls.test_urls")),
]