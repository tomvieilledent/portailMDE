"""Facade for training session persistence operations."""

from datetime import datetime, timezone
from typing import Any

import uuid

from backend.persistence.models import (
    TrainingSession as ORMTrainingSession,
    FormationUser as ORMFormationUser,
)
from ._common_sql import isoformat, session_scope


class TrainingSessionFacade:
    """SQL-backed facade for training session entities."""

    def create(self, training_id, start_date, end_date, max_participants,
               location=None, link=None, created_by=None, is_public=False):
        with session_scope() as db:
            session = ORMTrainingSession(
                id=str(uuid.uuid4()),
                training_id=training_id,
                start_date=start_date,
                end_date=end_date,
                max_participants=max_participants,
                location=location,
                link=link,
                status='upcoming',
                is_public=bool(is_public),
                created_by=created_by,
                created_at=datetime.now(timezone.utc),
            )
            db.add(session)
            db.flush()
            db.refresh(session)
            return self._to_dict(session, enrolled=0)

    def get(self, session_id):
        with session_scope() as db:
            s: Any = db.query(ORMTrainingSession).filter(
                ORMTrainingSession.id == session_id).first()
            if not s:
                return None
            return self._to_dict(s, enrolled=self._enrolled_count(db, s.id))

    def list(self, training_id=None, status=None, limit=100):
        with session_scope() as db:
            q = db.query(ORMTrainingSession)
            if training_id:
                q = q.filter(ORMTrainingSession.training_id == training_id)
            if status:
                q = q.filter(ORMTrainingSession.status == status)
            rows = q.order_by(ORMTrainingSession.start_date.asc()).limit(limit).all()
            return [self._to_dict(r, enrolled=self._enrolled_count(db, r.id))
                    for r in rows]

    @staticmethod
    def _enrolled_count(db, session_id):
        return db.query(ORMFormationUser).filter(
            ORMFormationUser.session_id == session_id,
            ORMFormationUser.type == 'enrolled',
        ).count()

    def update(self, session_id, **kwargs):
        with session_scope() as db:
            s: Any = db.query(ORMTrainingSession).filter(
                ORMTrainingSession.id == session_id).first()
            if not s:
                return None
            for field in ('start_date', 'end_date', 'max_participants',
                          'location', 'link', 'status'):
                if field in kwargs:
                    setattr(s, field, kwargs[field])
            if 'is_public' in kwargs:
                s.is_public = bool(kwargs['is_public'])
            s.updated_at = datetime.now(timezone.utc)
            db.add(s)
            db.flush()
            db.refresh(s)
            return self._to_dict(s, enrolled=self._enrolled_count(db, s.id))

    def complete(self, session_id):
        """Mark session as completed and bulk-complete all enrolled users."""
        with session_scope() as db:
            s: Any = db.query(ORMTrainingSession).filter(
                ORMTrainingSession.id == session_id).first()
            if not s:
                return None
            s.status = 'completed'
            s.updated_at = datetime.now(timezone.utc)
            completed_at = s.end_date or datetime.now(timezone.utc)
            db.query(ORMFormationUser).filter(
                ORMFormationUser.session_id == session_id,
                ORMFormationUser.type == 'enrolled',
            ).update({'type': 'completed', 'completed_at': completed_at})
            db.add(s)
            db.flush()
            db.refresh(s)
            return self._to_dict(s, enrolled=self._enrolled_count(db, s.id))

    def count_enrolled(self, session_id):
        with session_scope() as db:
            return db.query(ORMFormationUser).filter(
                ORMFormationUser.session_id == session_id,
                ORMFormationUser.type == 'enrolled',
            ).count()

    def _to_dict(self, s, enrolled=0):
        return {
            'id': s.id,
            'training_id': s.training_id,
            'start_date': isoformat(s.start_date),
            'end_date': isoformat(s.end_date),
            'max_participants': s.max_participants,
            'enrolled': enrolled,
            'location': s.location,
            'link': s.link,
            'status': s.status,
            'is_public': bool(s.is_public),
            'created_by': s.created_by,
            'created_at': isoformat(s.created_at),
            'updated_at': isoformat(s.updated_at),
        }
