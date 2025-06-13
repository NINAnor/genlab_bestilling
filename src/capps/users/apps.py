from typing import Self

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "capps.users"
    verbose_name = _("Users")

    def ready(self: Self) -> None:
        try:
            import capps.users.signals  # noqa: F401
        except ImportError:
            pass
