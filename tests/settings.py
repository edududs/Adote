# pyright: reportConstantRedefinition=false
"""Test settings: the real ones, production mode, with what the environment would provide."""

import os
import tempfile
from pathlib import Path

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-key")
os.environ.pop("DJANGO_DEBUG", None)
# SQLite unless TEST_DATABASE_URL points elsewhere: CI runs the whole suite on Postgres too.
os.environ.pop("DATABASE_URL", None)
if os.environ.get("TEST_DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

from adote.config.settings import *  # noqa: F403 - Django's idiom for layered settings

STATIC_ROOT = Path(tempfile.mkdtemp(prefix="adote-static-"))  # WhiteNoise warns about a missing one
SECURE_SSL_REDIRECT = False  # the test client speaks plain HTTP
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # speed; never outside tests
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
LOGGING = {"version": 1, "disable_existing_loggers": False, "root": {"level": "CRITICAL"}}
