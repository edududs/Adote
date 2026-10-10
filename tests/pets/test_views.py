from collections.abc import Callable
from uuid import UUID

import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from adote.accounts.adapters.models import User
from adote.adoption.adapters.composition import approve_request, request_adoption
from adote.pets.adapters.models import Breed, PetModel
from tests.conftest import png_bytes, signed_in

pytestmark = pytest.mark.django_db


def form(**changes: object) -> dict[str, object]:
    data: dict[str, object] = {
        "photo": SimpleUploadedFile("minha foto.png", png_bytes(), content_type="image/png"),
        "name": "  Thor  ",
        "species": "dog",
        "sex": "male",
        "breed": str(Breed.objects.get(species="dog", name="Beagle").pk),
        "description": "Dócil e brincalhão.",
        "state": "DF",
        "city": "Brasília",
        "contact_phone": "(61) 98888-7777",
    }
    return data | changes


def test_publishing_stores_the_pet_and_a_renamed_photo(
    user_factory: Callable[..., User], tag_ids: list[int]
) -> None:
    owner = user_factory()
    response = signed_in(owner).post(reverse("pets:publish"), form(tags=[str(t) for t in tag_ids[:2]]))
    pet = PetModel.objects.get()
    assert response.status_code == 302
    assert response["Location"] == reverse("adoption:pet", args=[pet.pk])
    assert (pet.name, pet.owner_id, pet.contact_phone) == ("Thor", owner.pk, "61988887777")
    assert sorted(pet.tags.values_list("pk", flat=True)) == sorted(tag_ids[:2])
    assert pet.photo.name.startswith("pets/")
    assert pet.photo.name.endswith(".png")
    assert "minha foto" not in pet.photo.name
    assert default_storage.exists(pet.photo.name)


def test_the_form_starts_with_the_tutors_contact(user_factory: Callable[..., User]) -> None:
    owner = user_factory(phone="61977776666", city="Gama")
    initial = signed_in(owner).get(reverse("pets:publish")).context["form"].initial
    assert initial == {"state": "DF", "city": "Gama", "contact_phone": "(61) 97777-6666"}


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        pytest.param(
            {"photo": SimpleUploadedFile("x.png", b"not an image", content_type="image/png")},
            "photo",
            id="not-an-image",
        ),
        pytest.param(
            {"photo": SimpleUploadedFile("x.gif", png_bytes(image_format="GIF"), content_type="image/gif")},
            "photo",
            id="gif",
        ),
        pytest.param({"contact_phone": "123"}, "contact_phone", id="bad-phone"),
        pytest.param({"species": "cat"}, "breed", id="dog-breed-on-a-cat"),
        pytest.param({"breed": "999999"}, "breed", id="unknown-breed"),
        pytest.param({"name": "   "}, "name", id="blank-name"),
        pytest.param({"state": "XX"}, "state", id="bad-state"),
    ],
)
def test_invalid_submissions_explain_the_field_and_store_nothing(
    user_factory: Callable[..., User], changes: dict[str, object], field: str
) -> None:
    response = signed_in(user_factory()).post(reverse("pets:publish"), form(**changes))
    assert response.status_code == 200
    assert field in response.context["form"].errors
    assert not PetModel.objects.exists()
    assert 'aria-invalid="true"' in response.content.decode()


@override_settings(PET_PHOTO_MAX_BYTES=10)
def test_a_photo_too_large_is_refused(user_factory: Callable[..., User]) -> None:
    response = signed_in(user_factory()).post(reverse("pets:publish"), form())
    assert "5 MB" in str(response.context["form"].errors["photo"])


def test_too_many_tags_are_refused(user_factory: Callable[..., User], tag_ids: list[int]) -> None:
    response = signed_in(user_factory()).post(
        reverse("pets:publish"), form(tags=[str(t) for t in tag_ids[:11]])
    )
    assert "tags" in response.context["form"].errors


def test_only_the_tutor_removes_and_only_before_adoption(
    user_factory: Callable[..., User], pet_factory: Callable[..., UUID]
) -> None:
    owner, other = user_factory(), user_factory()
    pet_id = pet_factory(owner)
    url = reverse("pets:remove", args=[pet_id])
    assert signed_in(owner).get(url).status_code == 405
    assert signed_in(other).post(url).status_code == 404
    request = request_adoption()(pet_id, adopter_id=other.pk)
    approve_request()(request.id, by=owner.pk)
    response = signed_in(owner).post(url)
    assert response.status_code == 302
    assert PetModel.objects.filter(pk=pet_id).exists()

    second = pet_factory(owner, name="Mel")
    photo = PetModel.objects.get(pk=second).photo.name
    signed_in(owner).post(reverse("pets:remove", args=[second]))
    assert not PetModel.objects.filter(pk=second).exists()
    assert not default_storage.exists(photo)


def test_publishing_requires_login(db: None) -> None:
    from django.test import Client  # noqa: PLC0415

    assert Client().get(reverse("pets:publish")).status_code == 302
