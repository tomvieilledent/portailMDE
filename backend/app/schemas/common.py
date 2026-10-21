"""Schémas communs : pagination."""

from typing import Annotated
from urllib.parse import urlsplit

from pydantic import AfterValidator, BaseModel, Field


def _check_http_url(value: str | None) -> str | None:
    """Refuse tout lien qui n'est pas http(s) (ex. ``javascript:``), pour éviter le XSS stocké."""
    if value is None or value == "":
        return value
    parts = urlsplit(value.strip())
    if parts.scheme.lower() not in ("http", "https") or not parts.netloc:
        raise ValueError("L'URL doit commencer par http:// ou https://")
    return value.strip()


HttpUrlStr = Annotated[str, AfterValidator(_check_http_url)]


class Page[T](BaseModel):
    """Réponse paginée standard."""

    items: list[T]
    total: int
    limit: int
    offset: int


class PageParams(BaseModel):
    """Paramètres de pagination."""

    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)
