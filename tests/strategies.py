"""Hypothesis strategies for the domain's values: valid ones, and the noisy ways people type them."""

from hypothesis import strategies as st

from adote.accounts.domain import Profile
from adote.pets.domain import PetDetails, Sex, Species
from adote.shared.domain import PhoneNumber, PostalCode, State
from adote.shared.domain.phone import AREA_CODES

area_codes = st.sampled_from(sorted(AREA_CODES))
states = st.sampled_from(list(State))


@st.composite
def phone_digits(draw: st.DrawFn) -> str:
    """National digits of a valid number: a mobile (9 + 8 digits) or a landline (2-5 + 7 digits)."""
    area = draw(area_codes)
    if draw(st.booleans()):
        rest = "9" + draw(st.text("0123456789", min_size=8, max_size=8))
    else:
        rest = draw(st.sampled_from("2345")) + draw(st.text("0123456789", min_size=7, max_size=7))
    return f"{area}{rest}"


phones = phone_digits().map(lambda digits: PhoneNumber(digits=digits))


@st.composite
def typed_phone(draw: st.DrawFn, digits: str) -> str:
    """`digits` as a person might type it: mask, spaces, dashes, a +55 or a trunk 0 in front."""
    prefix = draw(st.sampled_from(["", "+55 ", "55", "0", "+55", "(0", "0 "]))
    noise = st.sampled_from(["", " ", "-", ".", "(", ")", "  "])
    body = "".join(char + draw(noise) for char in digits)
    return f"{prefix}{body}"


postal_digits = st.text("0123456789", min_size=8, max_size=8).filter(lambda d: d != "00000000")
postal_codes = postal_digits.map(lambda digits: PostalCode(digits=digits))

names = st.text(
    alphabet=st.characters(categories=["L"], max_codepoint=0x24F), min_size=1, max_size=30
).filter(lambda text: text.strip() == text and text)
paragraphs = st.text(
    alphabet=st.characters(categories=["L", "N", "Zs", "P"], max_codepoint=0x24F), min_size=1, max_size=200
).filter(lambda text: text.strip())


@st.composite
def profiles(draw: st.DrawFn) -> Profile:
    local = draw(st.from_regex(r"[a-z][a-z0-9]{2,12}", fullmatch=True))
    return Profile(
        first_name=draw(names),
        last_name=draw(st.one_of(st.just(""), names)),
        email=f"{local}@example.com",
        phone=draw(phones),
        postal_code=draw(st.none() | postal_codes),
        state=draw(states),
        city=draw(st.one_of(st.just(""), names)),
        neighborhood="",
        about=draw(paragraphs),
    )


@st.composite
def pet_details(
    draw: st.DrawFn,
    *,
    breed_id: int = 1,
    species: Species = Species.DOG,
    tag_ids: frozenset[int] = frozenset(),
) -> PetDetails:
    return PetDetails(
        name=draw(names),
        species=species,
        sex=draw(st.sampled_from(list(Sex))),
        breed_id=breed_id,
        tag_ids=tag_ids,
        description=draw(paragraphs),
        city=draw(names),
        state=draw(states),
        contact_phone=draw(phones),
    )
