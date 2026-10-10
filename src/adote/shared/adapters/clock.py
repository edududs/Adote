from datetime import datetime

from django.utils import timezone


class SystemClock:
    def now(self) -> datetime:
        return timezone.now()
