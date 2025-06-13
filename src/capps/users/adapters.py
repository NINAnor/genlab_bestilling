import logging
import traceback
from typing import Self

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.http import HttpRequest


def report(e, error):
    logging.error(str(e))  # noqa: LOG015
    logging.error(str(error))  # noqa: LOG015
    try:
        from sentry_sdk import capture_exception, set_context

        set_context("oauth error", {"error": str(error)})
        capture_exception(e)
    except Exception:
        logging.error(traceback.format_exc())  # noqa: LOG015


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self: Self, request: HttpRequest) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    just for debugging obscure integration exceptions
    """

    def on_authentication_error(
        self: Self, request, provider, error=None, exception=None, extra_context=None
    ):
        report(exception, error)
        return super().on_authentication_error(
            request,
            provider,
            error=error,
            exception=exception,
            extra_context=extra_context,
        )
