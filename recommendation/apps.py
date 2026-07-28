from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RecommendationConfig(AppConfig):
    name = 'recommendation'
    verbose_name = _("Psychological test")