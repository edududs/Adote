from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

import pytest
from django.contrib.messages import get_messages
from django.test import Client
from django.urls import reverse
from hypothesis import given
from hypothesis import strategies as st

from adote.accounts.adapters.models import User
from adote.adoption.adapters.composition import approve_request, request_adoption
from adote.adoption.adapters.models import AdoptionRequestModel
from adote.adoption.domain import RequestStatus
from tests.conftest import DB, signed_in

pytestmark = pytest.mark.django_db


@dataclass
class Scene:
    owner: User
    adopter: User
    stranger: User
    pet_id: UUID
    request_id: UUID


@pytest.fixture
def scene(user_factory: Callable[..., User], pet_factory: Callable[..., UUID]) -> Scene:
    owner, adopter, stranger = user_factory("tutor"), user_factory("ana"), user_factory("estranho")
    pet_id = pet_factory(owner)
    request = request_adoption()(pet_id, adopter_id=adopter.pk, message="Por favor")
    return Scene(owner, adopter, stranger, pet_id, request.id)


def flash(response: object) -> list[str]:
    return [str(message) for message in get_messages(response.wsgi_request)]  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]


def _urls(scene: Scene) -> dict[str, str]:
    return {
        "board": reverse("adoption:board"),
        "pet": reverse("adoption:pet", args=[scene.pet_id]),
        "my_pets": reverse("adoption:my_pets"),
        "received": reverse("adoption:received"),
        "sent": reverse("adoption:sent"),
        "adopter": reverse("adoption:adopter", args=[scene.request_id]),
        "dashboard": reverse("adoption:dashboard"),
        "dashboard_data": reverse("adoption:dashboard_data"),
    }


def test_every_page_asks_for_login(scene: Scene) -> None:
    client = Client()
    for url in _urls(scene).values():
        response = client.get(url)
        assert response.status_code == 302
        assert response["Location"].startswith(reverse("accounts:login"))
    for name in ("approve", "reject", "withdraw"):
        response = client.post(reverse(f"adoption:{name}", args=[scene.request_id]))
        assert response.status_code == 302
    assert AdoptionRequestModel.objects.get().status == RequestStatus.PENDING.value


@pytest.mark.parametrize("name", ["approve", "reject", "withdraw"])
def test_state_changes_refuse_get(scene: Scene, name: str) -> None:
    response = signed_in(scene.owner).get(reverse(f"adoption:{name}", args=[scene.request_id]))
    assert response.status_code == 405


@pytest.mark.parametrize(
    ("name", "allowed"),
    [("approve", "owner"), ("reject", "owner"), ("withdraw", "adopter")],
)
def test_only_the_right_person_moves_a_request(scene: Scene, name: str, allowed: str) -> None:
    for role in ("owner", "adopter", "stranger"):
        if role == allowed:
            continue
        response = signed_in(getattr(scene, role)).post(reverse(f"adoption:{name}", args=[scene.request_id]))
        assert response.status_code == 404, role  # someone else's request looks like a missing one
        assert AdoptionRequestModel.objects.get().status == RequestStatus.PENDING.value
    response = signed_in(getattr(scene, allowed)).post(reverse(f"adoption:{name}", args=[scene.request_id]))
    assert response.status_code == 302
    assert AdoptionRequestModel.objects.get().status != RequestStatus.PENDING.value


def test_the_adopter_profile_is_for_the_tutor_only(scene: Scene) -> None:
    url = reverse("adoption:adopter", args=[scene.request_id])
    assert signed_in(scene.stranger).get(url).status_code == 404
    assert signed_in(scene.adopter).get(url).status_code == 404
    response = signed_in(scene.owner).get(url)
    assert response.status_code == 200
    assert scene.adopter.email in response.content.decode()
    assert "Por favor" in response.content.decode()


@DB
@given(st.uuids(), st.sampled_from(["approve", "reject", "withdraw", "adopter", "pet", "request"]))
def test_unknown_identifiers_are_404(scene: Scene, unknown: UUID, name: str) -> None:
    client = signed_in(scene.owner)
    url_name = f"adoption:{name}"
    url = reverse(url_name, args=[unknown])
    response = client.get(url) if name in {"adopter", "pet"} else client.post(url)
    assert response.status_code == 404


def test_the_tutors_phone_is_shown_only_to_the_approved_adopter(scene: Scene) -> None:
    url = reverse("adoption:pet", args=[scene.pet_id])
    phone = "(61) 99999-0000"
    assert phone in signed_in(scene.owner).get(url).content.decode()
    assert phone not in signed_in(scene.adopter).get(url).content.decode()
    assert phone not in signed_in(scene.stranger).get(url).content.decode()
    approve_request()(scene.request_id, by=scene.owner.pk)
    page = signed_in(scene.adopter).get(url).content.decode()
    assert phone in page
    assert "wa.me/5561999990000" in page
    assert phone not in signed_in(scene.stranger).get(url).content.decode()


def test_the_pet_page_offers_what_each_person_may_do(scene: Scene) -> None:
    url = reverse("adoption:pet", args=[scene.pet_id])
    owner, adopter, stranger = (
        signed_in(u).get(url).context for u in (scene.owner, scene.adopter, scene.stranger)
    )
    assert (owner["can_decide"], owner["can_request"], owner["is_owner"]) == (True, False, True)
    assert (adopter["can_withdraw"], adopter["can_request"]) == (True, False)
    assert (stranger["can_request"], stranger["can_withdraw"]) == (True, False)


def test_requesting_tells_what_happened(scene: Scene, user_factory: Callable[..., User]) -> None:
    url = reverse("adoption:request", args=[scene.pet_id])
    response = signed_in(scene.stranger).post(url, {"message": "Quero muito"})
    assert response.status_code == 302
    assert "Pedido enviado" in flash(response)[-1]
    assert AdoptionRequestModel.objects.filter(adopter=scene.stranger, message="Quero muito").exists()
    assert "já fez um pedido" in flash(signed_in(scene.stranger).post(url))[-1]
    assert "não pode pedir" in flash(signed_in(scene.owner).post(url))[-1]
    approve_request()(scene.request_id, by=scene.owner.pk)
    assert "já foi adotado" in flash(signed_in(user_factory()).post(url))[-1]


def test_a_too_long_message_is_dropped_not_refused(scene: Scene) -> None:
    signed_in(scene.stranger).post(reverse("adoption:request", args=[scene.pet_id]), {"message": "x" * 5000})
    assert AdoptionRequestModel.objects.get(adopter=scene.stranger).message == ""


def test_deciding_twice_warns(scene: Scene) -> None:
    client = signed_in(scene.owner)
    client.post(reverse("adoption:reject", args=[scene.request_id]))
    assert (
        "já tinha sido respondido"
        in flash(client.post(reverse("adoption:approve", args=[scene.request_id])))[-1]
    )
    adopter = signed_in(scene.adopter)
    assert (
        "já tinha sido respondido"
        in flash(adopter.post(reverse("adoption:withdraw", args=[scene.request_id])))[-1]
    )


def test_listings_show_each_person_their_own(scene: Scene, user_factory: Callable[..., User]) -> None:
    received = signed_in(scene.owner).get(reverse("adoption:received"))
    assert [r.pk for r in received.context["requests"]] == [scene.request_id]
    assert list(signed_in(scene.stranger).get(reverse("adoption:received")).context["requests"]) == []
    sent = signed_in(scene.adopter).get(reverse("adoption:sent"))
    assert [r.pk for r in sent.context["requests"]] == [scene.request_id]
    mine = signed_in(scene.owner).get(reverse("adoption:my_pets")).context["pets"]
    assert [(p.pk, p.pending_count, p.adopted) for p in mine] == [(scene.pet_id, 1, False)]
    assert list(signed_in(scene.adopter).get(reverse("adoption:my_pets")).context["pets"]) == []


def test_received_requests_put_pending_first(scene: Scene, user_factory: Callable[..., User]) -> None:
    late = request_adoption()(scene.pet_id, adopter_id=user_factory().pk)
    signed_in(scene.owner).post(reverse("adoption:reject", args=[scene.request_id]))
    received = signed_in(scene.owner).get(reverse("adoption:received")).context["requests"]
    assert [r.pk for r in received] == [late.id, scene.request_id]


# The board


@pytest.fixture
def town(user_factory: Callable[..., User], pet_factory: Callable[..., UUID]) -> User:
    """A viewer, and pets of every kind around them: theirs, adopted, requested, filtered out."""
    viewer, alice, bob = user_factory("viewer"), user_factory("alice"), user_factory("bob")
    from adote.pets.domain import Sex  # noqa: PLC0415
    from adote.shared.domain import State  # noqa: PLC0415

    pet_factory(viewer, name="Meu")
    for n, (owner, breed, sex, state, city) in enumerate(
        [
            (alice, "Beagle", Sex.MALE, State.DF, "Brasília"),
            (alice, "Pug", Sex.FEMALE, State.SP, "São Paulo"),
            (bob, "Beagle", Sex.FEMALE, State.SP, "Campinas"),
            (bob, "Poodle", Sex.MALE, State.RJ, "Niterói"),
            (bob, "Pug", Sex.MALE, State.DF, "Taguatinga"),
        ]
    ):
        pet_factory(owner, name=f"Pet{n}", breed=breed, sex=sex, state=state, city=city)
    adopted = pet_factory(alice, name="Adotado")
    request = request_adoption()(adopted, adopter_id=bob.pk)
    approve_request()(request.id, by=alice.pk)
    requested = pet_factory(bob, name="Pedido")
    request_adoption()(requested, adopter_id=viewer.pk)
    return viewer


@DB
@given(
    species=st.sampled_from(["", "dog", "cat", "lizard"]),
    breed=st.sampled_from(["", "x", "-1", "999999"]) | st.integers(1, 60).map(str),
    sex=st.sampled_from(["", "male", "female", "other"]),
    state=st.sampled_from(["", "DF", "SP", "RJ", "XX"]),
    city=st.sampled_from(["", "bras", "CAMP", "zzz", " niter "]),
    page=st.sampled_from(["", "1", "2", "-3", "abc"]),
)
def test_the_board_only_lists_pets_one_may_adopt_and_every_filter_holds(
    town: User, species: str, breed: str, sex: str, state: str, city: str, page: str
) -> None:
    query = {"species": species, "breed": breed, "sex": sex, "state": state, "city": city, "pagina": page}
    response = signed_in(town).get(reverse("adoption:board"), query)
    assert response.status_code == 200
    pets = list(response.context["page"].object_list)
    filters = response.context["form"].to_filter()
    for pet in pets:
        assert pet.owner_id != town.pk
        assert not AdoptionRequestModel.objects.filter(pet=pet, status="approved").exists()
        assert not filters.species or pet.species == filters.species
        assert filters.breed_id is None or pet.breed_id == filters.breed_id
        assert not filters.sex or pet.sex == filters.sex
        assert not filters.state or pet.state == filters.state
        assert filters.city.lower() in pet.city.lower()
    if not any(query.values()):
        names = {pet.name for pet in pets}
        assert names == {"Pet0", "Pet1", "Pet2", "Pet3", "Pet4", "Pedido"}
        assert [p.requested_by_me for p in pets if p.name == "Pedido"] == [True]


def test_the_board_filters_by_tag_and_paginates(
    user_factory: Callable[..., User], pet_factory: Callable[..., UUID], tag_ids: list[int]
) -> None:
    viewer, owner = user_factory(), user_factory()
    for n in range(14):
        pet_factory(owner, name=f"P{n}", tag_ids=frozenset({tag_ids[0]}) if n % 2 else frozenset())
    client = signed_in(viewer)
    first = client.get(reverse("adoption:board"))
    assert len(first.context["page"].object_list) == 12
    second = client.get(reverse("adoption:board"), {"pagina": "2"})
    assert len(second.context["page"].object_list) == 2
    tagged = client.get(reverse("adoption:board"), {"tag": str(tag_ids[0])})
    assert len(tagged.context["page"].object_list) == 7
    # {% querystring %} keeps the filters in the page links
    filtered = client.get(reverse("adoption:board"), {"species": "dog"}).content.decode()
    assert "?species=dog&amp;pagina=2" in filtered


# The dashboard


@DB
@given(st.lists(st.tuples(st.sampled_from(["Beagle", "Pug", "Poodle"]), st.booleans()), max_size=6))
def test_dashboard_numbers_add_up(
    user_factory: Callable[..., User], pet_factory: Callable[..., UUID], pets: list[tuple[str, bool]]
) -> None:
    from tests.conftest import rolled_back  # noqa: PLC0415

    with rolled_back():
        owner, adopter = user_factory(), user_factory()
        for breed, adopted in pets:
            pet_id = pet_factory(owner, breed=breed)
            if adopted:
                request = request_adoption()(pet_id, adopter_id=adopter.pk)
                approve_request()(request.id, by=owner.pk)
        client = signed_in(adopter)
        totals = client.get(reverse("adoption:dashboard")).context["totals"]
        data = client.get(reverse("adoption:dashboard_data")).json()
        adopted_count = sum(adopted for _, adopted in pets)
        assert totals.published == len(pets)
        assert totals.adopted == adopted_count == sum(data["adoptions"])
        assert totals.available + totals.adopted == totals.published
        assert totals.pending_requests == 0
        assert data["adoptions"] == sorted(data["adoptions"], reverse=True)
        expected = {breed for breed, adopted in pets if adopted}
        assert set(data["labels"]) == expected
