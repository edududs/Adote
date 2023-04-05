from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import Raca, Tag


@receiver(post_migrate)
def inserir_racas(sender, **kwargs):
    if Raca.objects.count() == 0:
        racas = ['SRD', 'Poodle', 'Bulldog', 'Pinscher', 'Golden Retriever', 'Labrador Retriever', 'Chihuahua', 'Shih Tzu', 'Yorkshire Terrier', 'Dachshund', 'Boxer',
                 'Doberman', 'Rottweiler', 'Border Collie', 'Bichon Frisé', 'Schnauzer', 'Akita', 'Bernese Mountain Dog', 'Cavalier King Charles Spaniel', 'American Pit Bull Terrier']
        for raca in racas:
            Raca(raca=raca).save()


@receiver(post_migrate)
def inserir_tags(sender, **kwargs):
    if Tag.objects.count() == 0:
        tags = ['Sociável', 'Sociável com crianças',
                'Vacinado', 'Dócil', 'Agitado', 'Castrado']
        for tag in tags:
            Tag(tag=tag).save()
