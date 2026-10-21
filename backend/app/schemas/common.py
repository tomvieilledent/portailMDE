"""Schémas communs : pagination."""

from pydantic import BaseModel, Field


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
