from django.db.models.signals import post_migrate
from django.dispatch import receiver
from pyUFbr.baseuf import ufbr

from .models import Estado, Cidade


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

@receiver(post_migrate)
def inserir_cidades_ufbr(sender, **kwargs):
    if Cidade.objects.count() == 0:
        lista_cidades_estados = [(estado, cidade) for estado in ufbr.list_uf for cidade in ufbr.list_cidades(estado)]
        for estado, cidade in lista_cidades_estados:
            print(f"Inserindo cidade {cidade} do estado {estado}")
            estado_obj = Estado.objects.get(sigla=estado)
            Cidade.objects.create(estado=estado_obj, nome=cidade)