"""The core of each context imports only the stdlib, pydantic and the layers beneath it, its own or the
shared kernel's. Never Django, never another context. Walking the AST keeps this from rotting."""

import ast
import sys
from importlib.util import resolve_name
from pathlib import Path

import pytest

ROOT = "adote"
PACKAGE = Path(__file__).resolve().parents[1] / "src" / ROOT
SHARED = "shared"
CONTEXTS = ("accounts", "pets", "adoption", SHARED)
LAYERS = {
    "domain": ("domain",),
    "application": ("domain", "application"),
}
CORE = [(context, layer) for context in CONTEXTS for layer in LAYERS]


def allowed(context: str, layer: str) -> set[str]:
    """Own layers beneath, plus the same layers of the shared kernel. Never another context."""
    return {"pydantic"} | {
        f"{ROOT}.{owner}.{beneath}" for owner in (context, SHARED) for beneath in LAYERS[layer]
    }


def violations(source: str, module: str, context: str, layer: str) -> list[str]:
    package = module.rsplit(".", 1)[0]
    imported: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            name = "." * node.level + (node.module or "")
            imported.append(resolve_name(name, package) if node.level else name)
    permitted = allowed(context, layer)
    return [
        name
        for name in imported
        if name.split(".")[0] not in sys.stdlib_module_names
        and not any(name == prefix or name.startswith(f"{prefix}.") for prefix in permitted)
    ]


@pytest.mark.parametrize(("context", "layer"), CORE)
def test_core_layers_import_only_what_they_may(context: str, layer: str) -> None:
    directory = PACKAGE / context / layer
    assert directory.is_dir(), f"{directory} is missing: the guard would pass vacuously"
    files = list(directory.rglob("*.py"))
    assert files
    for path in files:
        module = ".".join((ROOT, *path.relative_to(PACKAGE).with_suffix("").parts))
        assert not violations(path.read_text(encoding="utf-8"), module, context, layer), path


@pytest.mark.parametrize("context", CONTEXTS)
def test_every_context_has_an_adapters_layer(context: str) -> None:
    assert (PACKAGE / context / "adapters" / "apps.py").is_file()


def test_demo_is_composition_only() -> None:
    """`demo` has no vocabulary and no rule, only the seed that drives the other contexts' use cases."""
    packages = {
        child.name for child in (PACKAGE / "demo").iterdir() if child.is_dir() and child.name != "__pycache__"
    }
    assert packages == {"adapters"}


def test_guard_detects_deliberate_violations() -> None:
    assert violations("import django", f"{ROOT}.adoption.domain.process", "adoption", "domain")
    assert violations("from django.db import models", f"{ROOT}.pets.application.ports", "pets", "application")
    assert violations(
        f"from {ROOT}.pets.domain import Pet", f"{ROOT}.adoption.domain.process", "adoption", "domain"
    )
    assert violations(
        "from ..application import ports", f"{ROOT}.adoption.domain.process", "adoption", "domain"
    )
    assert violations(
        f"from {ROOT}.adoption.adapters import x",
        f"{ROOT}.adoption.application.ports",
        "adoption",
        "application",
    )
    assert violations(f"from {ROOT}.config import settings", f"{ROOT}.shared.domain.phone", SHARED, "domain")
    assert violations("import PIL", f"{ROOT}.pets.application.use_cases", "pets", "application")


def test_guard_accepts_the_allowed_imports() -> None:
    domain = (
        "import uuid\nfrom pydantic import BaseModel\nfrom .errors import X\n"
        "from adote.shared.domain import State\n"
    )
    assert not violations(domain, f"{ROOT}.adoption.domain.process", "adoption", "domain")
    application = (
        "from ..domain import Pet\nfrom adote.shared.application import Clock\nfrom . import ports\n"
    )
    assert not violations(application, f"{ROOT}.pets.application.use_cases", "pets", "application")
