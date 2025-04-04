from typing import Self

from django.apps import AppConfig as DjangoAppConfig
from django.utils.translation import gettext_lazy as _


class AppConfig(DjangoAppConfig):
    name = "genlab_bestilling.staff"
    verbose_name = _("GenLab staff")

    def ready(self: Self) -> None:
        try:
            import genlab_bestilling.signals  # noqa: F401
        except ImportError:
            pass
