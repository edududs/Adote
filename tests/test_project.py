import importlib
import re
import subprocess
import sys
import tomllib
from collections.abc import Callable, Iterable
from pathlib import Path
from uuid import UUID

import pytest
from django.contrib import admin
from django.contrib.staticfiles import finders
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from hypothesis import given
from hypothesis import strategies as st

from adote import __version__
from adote.accounts.adapters.models import User
from adote.adoption.adapters.models import AdoptionRequestModel
from adote.config.settings import env, env_bool, env_list
from adote.demo.adapters.seeding import PASSWORD, seed
from adote.pets.adapters.models import PetModel
from tests.conftest import signed_in

REPO = Path(__file__).resolve().parents[1]


def test_the_package_version_is_the_project_version() -> None:
    project = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert __version__ == project["version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__), "SemVer: MAJOR.MINOR.PATCH"


@pytest.mark.django_db
def test_health_reports_ok_and_the_version() -> None:
    response = Client().get(reverse("shared:health"))
    assert response.json() == {"status": "ok", "version": __version__}
    assert "no-cache" in response["Cache-Control"]


@pytest.mark.django_db
def test_no_model_change_lacks_a_migration() -> None:
    call_command("makemigrations", "--check", "--dry-run", verbosity=0)


@pytest.mark.django_db
def test_the_demo_seed_runs_once_through_the_rules() -> None:
    assert seed()
    assert not seed()
    assert User.objects.count() == 3
    assert PetModel.objects.count() == 5
    statuses = sorted(AdoptionRequestModel.objects.values_list("status", flat=True))
    assert statuses == ["approved", "pending", "pending", "pending", "rejected"]
    client = Client()
    assert client.login(username="ana", password=PASSWORD)


@pytest.mark.django_db
def test_the_seed_command_reports(capsys: pytest.CaptureFixture[str]) -> None:
    call_command("seed_demo")
    call_command("seed_demo")
    out = capsys.readouterr().out
    assert "Semente criada" in out
    assert "nada mudou" in out


@pytest.mark.django_db
def test_every_admin_page_opens_and_requests_are_read_only(
    user_factory: Callable[..., User], pet_factory: Callable[..., UUID]
) -> None:
    seed()
    root = User.objects.create_superuser("root", "root@example.com", "uma-senha-longa")
    client = signed_in(root)
    for model in admin.site._registry:  # noqa: SLF001 - the registry is the list of pages to visit
        meta = model._meta  # noqa: SLF001 - Django's documented way to reach model metadata
        changelist = client.get(reverse(f"admin:{meta.app_label}_{meta.model_name}_changelist"))
        assert changelist.status_code == 200, meta.label
        first = model._default_manager.first()  # noqa: SLF001
        if first is not None:
            change = client.get(reverse(f"admin:{meta.app_label}_{meta.model_name}_change", args=[first.pk]))
            assert change.status_code == 200, meta.label
    assert client.get(reverse("admin:adoption_adoptionrequestmodel_add")).status_code == 403


def test_every_static_file_a_template_names_exists() -> None:
    templates = list((REPO / "src").rglob("templates/**/*.html"))
    assert templates
    names = {
        name
        for path in templates
        for name in re.findall(r"{% static '([^']+)' %}", path.read_text(encoding="utf-8"))
    }
    assert names
    missing = [name for name in sorted(names) if finders.find(name) is None]
    assert not missing


def test_templates_load_nothing_from_other_origins() -> None:
    for path in (REPO / "src").rglob("templates/**/*.html"):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"""(src|href)=["']https?://""", text), path


@pytest.mark.django_db
def test_errors_use_the_apps_pages(user_factory: Callable[..., User]) -> None:
    response = signed_in(user_factory()).get("/nada-aqui/")
    assert response.status_code == 404
    assert "não achamos essa página" in response.content.decode()


@pytest.mark.django_db
def test_security_headers_are_on(user_factory: Callable[..., User]) -> None:
    response = Client().get(reverse("accounts:login"))
    assert response["X-Frame-Options"] == "DENY"
    assert response["X-Content-Type-Options"] == "nosniff"
    policy = response["Content-Security-Policy"]
    assert "script-src 'self';" in policy
    assert "frame-ancestors 'none'" in policy


@given(st.sampled_from(["1", "true", "TRUE", " yes ", "on"]), st.sampled_from(["0", "false", "no", "off"]))
def test_env_bool_reads_the_usual_spellings(yes: str, no: str) -> None:
    import os  # noqa: PLC0415

    os.environ["ADOTE_TEST_FLAG"] = yes
    assert env_bool("ADOTE_TEST_FLAG", default=False)
    os.environ["ADOTE_TEST_FLAG"] = no
    assert not env_bool("ADOTE_TEST_FLAG", default=True)
    for blank in ("", "  "):
        os.environ["ADOTE_TEST_FLAG"] = blank
        assert env_bool("ADOTE_TEST_FLAG", default=True)
    del os.environ["ADOTE_TEST_FLAG"]
    assert env_bool("ADOTE_TEST_FLAG", default=True)


@given(st.sampled_from(["", " ", "\t"]), st.text(min_size=1).filter(str.strip))
def test_a_blank_variable_counts_as_unset(blank: str, default: str) -> None:
    """A copied `.env.example` leaves keys empty; they must fall back to the default, not to ''."""
    import os  # noqa: PLC0415

    os.environ["ADOTE_TEST_VALUE"] = blank
    assert env("ADOTE_TEST_VALUE", default) == default
    os.environ["ADOTE_TEST_VALUE"] = " kept as is "
    assert env("ADOTE_TEST_VALUE", default) == " kept as is "
    del os.environ["ADOTE_TEST_VALUE"]
    assert env("ADOTE_TEST_VALUE", default) == default


@given(st.lists(st.from_regex(r"[a-z0-9.\-]{1,12}", fullmatch=True), max_size=5))
def test_env_list_splits_on_commas_and_drops_blanks(items: list[str]) -> None:
    import os  # noqa: PLC0415

    os.environ["ADOTE_TEST_LIST"] = " , ".join(items) + ", ,"
    assert env_list("ADOTE_TEST_LIST") == items
    del os.environ["ADOTE_TEST_LIST"]


def _settings_with(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    code = "import adote.config.settings as s; print(s.DEBUG, s.SECURE_SSL_REDIRECT if not s.DEBUG else '-')"
    clean = {key: value for key, value in __import__("os").environ.items() if not key.startswith("DJANGO_")}
    return subprocess.run(  # noqa: S603 - fixed interpreter and code
        [sys.executable, "-c", code], env=clean | env, capture_output=True, text=True, check=False
    )


def test_production_is_the_default_and_needs_a_secret() -> None:
    missing = _settings_with({})
    assert missing.returncode != 0
    assert "DJANGO_SECRET_KEY is required" in missing.stderr
    production = _settings_with({"DJANGO_SECRET_KEY": "x" * 50})
    assert production.stdout.split() == ["False", "True"]
    development = _settings_with({"DJANGO_DEBUG": "1"})
    assert development.stdout.split() == ["True", "-"]


def test_the_server_entry_points_load() -> None:
    from adote.config import asgi, wsgi  # noqa: PLC0415

    assert callable(wsgi.application)
    assert callable(asgi.application)


@pytest.mark.django_db
def test_the_catalog_seed_is_idempotent_and_reversible() -> None:
    """Runs the migration's own functions inside the test transaction: a real migrate back and forth
    would need a transactional test, whose flush wipes the seeded catalog for every test after it."""
    from django.apps import apps  # noqa: PLC0415

    from adote.pets.adapters.models import Breed, Tag  # noqa: PLC0415

    migration = importlib.import_module("adote.pets.adapters.migrations.0002_seed_catalog")
    counts = (Breed.objects.count(), Tag.objects.count())
    migration.seed(apps, None)
    assert (Breed.objects.count(), Tag.objects.count()) == counts
    migration.unseed(apps, None)
    assert not Breed.objects.exists()
    assert not Tag.objects.exists()
    migration.seed(apps, None)
    assert (Breed.objects.count(), Tag.objects.count()) == counts


@given(st.sampled_from(["61999998888", "6133334444", "", "123", "abc"]))
def test_the_phone_filter_formats_valid_numbers_and_keeps_the_rest(digits: str) -> None:
    from adote.shared.adapters.templatetags.adote import phone  # noqa: PLC0415

    shown = phone(digits)
    assert shown in {"(61) 99999-8888", "(61) 3333-4444"} if len(digits) >= 10 else shown == digits


@pytest.mark.django_db
def test_profiles_show_the_phone_formatted(user_factory: Callable[..., User]) -> None:
    user = user_factory(phone="11987654321")
    page = signed_in(user).get(reverse("accounts:profile")).content.decode()
    assert "(11) 98765-4321" in page
    assert "11987654321" not in page


PUBLIC = {"accounts:login", "accounts:signup", "shared:health", "admin:login"}


def _named_routes() -> list[tuple[str, int]]:
    from django.urls import URLPattern, URLResolver, get_resolver  # noqa: PLC0415

    found: list[tuple[str, int]] = []

    def walk(patterns: Iterable[object], namespace: str) -> None:
        for pattern in patterns:
            if isinstance(pattern, URLResolver):
                inner = f"{namespace}{pattern.namespace}:" if pattern.namespace else namespace
                walk(pattern.url_patterns, inner)
            elif isinstance(pattern, URLPattern) and pattern.name and not namespace.startswith("admin:"):
                found.append((f"{namespace}{pattern.name}", len(pattern.pattern.converters)))

    walk(get_resolver().url_patterns, "")
    return found


@pytest.mark.django_db
def test_every_route_requires_login_except_the_public_ones() -> None:
    from uuid import uuid4  # noqa: PLC0415

    client = Client()
    routes = _named_routes()
    assert {name for name, _ in routes} >= PUBLIC - {"admin:login"}
    for name, arguments in routes:
        url = reverse(name, args=[uuid4()] * arguments)
        status = client.get(url).status_code
        if name in PUBLIC:
            assert status == 200, name
        else:
            assert status in {302, 405}, name
            if status == 302:
                assert client.get(url)["Location"].startswith(reverse("accounts:login")), name
