"""What a person tells about themselves. Credentials are not here: the adapter owns them."""

from typing import Annotated

from pydantic import EmailStr, StringConstraints

from adote.shared.domain import FrozenModel, PhoneNumber, PostalCode, State

NAME_LIMIT = 150
PLACE_LIMIT = 100
ABOUT_LIMIT = 2000

type AccountId = int
type Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=NAME_LIMIT)]
type OptionalName = Annotated[str, StringConstraints(strip_whitespace=True, max_length=NAME_LIMIT)]
type Place = Annotated[str, StringConstraints(strip_whitespace=True, max_length=PLACE_LIMIT)]
type About = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=ABOUT_LIMIT)]


class Profile(FrozenModel):
    first_name: Name
    last_name: OptionalName = ""
    email: EmailStr
    phone: PhoneNumber
    postal_code: PostalCode | None = None
    state: State
    city: Place = ""
    neighborhood: Place = ""
    about: About  # the adopter's introduction: the one thing a tutor reads before deciding

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
