"""Small SQL helper utilities shared across all persistence facades."""

from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterable, List, Optional

from backend.persistence.db import SessionLocal


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations.

    Commits on clean exit and rolls back on any exception, then always
    closes the session.

    Yields:
        sqlalchemy.orm.Session: A session bound to the configured engine.

    Raises:
        Exception: Re-raises any exception that occurs inside the block
            after rolling back.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def isoformat(value: Any) -> Optional[str]:
    """Return an ISO 8601 string for datetimes, pass-through otherwise.

    Args:
        value (Any): Value to convert. ``datetime`` instances are formatted;
            ``None`` is returned as ``None``.

    Returns:
        str | None: ISO-formatted string, or ``None`` when *value* is ``None``.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def normalize_text(value: Optional[str]) -> Optional[str]:
    """Strip a string value or return ``None`` when input is ``None``.

    Args:
        value (str | None): Text to normalise. Non-string values are returned
            unchanged.

    Returns:
        str | None: Stripped string, or ``None``.
    """
    if value is None:
        return None
    return value.strip() if isinstance(value, str) else value


def to_csv(values: Optional[Iterable]) -> Optional[str]:
    """Serialise an iterable of values to a comma-separated string.

    Args:
        values (Iterable | None): Items to join. Empty input returns ``None``.

    Returns:
        str | None: Comma-separated string, or ``None`` for empty/falsy input.
    """
    if not values:
        return None
    return ",".join(str(item).strip() for item in values if str(item).strip())


def from_csv(value: Optional[str]) -> List[str]:
    """Parse a comma-separated string back to a list of non-empty items.

    Args:
        value (str | None): Comma-separated string. Falsy input returns ``[]``.

    Returns:
        list[str]: List of non-empty stripped tokens.
    """
    if not value:
        return []
    return [item for item in value.split(",") if item]
