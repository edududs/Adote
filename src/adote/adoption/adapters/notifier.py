"""Turns adoption events into e-mails. The texts are pt-BR, like every word the person reads."""

from dataclasses import dataclass

from django.urls import reverse

from adote.accounts.adapters.models import User
from adote.adoption.domain import (
    AdoptionEvent,
    RequestApproved,
    RequestRejected,
    RequestSubmitted,
    RequestWithdrawn,
)
from adote.pets.adapters.models import PetModel
from adote.shared.application import Mailer
from adote.shared.domain import PhoneNumber


@dataclass(frozen=True, slots=True)
class EmailNotifier:
    mailer: Mailer
    site_url: str

    def notify(self, event: AdoptionEvent) -> None:
        pet = PetModel.objects.filter(pk=event.pet_id).only("name", "contact_phone").first()
        owner = User.objects.filter(pk=event.owner_id).first()
        adopter = User.objects.filter(pk=event.request.adopter_id).first()
        if pet is None or owner is None or adopter is None:
            return
        owner_name = owner.get_full_name() or owner.username
        adopter_name = adopter.get_full_name() or adopter.username
        match event:
            case RequestSubmitted():
                self.mailer.send(
                    to=owner.email,
                    subject=f"Novo pedido para adotar {pet.name}",
                    body=(
                        f"Olá, {owner.first_name or owner.username}!\n\n"
                        f"{adopter_name} quer adotar {pet.name}."
                        + (f'\n\nMensagem: "{event.request.message}"' if event.request.message else "")
                        + f"\n\nVeja o perfil e responda em {self._url('adoption:received')}\n"
                    ),
                )
            case RequestApproved():
                phone = PhoneNumber(digits=pet.contact_phone).formatted()
                self.mailer.send(
                    to=adopter.email,
                    subject=f"Seu pedido para adotar {pet.name} foi aprovado!",
                    body=(
                        f"Olá, {adopter.first_name or adopter.username}!\n\n"
                        f"{owner_name} aprovou o seu pedido para adotar {pet.name}.\n"
                        f"Combine a entrega pelo telefone {phone} ou pelo e-mail {owner.email}.\n\n"
                        f"Seus pedidos: {self._url('adoption:sent')}\n"
                    ),
                )
            case RequestRejected(automatic=automatic):
                reason = (
                    f"{pet.name} encontrou outro lar."
                    if automatic
                    else f"Quem divulgou {pet.name} escolheu não seguir com o seu pedido."
                )
                self.mailer.send(
                    to=adopter.email,
                    subject=f"Atualização do seu pedido para adotar {pet.name}",
                    body=(
                        f"Olá, {adopter.first_name or adopter.username}.\n\n{reason}\n"
                        f"Outros pets esperam por um lar: {self._url('adoption:board')}\n"
                    ),
                )
            case RequestWithdrawn():
                self.mailer.send(
                    to=owner.email,
                    subject=f"Um pedido para adotar {pet.name} foi cancelado",
                    body=(
                        f"Olá, {owner.first_name or owner.username}.\n\n"
                        f"{adopter_name} cancelou o pedido para adotar {pet.name}.\n"
                    ),
                )
            case _:
                return

    def _url(self, name: str) -> str:
        return f"{self.site_url.rstrip('/')}{reverse(name)}"
