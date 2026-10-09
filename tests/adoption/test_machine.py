"""The same state machine, three systems under test: the aggregate alone, the use cases over the
in-memory repository, and the use cases over the Django repository on the real database."""

import pytest
from django.db import transaction
from hypothesis import HealthCheck, settings
from hypothesis.stateful import run_state_machine_as_test  # pyright: ignore[reportUnknownVariableType]

from tests.conftest import make_pet, make_user
from tests.fakes import InMemoryAdoptionProcesses, uuid

from .machine import ACCOUNTS, AdoptionMachine, AggregateDriver, Driver, UseCaseDriver


class AggregateMachine(AdoptionMachine):
    def make_driver(self) -> Driver:
        return AggregateDriver()


class InMemoryMachine(AdoptionMachine):
    def make_driver(self) -> Driver:
        processes = InMemoryAdoptionProcesses()
        processes.add_pet(uuid(1), owner_id=1000)
        return UseCaseDriver(processes, uuid(1), [1000, 1001, 1002, 1003, 1004])


class DjangoMachine(AdoptionMachine):
    """Each run lives in a transaction that is rolled back at teardown, so runs never see each other."""

    def make_driver(self) -> Driver:
        from adote.adoption.adapters.repository import DjangoAdoptionProcesses  # noqa: PLC0415 - needs the DB

        self.atomic = transaction.atomic()
        self.atomic.__enter__()
        users = [make_user() for _ in ACCOUNTS]
        pet_id = make_pet(users[0])
        return UseCaseDriver(DjangoAdoptionProcesses(), pet_id, [user.pk for user in users])

    def teardown(self) -> None:
        transaction.set_rollback(True)
        self.atomic.__exit__(None, None, None)


AggregateTest = AggregateMachine.TestCase  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
AggregateTest.settings = settings(max_examples=300, stateful_step_count=30, deadline=None)

InMemoryTest = InMemoryMachine.TestCase  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
InMemoryTest.settings = settings(max_examples=150, stateful_step_count=25, deadline=None)


@pytest.mark.django_db
def test_django_repository_follows_the_model() -> None:
    run_state_machine_as_test(
        DjangoMachine,
        settings=settings(
            max_examples=40,
            stateful_step_count=15,
            deadline=None,
            suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
        ),
    )
