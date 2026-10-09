from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from adote.shared.adapters.compat import login_not_required

admin.site.site_header = "Adote: administração"
admin.site.site_title = "Adote"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("adote.shared.adapters.urls")),
    path("conta/", include("adote.accounts.adapters.urls")),
    path("pets/", include("adote.pets.adapters.urls")),
    path("", include("adote.adoption.adapters.urls")),
]

if settings.SERVE_MEDIA:
    urlpatterns += [
        re_path(
            rf"^{settings.MEDIA_URL.lstrip('/')}(?P<path>.*)$",
            login_not_required(serve),
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]
