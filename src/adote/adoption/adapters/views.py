from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from adote.accounts.adapters.models import User
from adote.adoption.domain import (
    Action,
    AlreadyRequestedError,
    NotTheAdopterError,
    NotTheOwnerError,
    OwnPetError,
    PetAlreadyAdoptedError,
    RequestNotFoundError,
    RequestNotPendingError,
    UnknownPetError,
)
from adote.shared.domain import PhoneNumber

from . import queries
from .composition import approve_request, reject_request, request_adoption, withdraw_request
from .forms import BoardFilterForm, RequestForm
from .repository import DjangoAdoptionProcesses

PAGE_SIZE = 12


def _signed_in(request: HttpRequest) -> User:
    user = request.user
    assert isinstance(user, User)  # noqa: S101 - every caller is behind login_required
    return user


@login_required
@require_GET
def board(request: HttpRequest) -> HttpResponse:
    form = BoardFilterForm(request.GET)
    pets = queries.board(_signed_in(request).pk, form.to_filter())
    page = Paginator(pets, PAGE_SIZE).get_page(request.GET.get("pagina"))
    query = request.GET.copy()
    query.pop("pagina", None)
    return render(request, "adoption/board.html", {"form": form, "page": page, "query": query.urlencode()})


@login_required
@require_GET
def pet(request: HttpRequest, pet_id: UUID) -> HttpResponse:
    viewer = _signed_in(request)
    row = queries.pet_page(pet_id)
    process = DjangoAdoptionProcesses().get(pet_id)
    if row is None or process is None:
        raise Http404
    actions = process.actions_for(viewer.pk)
    live = process.live_request_of(viewer.pk)
    # Privacy: the tutor's phone goes only to the adopter they approved, and to the tutor themself.
    shares_contact = viewer.pk in {process.owner_id, process.adopter_id}
    phone = PhoneNumber(digits=row.contact_phone)
    context = {
        "pet": row,
        "is_owner": viewer.pk == process.owner_id,
        "can_request": Action.REQUEST in actions,
        "can_withdraw": Action.WITHDRAW in actions,
        "can_decide": Action.DECIDE in actions,
        "my_request": live,
        "pending_count": len(process.pending),
        "contact": phone if shares_contact else None,
        "form": RequestForm(),
    }
    return render(request, "adoption/pet.html", context)


@login_required
@require_POST
def request_pet(request: HttpRequest, pet_id: UUID) -> HttpResponse:
    form = RequestForm(request.POST)
    message = form.cleaned_data["message"] if form.is_valid() else ""
    try:
        request_adoption()(pet_id, adopter_id=_signed_in(request).pk, message=message)
    except UnknownPetError as error:
        raise Http404 from error
    except OwnPetError:
        messages.error(request, "Você não pode pedir para adotar um pet que você divulgou.")
    except PetAlreadyAdoptedError:
        messages.warning(request, "Este pet já foi adotado.")
    except AlreadyRequestedError:
        messages.info(request, "Você já fez um pedido para este pet.")
    else:
        messages.success(request, "Pedido enviado! Avisaremos por e-mail quando houver resposta.")
    return redirect("adoption:pet", pet_id=pet_id)


def _decide(request: HttpRequest, request_id: UUID, *, approve: bool) -> HttpResponse:
    use_case = approve_request() if approve else reject_request()
    try:
        use_case(request_id, by=_signed_in(request).pk)
    except (RequestNotFoundError, NotTheOwnerError) as error:
        raise Http404 from error
    except RequestNotPendingError:
        messages.warning(request, "Este pedido já tinha sido respondido ou cancelado.")
    else:
        messages.success(
            request,
            "Pedido aprovado! Os outros pedidos para este pet foram recusados."
            if approve
            else "Pedido recusado.",
        )
    return redirect("adoption:received")


@login_required
@require_POST
def approve(request: HttpRequest, request_id: UUID) -> HttpResponse:
    return _decide(request, request_id, approve=True)


@login_required
@require_POST
def reject(request: HttpRequest, request_id: UUID) -> HttpResponse:
    return _decide(request, request_id, approve=False)


@login_required
@require_POST
def withdraw(request: HttpRequest, request_id: UUID) -> HttpResponse:
    try:
        withdraw_request()(request_id, by=_signed_in(request).pk)
    except (RequestNotFoundError, NotTheAdopterError) as error:
        raise Http404 from error
    except RequestNotPendingError:
        messages.warning(request, "Este pedido já tinha sido respondido.")
    else:
        messages.success(request, "Pedido cancelado.")
    return redirect("adoption:sent")


@login_required
@require_GET
def received(request: HttpRequest) -> HttpResponse:
    return render(request, "adoption/received.html", {"requests": queries.received(_signed_in(request).pk)})


@login_required
@require_GET
def sent(request: HttpRequest) -> HttpResponse:
    return render(request, "adoption/sent.html", {"requests": queries.sent(_signed_in(request).pk)})


@login_required
@require_GET
def adopter(request: HttpRequest, request_id: UUID) -> HttpResponse:
    row = queries.adopter_for_owner(request_id, _signed_in(request).pk)
    if row is None:
        raise Http404
    return render(request, "adoption/adopter.html", {"adoption_request": row})


@login_required
@require_GET
def my_pets(request: HttpRequest) -> HttpResponse:
    return render(request, "adoption/my_pets.html", {"pets": queries.my_pets(_signed_in(request).pk)})


@login_required
@require_GET
def dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, "adoption/dashboard.html", {"totals": queries.totals()})


@login_required
@require_GET
def dashboard_data(request: HttpRequest) -> JsonResponse:
    rows = queries.adoptions_by_breed()
    return JsonResponse({"labels": [name for name, _ in rows], "adoptions": [count for _, count in rows]})
