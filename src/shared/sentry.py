import logging
import traceback

from django.conf import settings


def report_errors(err: Exception, app_name: str = __name__) -> None:
    logger = logging.getLogger(app_name)

    if settings.SENTRY_DSN:  # type: ignore[misc]
        from sentry_sdk import capture_exception  # noqa: PLC0415

        capture_exception(err)

    logger.error(traceback.format_exc())
