from django.db import connection
from django.http import HttpRequest, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from adote import __version__
from adote.shared.adapters.compat import login_not_required


@login_not_required
@require_GET
@never_cache
def health(request: HttpRequest) -> JsonResponse:
    """For the load balancer and the container healthcheck: the process answers and the database too."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok", "version": __version__})
