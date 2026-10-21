"""Recherche textuelle insensible à la casse et aux accents (« développeur » = « developpeur »)."""

import unicodedata

from sqlalchemy import func

_ACCENTED = "àáâãäåçèéêëìíîïñòóôõöùúûüýÿ"
_PLAIN = "aaaaaaceeeeiiiinooooouuuuyy"


def fold(text: str) -> str:
    """Minuscules sans accents ; œ et æ sont éclatés (œ → oe, æ → ae)."""
    text = text.strip().lower().replace("œ", "oe").replace("æ", "ae")
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def contains(column, search: str):
    """Condition SQL « la colonne contient ``search`` », sans tenir compte de la casse ni des accents."""
    folded = func.translate(func.lower(func.coalesce(column, "")), _ACCENTED, _PLAIN)
    return folded.like(f"%{fold(search)}%")
