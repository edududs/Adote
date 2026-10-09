from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from adote.accounts.adapters.models import User
from adote.pets.domain import (
    AdoptedPetError,
    BreedOfAnotherSpeciesError,
    NotPetOwnerError,
    PetNotFoundError,
    UnknownBreedError,
    UnknownTagError,
)
from adote.shared.domain import PhoneNumber

from .composition import publish_pet, remove_pet
from .forms import PetForm


def _signed_in(request: HttpRequest) -> User:
    user = request.user
    assert isinstance(user, User)  # noqa: S101 - every caller is behind login_required
    return user


@login_required
@require_http_methods(["GET", "POST"])
def publish(request: HttpRequest) -> HttpResponse:
    user = _signed_in(request)
    initial = {"state": user.state, "city": user.city}
    if user.phone:
        initial["contact_phone"] = PhoneNumber(digits=user.phone).formatted()
    form = PetForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            pet = publish_pet()(user.pk, form.pet_details(), form.photo_upload())
        except UnknownBreedError:
            form.add_error("breed", "Escolha uma raça da lista.")
        except BreedOfAnotherSpeciesError:
            form.add_error("breed", "Esta raça não é da espécie escolhida.")
        except UnknownTagError:
            form.add_error("tags", "Escolha características da lista.")
        else:
            messages.success(request, f"{pet.details.name} foi divulgado. Agora é esperar os pedidos!")
            return redirect("adoption:pet", pet_id=pet.id)
    return render(request, "pets/publish.html", {"form": form})


@login_required
@require_POST
def remove(request: HttpRequest, pet_id: UUID) -> HttpResponse:
    try:
        remove_pet()(pet_id, by=_signed_in(request).pk)
    except (PetNotFoundError, NotPetOwnerError) as error:
        # Someone else's pet answers like a missing one: no hint that the identifier exists.
        raise Http404 from error
    except AdoptedPetError:
        messages.warning(request, "Um pet adotado fica no histórico e não pode ser removido.")
    else:
        messages.success(request, "Pet removido.")
    return redirect("adoption:my_pets")
