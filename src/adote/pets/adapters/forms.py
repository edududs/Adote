from typing import Any

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from PIL import Image, UnidentifiedImageError
from pydantic import ValidationError

from adote.pets.application import Photo
from adote.pets.domain import CITY_LIMIT, DESCRIPTION_LIMIT, NAME_LIMIT, TAG_LIMIT, PetDetails, Sex, Species
from adote.shared.adapters.forms import BootstrapForm
from adote.shared.domain import InvalidPhoneNumberError, PhoneNumber, State

from .models import SEX_CHOICES, SPECIES_CHOICES, STATE_CHOICES, Breed, Tag

FORMATS = {"JPEG": ".jpeg", "PNG": ".png", "WEBP": ".webp"}


def breed_choices() -> list[tuple[str, list[tuple[int, str]]]]:
    """Breeds grouped by species, so the select shows one optgroup per species."""
    groups: dict[str, list[tuple[int, str]]] = {species.label: [] for species in Species}
    for breed in Breed.objects.all():
        groups[Species(breed.species).label].append((breed.pk, breed.name))
    return list(groups.items())


class PetForm(BootstrapForm, forms.Form):
    photo = forms.ImageField(
        label="Foto",
        help_text="JPEG, PNG ou WEBP, até 5 MB.",
        widget=forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
    )
    name = forms.CharField(label="Nome", max_length=NAME_LIMIT)
    species = forms.ChoiceField(label="Espécie", choices=SPECIES_CHOICES)
    sex = forms.ChoiceField(label="Sexo", choices=SEX_CHOICES)
    breed = forms.TypedChoiceField(label="Raça", coerce=int, choices=breed_choices)
    tags = forms.TypedMultipleChoiceField(
        label="Características",
        coerce=int,
        required=False,
        choices=lambda: [(tag.pk, tag.name) for tag in Tag.objects.all()],
        widget=forms.SelectMultiple(attrs={"data-enhance": "select2"}),
    )
    description = forms.CharField(
        label="Descrição",
        max_length=DESCRIPTION_LIMIT,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Idade aproximada, porte, temperamento, cuidados de saúde.",
    )
    state = forms.ChoiceField(label="Estado", choices=[("", "Selecione"), *STATE_CHOICES])
    city = forms.CharField(label="Cidade", max_length=CITY_LIMIT)
    contact_phone = forms.CharField(
        label="Telefone para contato",
        max_length=20,
        widget=forms.TextInput(attrs={"data-mask": "phone", "inputmode": "tel"}),
        help_text="Só aparece para você e para quem tiver o pedido aprovado.",
    )

    def clean_photo(self) -> Photo:
        upload: UploadedFile = self.cleaned_data["photo"]
        if (upload.size or 0) > settings.PET_PHOTO_MAX_BYTES:
            msg = "A foto passa de 5 MB."
            raise forms.ValidationError(msg)
        upload.seek(0)
        content = upload.read()
        try:
            with Image.open(upload) as image:
                detected = image.format or ""
        except (UnidentifiedImageError, OSError) as error:
            msg = "Envie uma imagem JPEG, PNG ou WEBP."
            raise forms.ValidationError(msg) from error
        if detected not in FORMATS:
            msg = "Envie uma imagem JPEG, PNG ou WEBP."
            raise forms.ValidationError(msg)
        return Photo(filename=f"photo{FORMATS[detected]}", content=content)

    def clean_tags(self) -> frozenset[int]:
        tags = frozenset[int](self.cleaned_data["tags"])
        if len(tags) > TAG_LIMIT:
            msg = f"Escolha no máximo {TAG_LIMIT} características."
            raise forms.ValidationError(msg)
        return tags

    def clean_contact_phone(self) -> PhoneNumber:
        try:
            return PhoneNumber.parse(self.cleaned_data["contact_phone"])
        except InvalidPhoneNumberError as error:
            msg = "Informe um telefone com DDD, como (61) 99999-0000."
            raise forms.ValidationError(msg) from error

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()
        if not self.errors:
            try:
                self.pet_details()
            except ValidationError as error:
                msg = "Confira os dados do pet."
                raise forms.ValidationError(msg) from error
        return cleaned

    def pet_details(self) -> PetDetails:
        data = self.cleaned_data
        return PetDetails(
            name=data["name"],
            species=Species(data["species"]),
            sex=Sex(data["sex"]),
            breed_id=data["breed"],
            tag_ids=data["tags"],
            description=data["description"],
            city=data["city"],
            state=State(data["state"]),
            contact_phone=data["contact_phone"],
        )

    def photo_upload(self) -> Photo:
        return self.cleaned_data["photo"]
