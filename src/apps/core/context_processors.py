from django.conf import settings
from django.http import HttpRequest


def context_settings(request: HttpRequest):
    return {
        "PROJECT_NAME": settings.PROJECT_NAME,
        "DEPLOYMENT_ENV": settings.DEPLOYMENT_ENV,
    }
