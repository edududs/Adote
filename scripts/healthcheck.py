"""Container healthcheck: GET /saude/ as the proxy would send it (allowed host, HTTPS forwarded)."""

import os
import sys
import urllib.request

host = (os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost").split(",")[0] or "localhost").strip()
request = urllib.request.Request(
    "http://127.0.0.1:8000/saude/", headers={"Host": host, "X-Forwarded-Proto": "https"}
)
try:
    with urllib.request.urlopen(request, timeout=2) as response:  # noqa: S310 - fixed loopback URL
        sys.exit(0 if response.status == 200 else 1)  # noqa: PLR2004 - HTTP OK
except OSError:
    sys.exit(1)
