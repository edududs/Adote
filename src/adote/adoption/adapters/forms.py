from django import forms

from adote.adoption.domain import MESSAGE_LIMIT
from adote.pets.adapters.forms import breed_choices
from adote.pets.adapters.models import SEX_CHOICES, SPECIES_CHOICES, STATE_CHOICES, Tag
from adote.shared.adapters.forms import StyledForm

from .queries import BoardFilter


class RequestForm(StyledForm, forms.Form):
    message = forms.CharField(
        label="Conte um pouco sobre você e sua casa",
        max_length=MESSAGE_LIMIT,
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": "Ex.: moro em casa com quintal, já tive cachorro…"}
        ),
    )


class BoardFilterForm(StyledForm, forms.Form):
    """Every field is optional and an invalid value is ignored: a filter never errors, it just widens."""

    species = forms.ChoiceField(label="Espécie", required=False, choices=[("", "Todas"), *SPECIES_CHOICES])
    breed = forms.TypedChoiceField(
        label="Raça", required=False, coerce=int, empty_value=None,
        choices=lambda: [("", "Todas"), *breed_choices()],
    )  # fmt: skip
    sex = forms.ChoiceField(label="Sexo", required=False, choices=[("", "Todos"), *SEX_CHOICES])
    state = forms.ChoiceField(label="Estado", required=False, choices=[("", "Todos"), *STATE_CHOICES])
    city = forms.CharField(label="Cidade", required=False, max_length=100)
    tag = forms.TypedChoiceField(
        label="Característica", required=False, coerce=int, empty_value=None,
        choices=lambda: [("", "Todas"), *((tag.pk, tag.name) for tag in Tag.objects.all())],
    )  # fmt: skip

    def to_filter(self) -> BoardFilter:
        if not self.is_valid():
            valid = {name: value for name, value in self.cleaned_data.items() if name not in self.errors}
        else:
            valid = self.cleaned_data
        return BoardFilter(
            species=valid.get("species") or "",
            breed_id=valid.get("breed"),
            sex=valid.get("sex") or "",
            state=valid.get("state") or "",
            city=(valid.get("city") or "").strip(),
            tag_id=valid.get("tag"),
        )
