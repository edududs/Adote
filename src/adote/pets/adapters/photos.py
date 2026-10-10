from pathlib import PurePath
from uuid import uuid4

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

FOLDER = "pets"


class DjangoPhotoStore:
    """Photos on Django's default storage, under a random name: the uploaded name is never trusted."""

    def save(self, filename: str, content: bytes) -> str:
        suffix = PurePath(filename).suffix.lower()
        return default_storage.save(f"{FOLDER}/{uuid4().hex}{suffix}", ContentFile(content))

    def delete(self, key: str) -> None:
        if key:
            default_storage.delete(key)
