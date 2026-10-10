"""Wires the adoption use cases to their adapters."""

from django.conf import settings

from adote.adoption.application import ApproveRequest, RejectRequest, RequestAdoption, WithdrawRequest
from adote.shared.adapters.clock import SystemClock
from adote.shared.adapters.mail import DjangoMailer

from .notifier import EmailNotifier
from .repository import DjangoAdoptionProcesses


def _parts() -> tuple[DjangoAdoptionProcesses, EmailNotifier, SystemClock]:
    return DjangoAdoptionProcesses(), EmailNotifier(DjangoMailer(), settings.SITE_URL), SystemClock()


def request_adoption() -> RequestAdoption:
    return RequestAdoption(*_parts())


def approve_request() -> ApproveRequest:
    return ApproveRequest(*_parts())


def reject_request() -> RejectRequest:
    return RejectRequest(*_parts())


def withdraw_request() -> WithdrawRequest:
    return WithdrawRequest(*_parts())
