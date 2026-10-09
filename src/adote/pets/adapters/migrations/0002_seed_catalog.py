"""Reference data every installation needs: breeds per species and the tags a tutor picks from.

Seeded by migration, not by a post_migrate signal: it runs once, in order, and is reversible.
"""

from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps

DOG_BREEDS = (
    "SRD (vira-lata)", "Akita", "American Pit Bull Terrier", "Basset Hound", "Beagle",
    "Bernese Mountain Dog", "Bichon Frisé", "Border Collie", "Boston Terrier", "Boxer", "Bull Terrier",
    "Bulldog", "Cane Corso", "Cavalier King Charles Spaniel", "Chihuahua", "Chow Chow", "Cocker Spaniel",
    "Dachshund", "Dálmata", "Doberman", "Fila Brasileiro", "Fox Paulistinha", "Golden Retriever",
    "Husky Siberiano", "Jack Russell Terrier", "Labrador Retriever", "Lhasa Apso", "Maltês", "Mastiff",
    "Pastor Alemão", "Pequinês", "Pinscher", "Pointer", "Poodle", "Poodle Toy", "Pug", "Rottweiler",
    "Schnauzer", "Shar Pei", "Shih Tzu", "Staffordshire Bull Terrier", "Terra Nova", "Weimaraner",
    "Welsh Corgi Pembroke", "West Highland White Terrier", "Whippet", "Yorkshire Terrier",
)  # fmt: skip
CAT_BREEDS = (
    "SRD (vira-lata)", "Angorá", "Bengal", "British Shorthair", "Himalaio", "Maine Coon", "Persa",
    "Ragdoll", "Siamês", "Sphynx",
)  # fmt: skip
TAGS = (
    "Castrado", "Vacinado", "Vermifugado", "Dócil", "Agitado", "Sociável", "Sociável com crianças",
    "Sociável com outros animais", "Porte pequeno", "Porte médio", "Porte grande", "Precisa de cuidados especiais",
)  # fmt: skip


def seed(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    breed = apps.get_model("pets", "Breed")
    tag = apps.get_model("pets", "Tag")
    for species, names in (("dog", DOG_BREEDS), ("cat", CAT_BREEDS)):
        for name in names:
            breed.objects.get_or_create(species=species, name=name)
    for name in TAGS:
        tag.objects.get_or_create(name=name)


def unseed(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    apps.get_model("pets", "Breed").objects.filter(pets__isnull=True).delete()
    apps.get_model("pets", "Tag").objects.filter(pets__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("pets", "0001_initial")]

    operations = [migrations.RunPython(seed, unseed)]
