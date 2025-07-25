import contextlib
from typing import Self

from django.apps import AppConfig as DjangoAppConfig
from django.utils.translation import gettext_lazy as _


class AppConfig(DjangoAppConfig):
    name = "genlab_bestilling"
    verbose_name = _("GenLab")

    def ready(self: Self) -> None:
        with contextlib.suppress(ImportError):
            import genlab_bestilling.signals  # noqa: F401, PLC0415
