"""`Mailer` over Django's e-mail backend: SMTP in production, the console in development, memory in tests."""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class DjangoMailer:
    def send(self, *, to: str, subject: str, body: str) -> None:
        """Never raises: a message that could not go out is logged, and the action that caused it stands."""
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to])
        except Exception:
            logger.exception("could not send %r to an account", subject)
