import contextlib
from typing import Self

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "capps.users"
    verbose_name = _("Users")

    def ready(self: Self) -> None:
        # Ensure that the signals are imported when the app is ready
        # This is necessary to ensure that the signals are connected.
        with contextlib.suppress(ImportError):
            import capps.users.signals  # noqa: F401, PLC0415
