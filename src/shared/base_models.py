from django.db import models

from .mixins import CleanSaveMixin


class CustomModel(CleanSaveMixin, models.Model):
    """Base model that all models should inherit from by default."""

    class Meta:
        abstract = True
