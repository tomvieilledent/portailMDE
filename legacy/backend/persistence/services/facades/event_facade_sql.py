"""Event persistence facade (SQLAlchemy)."""

from datetime import datetime, timezone
from typing import Any

from backend.persistence.models import Event as ORMEvent
from ._common_sql import isoformat, normalize_text, session_scope


class EventFacade:
    """SQLAlchemy-backed facade for agenda event CRUD operations."""

    def create(self, title, date, time=None, color=None, description=None,
               creator=None, created_by=None, is_public=False, **kwargs):
        with session_scope() as db:
            event = ORMEvent(
                title=normalize_text(title),
                date=normalize_text(date),
                time=normalize_text(time),
                color=normalize_text(color),
                description=normalize_text(description),
                creator=normalize_text(creator),
                created_by=created_by,
                is_public=bool(is_public),
                created_at=kwargs.get('created_at') or datetime.now(timezone.utc),
            )
            db.add(event)
            db.flush()
            db.refresh(event)
            return self._to_dict(event)

    def get(self, event_id):
        with session_scope() as db:
            event: Any = db.query(ORMEvent).filter(ORMEvent.id == event_id).first()
            return self._to_dict(event) if event else None

    def list(self, limit=500):
        """Return active events ordered by date then time.

        Args:
            limit (int): Maximum number of rows. Defaults to 500.

        Returns:
            list[dict]: Serialised event dicts.
        """
        with session_scope() as db:
            rows = (db.query(ORMEvent)
                    .filter(ORMEvent.is_active.is_(True))
                    .order_by(ORMEvent.date.asc(), ORMEvent.time.asc())
                    .limit(limit).all())
            return [self._to_dict(row) for row in rows]

    def update(self, event_id, **kwargs):
        with session_scope() as db:
            event: Any = db.query(ORMEvent).filter(ORMEvent.id == event_id).first()
            if not event:
                return None
            for field in ('title', 'date', 'time', 'color', 'description',
                          'creator'):
                if field in kwargs:
                    setattr(event, field, normalize_text(kwargs[field]))
            if 'is_public' in kwargs:
                event.is_public = bool(kwargs['is_public'])
            db.flush()
            db.refresh(event)
            return self._to_dict(event)

    def delete(self, event_id):
        """Soft-delete an event by flipping ``is_active``.

        Args:
            event_id (str): Event UUID.

        Returns:
            bool: ``True`` if found and deactivated, ``False`` otherwise.
        """
        with session_scope() as db:
            event: Any = db.query(ORMEvent).filter(ORMEvent.id == event_id).first()
            if not event:
                return False
            event.is_active = False
            return True

    def _to_dict(self, event):
        return {
            'id': event.id,
            'title': event.title,
            'date': event.date,
            'time': event.time,
            'color': event.color,
            'description': event.description,
            'creator': event.creator,
            'created_by': event.created_by,
            'is_public': bool(event.is_public),
            'created_at': isoformat(event.created_at),
        }
