from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import Estado


@receiver(post_migrate)
def inserir_estados(sender, **kwargs):
    if Estado.objects.count() == 0:
        estados = (('AC', 'Acre'),
                   ('AL', 'Alagoas'),
                   ('AP', 'Amapá'),
                   ('AM', 'Amazonas'),
                   ('BA', 'Bahia'),
                   ('CE', 'Ceará'),
                   ('DF', 'Distrito Federal'),
                   ('ES', 'Espírito Santo'),
                   ('GO', 'Goiás'),
                   ('MA', 'Maranhão'),
                   ('MT', 'Mato Grosso'),
                   ('MS', 'Mato Grosso do Sul'),
                   ('MG', 'Minas Gerais'),
                   ('PA', 'Pará'),
                   ('PB', 'Paraíba'),
                   ('PR', 'Paraná'),
                   ('PE', 'Pernambuco'),
                   ('PI', 'Piauí'),
                   ('RJ', 'Rio de Janeiro'),
                   ('RN', 'Rio Grande do Norte'),
                   ('RS', 'Rio Grande do Sul'),
                   ('RO', 'Rondônia'),
                   ('RR', 'Roraima'),
                   ('SC', 'Santa Catarina'),
                   ('SP', 'São Paulo'),
                   ('SE', 'Sergipe'),
                   ('TO', 'Tocantins'))
        for sigla, estado in estados:
            Estado.objects.create(sigla=sigla, nome=estado)
