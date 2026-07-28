from django.db import models
from django.utils.translation import gettext_lazy as _


class EnglishLevel(models.TextChoices):
    PRE_A1 = 'pre_a1', _('Pre-A1')
    A1 = 'a1', _('A1 - Beginner')
    A2 = 'a2', _('A2 - Elementary')
    B1 = 'b1', _('B1 - Intermediate')
    B2 = 'b2', _('B2 - Upper Intermediate')
    C1 = 'c1', _('C1 - Advanced')
    C2 = 'c2', _('C2 - Proficient')
