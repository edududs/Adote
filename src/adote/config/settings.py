"""Settings read from the environment (12-factor). Safe by default: development is the opt-in.

`DJANGO_DEBUG=1` turns on debug and a throwaway secret key. Without it, `DJANGO_SECRET_KEY` and
`DJANGO_ALLOWED_HOSTS` are required and the production security headers are on.
"""

import os
from pathlib import Path
from typing import Any

import dj_database_url
from django.contrib.messages import constants as messages
from django.core.exceptions import ImproperlyConfigured

PACKAGE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = PACKAGE_DIR.parent.parent  # the repository root, where manage.py lives


def env_bool(name: str, *, default: bool) -> bool:
    raw = os.environ.get(name)
    return default if raw is None else raw.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


DEBUG = env_bool("DJANGO_DEBUG", default=False)


def secret_key() -> str:
    key = os.environ.get("DJANGO_SECRET_KEY", "")
    if key:
        return key
    if not DEBUG:
        msg = "DJANGO_SECRET_KEY is required when DJANGO_DEBUG is off"
        raise ImproperlyConfigured(msg)
    return "django-insecure-development-only-never-in-production"


SECRET_KEY = secret_key()

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]" if DEBUG else "")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django.forms",
    "adote.shared.adapters",
    "adote.accounts.adapters",
    "adote.pets.adapters",
    "adote.adoption.adapters",
    "adote.demo.adapters",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Every view needs a signed-in account unless it is marked @login_not_required (Django 5.1+).
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
]

ROOT_URLCONF = "adote.config.urls"
WSGI_APPLICATION = "adote.config.wsgi.application"
ASGI_APPLICATION = "adote.config.asgi.application"

TEMPLATES: list[dict[str, Any]] = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.csp",
                "adote.shared.adapters.context_processors.version",
            ],
        },
    },
]

# Forms render each field through templates/forms/field.html (Django 5+ field templates).
FORM_RENDERER = "adote.shared.adapters.forms.AdoteFormRenderer"

# Database: SQLite by default, anything dj-database-url reads otherwise (Postgres in production).
DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=int(os.environ.get("DATABASE_CONN_MAX_AGE", "60")),
        conn_health_checks=True,
    )
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "adoption:board"
LOGOUT_REDIRECT_URL = "accounts:login"

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Static files are served by WhiteNoise, hashed and compressed. Uploaded photos live in MEDIA_ROOT.
STATIC_URL = "static/"
STATIC_ROOT = Path(os.environ.get("DJANGO_STATIC_ROOT", BASE_DIR / "staticfiles"))
MEDIA_URL = "media/"
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT", BASE_DIR / "media"))
# A reverse proxy or object storage should serve media in production; this is the fallback.
SERVE_MEDIA = env_bool("DJANGO_SERVE_MEDIA", default=DEBUG)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        if DEBUG
        else "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

PET_PHOTO_MAX_BYTES = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = PET_PHOTO_MAX_BYTES + 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = DATA_UPLOAD_MAX_MEMORY_SIZE

MESSAGE_TAGS = {
    messages.DEBUG: "alert-secondary",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}

# E-mail (Django 6.1 MAILERS): printed to the console unless an SMTP host is configured. The deploy
# checklist refuses a console mailer, so production cannot silently drop every message.
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
MAILERS: dict[str, dict[str, Any]] = {
    "default": (
        {
            "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "OPTIONS": {
                "host": EMAIL_HOST,
                "port": int(os.environ.get("EMAIL_PORT", "587")),
                "username": os.environ.get("EMAIL_HOST_USER", ""),
                "password": os.environ.get("EMAIL_HOST_PASSWORD", ""),
                "use_tls": env_bool("EMAIL_USE_TLS", default=True),
                "timeout": 10,
            },
        }
        if EMAIL_HOST
        else {"BACKEND": "django.core.mail.backends.console.EmailBackend"}
    )
}
del EMAIL_HOST  # deprecated as a setting name once MAILERS exists
# Background tasks (Django 6 Tasks framework). E-mails are enqueued as tasks; the immediate backend
# runs them in the request, and a worker backend can replace it without touching the code.
TASKS: dict[str, dict[str, Any]] = {
    "default": {"BACKEND": "django.tasks.backends.immediate.ImmediateBackend"}
}

# Absolute base of the links that go out in e-mails.
SITE_URL = os.environ.get("ADOTE_SITE_URL", "http://localhost:8000")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Adote <nao-responda@adote.local>")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Security. Every header below is on unless debugging; the TLS ones assume a proxy that terminates TLS.
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
    SECURE_REDIRECT_EXEMPT = [r"^saude/$"]  # the container healthcheck speaks plain HTTP on loopback
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", str(60 * 60 * 24 * 365)))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Content Security Policy (Django 6): every script, style and font is served by us (vendored, see
# static/vendor/README.md); no inline script at all. Only the CEP lookup reaches another origin.
SELF, NONE, UNSAFE_INLINE = "'self'", "'none'", "'unsafe-inline'"
SECURE_CSP: dict[str, list[str]] = {
    "default-src": [SELF],
    "script-src": [SELF],
    "style-src": [SELF, UNSAFE_INLINE],  # Tom Select and Chart.js set inline styles
    "img-src": [SELF, "data:", "blob:"],  # blob: previews the photo chosen for upload
    "font-src": [SELF],
    "connect-src": [SELF, "https://viacep.com.br"],
    "frame-ancestors": [NONE],
    "form-action": [SELF],
    "base-uri": [SELF],
    "object-src": [NONE],
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "{asctime} {levelname} {name} {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO")},
}
