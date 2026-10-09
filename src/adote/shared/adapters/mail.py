"""`Mailer` over Django's mailers, as a background task (Django 6 Tasks framework).

The immediate backend runs the task inside the request; a worker backend in TASKS would move every
e-mail out of it with no change here or in the domain.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

from adote.shared.adapters.compat import task

logger = logging.getLogger(__name__)


@task
def send_email(*, to: str, subject: str, body: str) -> None:
    """Never raises: a message that could not go out is logged, and the action that caused it stands."""
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to])
    except Exception:
        logger.exception("could not send %r to an account", subject)


class DjangoMailer:
    def send(self, *, to: str, subject: str, body: str) -> None:
        send_email.enqueue(to=to, subject=subject, body=body)
