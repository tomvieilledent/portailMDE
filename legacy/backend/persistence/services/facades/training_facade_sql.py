"""Training persistence facade (SQLAlchemy)."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError

from backend.persistence.db import SessionLocal
from backend.persistence.models import Training as ORMTraining
from ._common_sql import from_csv, isoformat, to_csv


class TrainingFacade:
    """SQLAlchemy-backed facade for training entities."""

    def create(self, title, company_id=None, **kwargs):
        """Persist a new training.

        Args:
            title (str): Training title (stripped before storage).
            company_id (str | None): Optional owning company UUID.
            **kwargs: Optional fields — ``description``, ``picture``.

        Returns:
            dict: Newly created training as a serialisable dict.

        Raises:
            sqlalchemy.exc.IntegrityError: On database constraint violation.
        """
        db = SessionLocal()
        try:
            t = ORMTraining(
                title=title.strip(),
                company_id=company_id,
                description=kwargs.get('description'),
                picture=kwargs.get('picture'),
                category=kwargs.get('category'),
                type=kwargs.get('type') or 'formation',
                documents=to_csv(kwargs.get('documents') or []),
                created_at=datetime.now(timezone.utc),
            )
            db.add(t)
            db.commit()
            db.refresh(t)
            return self._to_dict(t)
        except IntegrityError:
            db.rollback()
            raise
        finally:
            db.close()

    def get(self, training_id):
        """Retrieve a training by primary key.

        Args:
            training_id (str): Training UUID.

        Returns:
            dict | None: Training dict, or ``None`` if not found.
        """
        db = SessionLocal()
        t: Any = db.query(ORMTraining).filter(
            ORMTraining.id == training_id).first()
        db.close()
        return self._to_dict(t) if t else None

    def list(self, limit=100):
        """Return a list of trainings.

        Args:
            limit (int): Maximum number of rows. Defaults to 100.

        Returns:
            list[dict]: Serialised training dicts.
        """
        db = SessionLocal()
        rows = db.query(ORMTraining).limit(limit).all()
        db.close()
        return [self._to_dict(r) for r in rows]

    def update(self, training_id, **kwargs):
        """Partially update a training's mutable fields.

        Args:
            training_id (str): Training UUID.
            **kwargs: Fields to update — ``title``, ``company_id``,
                ``description``, ``picture``, ``is_active``.

        Returns:
            dict | None: Updated training dict, or ``None`` if not found.
        """
        db = SessionLocal()
        try:
            training: Any = db.query(ORMTraining).filter(
                ORMTraining.id == training_id).first()
            if not training:
                return None
            for field in ('title', 'company_id', 'description', 'picture',
                          'category', 'type'):
                if field in kwargs:
                    setattr(training, field, kwargs.get(field))
            if 'documents' in kwargs:
                training.documents = to_csv(kwargs.get('documents') or [])
            if 'is_active' in kwargs:
                training.is_active = bool(kwargs.get('is_active'))
            training.updated_at = datetime.now(timezone.utc)
            db.add(training)
            db.commit()
            db.refresh(training)
            return self._to_dict(training)
        finally:
            db.close()

    def deactivate(self, training_id, by=None):
        """Soft-deactivate a training.

        Args:
            training_id (str): Training UUID.
            by (str | None): Id of the actor performing the action.

        Returns:
            dict | None: Updated training dict, or ``None`` if not found.
        """
        return self.update(training_id, is_active=False)

    def delete(self, training_id):
        """Permanently delete a training row.

        Args:
            training_id (str): Training UUID.

        Returns:
            bool: ``True`` when deleted, ``False`` when not found.
        """
        db = SessionLocal()
        try:
            training: Any = db.query(ORMTraining).filter(
                ORMTraining.id == training_id).first()
            if not training:
                return False
            db.delete(training)
            db.commit()
            return True
        finally:
            db.close()

    def _to_dict(self, t):
        return {
            'id': t.id,
            'title': t.title,
            'company_id': t.company_id,
            'description': t.description,
            'picture': t.picture,
            'category': getattr(t, 'category', None),
            'type': getattr(t, 'type', None) or 'formation',
            'documents': from_csv(getattr(t, 'documents', None)),
            'is_active': t.is_active,
            'created_at': isoformat(t.created_at),
            'updated_at': isoformat(getattr(t, 'updated_at', None)),
            'deactivate_by': getattr(t, 'deactivate_by', None),
            'delete_by': getattr(t, 'delete_by', None),
            'uploaded_at': isoformat(getattr(t, 'uploaded_at', None)),
        }
