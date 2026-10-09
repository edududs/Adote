import logging
from collections.abc import Callable
from uuid import UUID

import pytest
from django.core import mail
from django.test import override_settings

from adote.accounts.adapters.models import User
from adote.adoption.adapters.composition import (
    approve_request,
    reject_request,
    request_adoption,
    withdraw_request,
)
from adote.adoption.adapters.notifier import EmailNotifier
from adote.adoption.domain import AdoptionRequest, RequestSubmitted
from adote.shared.adapters.mail import DjangoMailer
from tests.fakes import EPOCH, uuid

pytestmark = pytest.mark.django_db


def test_each_change_mails_the_right_person(
    user_factory: Callable[..., User], pet_factory: Callable[..., UUID]
) -> None:
    owner = user_factory("tutor", first_name="Tina")
    ana, bia = user_factory("ana", first_name="Ana"), user_factory("bia", first_name="Bia")
    pet_id = pet_factory(owner, name="Thor")

    first = request_adoption()(pet_id, adopter_id=ana.pk, message="Tenho quintal")
    (submitted,) = mail.outbox
    assert submitted.to == [owner.email]
    assert "Thor" in submitted.subject
    assert "Tenho quintal" in str(submitted.body)
    assert "/pedidos/recebidos/" in str(submitted.body)

    second = request_adoption()(pet_id, adopter_id=bia.pk)
    withdraw_request()(second.id, by=bia.pk)
    assert mail.outbox[-1].to == [owner.email]
    assert "cancelou" in str(mail.outbox[-1].body)

    third = request_adoption()(pet_id, adopter_id=user_factory("caio").pk)
    mail.outbox.clear()
    approve_request()(first.id, by=owner.pk)
    approved, auto_rejected = mail.outbox
    assert approved.to == [ana.email]
    assert "(61) 99999-0000" in str(approved.body)
    assert owner.email in str(approved.body)
    assert "encontrou outro lar" in str(auto_rejected.body)
    assert third.adopter_id != ana.pk


def test_a_manual_refusal_says_so(
    user_factory: Callable[..., User], pet_factory: Callable[..., UUID]
) -> None:
    owner, ana = user_factory(), user_factory()
    request = request_adoption()(pet_factory(owner), adopter_id=ana.pk)
    mail.outbox.clear()
    reject_request()(request.id, by=owner.pk)
    (message,) = mail.outbox
    assert message.to == [ana.email]
    assert "escolheu não seguir" in str(message.body)


def test_events_about_people_or_pets_that_are_gone_send_nothing(db: None) -> None:
    request = AdoptionRequest(id=uuid(1), pet_id=uuid(2), adopter_id=999, requested_at=EPOCH)
    EmailNotifier(DjangoMailer(), "http://x").notify(
        RequestSubmitted(pet_id=uuid(2), owner_id=998, request=request)
    )
    assert mail.outbox == []


def test_a_mail_failure_is_logged_and_never_reaches_the_person(caplog: pytest.LogCaptureFixture) -> None:
    with (
        override_settings(EMAIL_BACKEND="tests.adoption.test_notifier.BrokenBackend"),
        caplog.at_level(logging.ERROR, logger="adote.shared.adapters.mail"),
    ):
        DjangoMailer().send(to="a@example.com", subject="s", body="b")
    assert "could not send" in caplog.text


class BrokenBackend:
    def __init__(self, **kwargs: object) -> None:
        pass

    def send_messages(self, messages: object) -> int:
        msg = "SMTP is down"
        raise ConnectionError(msg)


def test_an_event_without_a_message_sends_nothing(
    user_factory: Callable[..., User], pet_factory: Callable[..., UUID]
) -> None:
    from adote.adoption.domain import AdoptionEvent  # noqa: PLC0415

    owner, adopter = user_factory(), user_factory()
    pet_id = pet_factory(owner)
    request = AdoptionRequest(id=uuid(1), pet_id=pet_id, adopter_id=adopter.pk, requested_at=EPOCH)
    EmailNotifier(DjangoMailer(), "http://x").notify(
        AdoptionEvent(pet_id=pet_id, owner_id=owner.pk, request=request)
    )
    assert mail.outbox == []
