from django.conf import settings
from django.core.mail import send_mail
from procrastinate.contrib.django import app


@app.task
def send_email_async(
    subject: str,
    message: str,
    from_email: str | None,
    recipient_list: list[str],
) -> None:
    """
    Send an email asynchronously using the task queue.

    Args:
        subject: Email subject line
        message: Email message body
        from_email: Sender email address (None uses default)
        recipient_list: List of recipient email addresses
    """

    send_mail(
        subject,
        message,
        from_email,
        recipient_list,
        fail_silently=settings.EMAIL_FAIL_SILENTLY,
    )
