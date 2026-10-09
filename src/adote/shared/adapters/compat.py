"""Typed doors to Django APIs newer than the django-types stubs.

Each entry is the real Django function with the signature it has. Delete an entry, and import from
Django directly, once the stubs know the API.
"""

from collections.abc import Callable
from typing import Protocol, cast

import django.contrib.auth.decorators as auth_decorators
import django.tasks as django_tasks  # pyright: ignore[reportMissingImports] - Django 6.0, no stubs yet


class Task[**P](Protocol):
    def enqueue(self, *args: P.args, **kwargs: P.kwargs) -> object: ...


def login_not_required[V: Callable[..., object]](view: V) -> V:
    """Django 5.1: exempts a view from LoginRequiredMiddleware."""
    exempt = auth_decorators.login_not_required  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownVariableType]
    return cast("V", exempt(view))


def task[**P](function: Callable[P, None]) -> Task[P]:
    """Django 6.0: turns a module-level function into a task of the default backend."""
    decorate = django_tasks.task  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    return cast("Task[P]", decorate(function))
