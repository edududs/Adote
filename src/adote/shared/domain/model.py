"""Base of every entity and value object: frozen, strict about fields, changed only by copy."""

from typing import Self

from pydantic import BaseModel, ConfigDict


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=False)

    def evolve(self, **changes: object) -> Self:
        """Return a copy with `changes` applied, validated again.

        Pydantic's own `model_copy(update=...)` skips validation, so it could build an invalid entity.
        """
        return type(self).model_validate({**dict(self), **changes})
