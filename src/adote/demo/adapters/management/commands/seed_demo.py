from django.core.management.base import BaseCommand

from adote.demo.adapters.seeding import PASSWORD, PEOPLE, seed


class Command(BaseCommand):
    help = "Povoa o banco com dados de demonstração (contas, pets e pedidos). Idempotente."

    def handle(self, *args: object, **options: object) -> None:
        if seed():
            users = ", ".join(person.username for person in PEOPLE)
            self.stdout.write(self.style.SUCCESS(f"Semente criada. Contas: {users}. Senha: {PASSWORD}"))
        else:
            self.stdout.write("A semente já existe; nada mudou.")
