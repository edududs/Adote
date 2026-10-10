import importlib
import io
import os
from collections.abc import Callable, Generator
from contextlib import contextmanager
from uuid import UUID

import pytest
from django.db import transaction
from django.test import Client
from hypothesis import HealthCheck, settings
from PIL import Image

from adote.accounts.adapters.models import User
from adote.pets.adapters.composition import publish_pet
from adote.pets.adapters.models import Breed, Tag
from adote.pets.application import Photo
from adote.pets.domain import PetDetails, Sex, Species
from adote.shared.domain import PhoneNumber, State

# Domain properties are cheap: many examples. Database ones are slower: fewer, no deadline.
settings.register_profile("default", max_examples=100, deadline=None)
settings.register_profile("ci", max_examples=300, deadline=None)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "default"))
DB = settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)

PASSWORD = "uma-senha-bem-longa-123"


def pytest_report_header() -> str:
    from django.db import connection  # noqa: PLC0415

    return f"database: {connection.vendor}"


@contextmanager
def rolled_back() -> Generator[None]:
    """Run one Hypothesis example inside a transaction that is always rolled back.

    pytest-django isolates a test, not each example Hypothesis runs inside it.
    """
    with transaction.atomic():
        yield
        transaction.set_rollback(True)


def png_bytes(size: tuple[int, int] = (8, 8), image_format: str = "PNG") -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (200, 120, 80)).save(buffer, format=image_format)
    return buffer.getvalue()


_counter = iter(range(10**9))


def make_user(username: str | None = None, **fields: str) -> User:
    n = next(_counter)
    username = username or f"user{n}"
    defaults = {
        "email": f"{username}@example.com",
        "first_name": username.title(),
        "phone": f"6199{n:07d}",
        "state": State.DF.value,
        "city": "Brasília",
        "about": "Gosto de bichos.",
    }
    return User.objects.create_user(username=username, password=PASSWORD, **(defaults | fields))


def make_pet(owner: User, *, name: str = "Thor", breed: str = "Beagle", **changes: object) -> UUID:
    details = PetDetails(
        name=name,
        species=Species.DOG,
        sex=Sex.MALE,
        breed_id=Breed.objects.get(species="dog", name=breed).pk,
        tag_ids=frozenset(),
        description="Um amor de cachorro.",
        city="Brasília",
        state=State.DF,
        contact_phone=PhoneNumber.parse("(61) 99999-0000"),
    ).evolve(**changes)
    return publish_pet()(owner.pk, details, Photo(filename="photo.png", content=png_bytes())).id


@pytest.fixture(autouse=True)
def _seeded_catalog(request: pytest.FixtureRequest) -> None:
    """Breeds and tags come from a data migration. A transactional test (the browser tests) ends by
    flushing every table, so any database test that follows puts the catalog back first."""
    if "django_db" not in request.keywords and "db" not in request.fixturenames:
        return
    from django.apps import apps  # noqa: PLC0415

    blocker = request.getfixturevalue("django_db_blocker")
    with blocker.unblock():
        if not Breed.objects.exists():
            importlib.import_module("adote.pets.adapters.migrations.0002_seed_catalog").seed(apps, None)


@pytest.fixture
def user_factory(db: None) -> Callable[..., User]:
    return make_user


@pytest.fixture
def pet_factory(db: None) -> Callable[..., UUID]:
    return make_pet


def signed_in(user: User) -> Client:
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def tag_ids(db: None) -> list[int]:
    return list(Tag.objects.values_list("pk", flat=True))
