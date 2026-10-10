"""Adote: plataforma de adoção de animais."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("adote")
except PackageNotFoundError:  # pragma: no cover - running from a tree that was never installed
    __version__ = "0.0.0"
