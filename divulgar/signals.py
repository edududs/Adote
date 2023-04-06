from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import Raca, Tag


@receiver(post_migrate)
def inserir_racas(sender, **kwargs):
    if Raca.objects.count() == 0:
        racas = ['SRD', 'Poodle', 'Bulldog', 'Pinscher', 'Golden Retriever', 'Labrador Retriever', 'Chihuahua', 'Shih Tzu', 'Yorkshire Terrier', 'Dachshund', 'Boxer',         'Doberman', 'Rottweiler', 'Border Collie', 'Bichon Frisé', 'Schnauzer', 'Akita', 'Bernese Mountain Dog', 'Cavalier King Charles Spaniel', 'American Pit Bull Terrier', 'Pastor Alemão', 'Chow Chow', 'Pug', 'Beagle', 'Basset Hound', 'Boston Terrier', 'Bull Terrier', 'Cane Corso', 'Cocker Spaniel', 'Dálmata', 'Fila Brasileiro', 'Fox Paulistinha', 'Husky Siberiano', 'Jack Russell Terrier', 'Lhasa Apso', 'Maltês', 'Mastiff', 'Pequinês', 'Pointer', 'Poodle Toy', 'Pug', 'Shar Pei', 'Staffordshire Bull Terrier', 'Terra Nova', 'Weimaraner', 'Welsh Corgi Pembroke', 'West Highland White Terrier', 'Whippet']

        for raca in racas:
            Raca(raca=raca).save()


@receiver(post_migrate)
def inserir_tags(sender, **kwargs):
    if Tag.objects.count() == 0:
        tags = ['Sociável', 'Sociável com crianças',
                'Vacinado', 'Dócil', 'Agitado', 'Castrado']
        for tag in tags:
            Tag(tag=tag).save()
