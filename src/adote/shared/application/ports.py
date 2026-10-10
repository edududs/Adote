from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        """Timezone-aware current time. Injected so rules about time are testable."""
        ...


class Mailer(Protocol):
    def send(self, *, to: str, subject: str, body: str) -> None:
        """Deliver one plain-text message. The provider is an adapter and environment variables."""
        ...
