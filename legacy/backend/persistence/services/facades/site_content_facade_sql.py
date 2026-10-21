"""Site content persistence facade (SQLAlchemy).

Stores editable content blocks (keyed, e.g. ``'landing'``) as JSON documents,
so the admin UI can edit a whole structured block at once.
"""

import json
from typing import Any

from backend.persistence.models import SiteContent as ORMSiteContent
from ._common_sql import session_scope


class SiteContentFacade:
    """Read/write JSON content blocks keyed by name."""

    def get(self, key):
        """Return the stored content for *key* as a dict, or ``None``.

        Args:
            key (str): Content block key (e.g. ``'landing'``).

        Returns:
            dict | None: Parsed JSON document, or ``None`` if absent/invalid.
        """
        with session_scope() as db:
            row: Any = db.query(ORMSiteContent).filter(
                ORMSiteContent.key == key).first()
            if not row or not row.value:
                return None
            try:
                return json.loads(row.value)
            except (ValueError, TypeError):
                return None

    def set(self, key, data):
        """Create or update the content block for *key*.

        Args:
            key (str): Content block key.
            data (dict): JSON-serialisable document to store.

        Returns:
            dict: The stored document.
        """
        payload = json.dumps(data, ensure_ascii=False)
        with session_scope() as db:
            row: Any = db.query(ORMSiteContent).filter(
                ORMSiteContent.key == key).first()
            if row:
                row.value = payload
            else:
                row = ORMSiteContent(key=key, value=payload)
            db.add(row)
            db.flush()
            return data
