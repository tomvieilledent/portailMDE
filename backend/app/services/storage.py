"""Stockage de fichiers sur disque : validation, nommage aléatoire, suppression."""

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.errors import AppError

# Signatures (magic bytes) des images acceptées.
_IMAGE_SIGNATURES = {
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".gif": (b"GIF87a", b"GIF89a"),
    ".webp": (b"RIFF",),
}
_OLE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
# Signatures des documents binaires ; txt et csv sont contrôlés comme du texte.
_DOCUMENT_SIGNATURES = {
    ".pdf": (b"%PDF",),
    ".doc": (_OLE,),
    ".xls": (_OLE,),
    ".ppt": (_OLE,),
    ".docx": (b"PK\x03\x04",),
    ".xlsx": (b"PK\x03\x04",),
    ".pptx": (b"PK\x03\x04",),
}
PUBLIC_UPLOAD_CATEGORIES = ("avatars", "business-cards", "logos", "trainings")
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".csv"}


class UploadTooLargeError(AppError):
    """Fichier téléversé dépassant la taille maximale autorisée (413)."""

    status_code = 413
    code = "PAYLOAD_TOO_LARGE"


def upload_root() -> Path:
    """Retourne le dossier racine des fichiers téléversés (créé si besoin)."""
    root = Path(get_settings().upload_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _read_limited(file: UploadFile, limit: int) -> bytes:
    """Lit le fichier en refusant les fichiers vides ou dépassant la limite en octets."""
    data = file.file.read(limit + 1)
    if len(data) > limit:
        raise UploadTooLargeError(f"Fichier trop volumineux (maximum {limit // (1024 * 1024)} Mo)")
    if not data:
        raise AppError("Fichier vide")
    return data


def _extension(file: UploadFile) -> str:
    """Retourne l'extension du fichier en minuscules."""
    return Path(file.filename or "").suffix.lower()


def save_image(file: UploadFile, category: str) -> str:
    """Enregistre une image ; retourne le chemin relatif (ex. ``avatars/<uuid>.png``)."""
    ext = _extension(file)
    signatures = _IMAGE_SIGNATURES.get(ext)
    if not signatures:
        raise AppError("Format d'image non supporté (png, jpg, gif, webp)")
    data = _read_limited(file, get_settings().max_image_bytes)
    if not data.startswith(signatures) or (ext == ".webp" and data[8:12] != b"WEBP"):
        raise AppError("Le contenu du fichier ne correspond pas à une image valide")
    return _write(data, category, ext)


def save_document(file: UploadFile, category: str) -> tuple[str, str]:
    """Enregistre un document ou une image ; retourne ``(chemin relatif, nom d'origine)``."""
    ext = _extension(file)
    if ext in _IMAGE_SIGNATURES:
        return save_image(file, category), file.filename or ""
    if ext not in DOCUMENT_EXTENSIONS:
        raise AppError("Type de fichier non autorisé")
    data = _read_limited(file, get_settings().max_document_bytes)
    signatures = _DOCUMENT_SIGNATURES.get(ext)
    if signatures is not None:
        valid = data.startswith(signatures)
    else:  # .txt, .csv : texte UTF-8 sans octet nul
        valid = b"\x00" not in data and _is_utf8(data)
    if not valid:
        raise AppError("Le contenu du fichier ne correspond pas à son extension")
    return _write(data, category, ext), file.filename or ""


def _is_utf8(data: bytes) -> bool:
    """Indique si les octets forment un texte UTF-8 valide."""
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def _write(data: bytes, category: str, ext: str) -> str:
    """Écrit le fichier sous un nom aléatoire et retourne son chemin relatif."""
    relative = f"{category}/{uuid.uuid4().hex}{ext}"
    target = upload_root() / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return relative


def delete_file(relative: str | None) -> None:
    """Supprime un fichier stocké (sans erreur s'il n'existe plus ou sort du dossier)."""
    if not relative:
        return
    root = upload_root().resolve()
    target = (root / relative).resolve()
    if root in target.parents and target.is_file():
        target.unlink()
