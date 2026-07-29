from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LunaGameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'luna_game'
    verbose_name = _('بازی با لونا')
