from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ExerciseConfig(AppConfig):
    name = 'exercise'
    verbose_name = _("مدیریت تمرینات و کوییز ها")
