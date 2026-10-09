from django.http import HttpRequest

from adote import __version__


def version(request: HttpRequest) -> dict[str, str]:
    return {"adote_version": __version__}
