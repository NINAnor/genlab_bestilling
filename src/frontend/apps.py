from django.apps import AppConfig as DjangoAppConfig
from django.utils.translation import gettext_lazy as _


class FrontendConfig(DjangoAppConfig):
    name = "frontend"
    verbose_name = _("Frontend")
