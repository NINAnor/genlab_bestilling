from typing import Any

from django.conf import settings
from django.http import HttpRequest


def context_settings(request: HttpRequest) -> dict[str, Any]:
    return {
        "PROJECT_NAME": settings.PROJECT_NAME,
        "DEPLOYMENT_ENV": settings.DEPLOYMENT_ENV,
    }
