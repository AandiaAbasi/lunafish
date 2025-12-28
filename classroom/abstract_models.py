from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """Base model inherited by all models"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")

    class Meta:
        abstract = True
