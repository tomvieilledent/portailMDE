"""Facade for formation/user enrollment relations."""

from datetime import datetime, timezone
from typing import Any

import uuid

from backend.persistence.models import (
    FormationUser as ORMFormationUser,
    TrainingSession as ORMTrainingSession,
)
from ._common_sql import isoformat, session_scope


class FormationUserFacade:
    """Manage FormationUser relations (interest, enrollment, completion)."""

    # ------------------------------------------------------------------
    # Interest
    # ------------------------------------------------------------------

    def express_interest(self, user_id, training_id):
        """Mark interest in a training. Idempotent on the user+training pair.

        Reuses an existing row (e.g. a bookmark-only row) and upgrades it to
        ``interested`` while preserving the ``saved`` flag.
        """
        with session_scope() as db:
            existing: Any = db.query(ORMFormationUser).filter(
                ORMFormationUser.user_id == user_id,
                ORMFormationUser.training_id == training_id,
            ).first()
            if existing:
                if not existing.type:
                    existing.type = 'interested'
                    existing.enrolled_at = datetime.now(timezone.utc)
                    db.add(existing)
                    db.flush()
                    db.refresh(existing)
                return self._to_dict(existing)
            relation = ORMFormationUser(
                id=str(uuid.uuid4()),
                user_id=user_id,
                training_id=training_id,
                session_id=None,
                type='interested',
                enrolled_at=datetime.now(timezone.utc),
            )
            db.add(relation)
            db.flush()
            db.refresh(relation)
            return self._to_dict(relation)

    def remove_interest(self, user_id, training_id):
        """Clear the 'interested' state for this user+training pair.

        If the row is also saved as a bookmark, the row is kept and only its
        type is cleared; otherwise the row is deleted.
        """
        with session_scope() as db:
            relation: Any = db.query(ORMFormationUser).filter(
                ORMFormationUser.user_id == user_id,
                ORMFormationUser.training_id == training_id,
                ORMFormationUser.type == 'interested',
            ).first()
            if not relation:
                return False
            if relation.saved:
                relation.type = None
                relation.session_id = None
                db.add(relation)
            else:
                db.delete(relation)
            return True

    # ------------------------------------------------------------------
    # Bookmark (saved)
    # ------------------------------------------------------------------

    def save_training(self, user_id, training_id):
        """Bookmark a training for the user. Idempotent."""
        with session_scope() as db:
            existing: Any = db.query(ORMFormationUser).filter(
                ORMFormationUser.user_id == user_id,
                ORMFormationUser.training_id == training_id,
            ).first()
            if existing:
                if not existing.saved:
                    existing.saved = True
                    db.add(existing)
                    db.flush()
                    db.refresh(existing)
                return self._to_dict(existing)
            relation = ORMFormationUser(
                id=str(uuid.uuid4()),
                user_id=user_id,
                training_id=training_id,
                session_id=None,
                type=None,
                saved=True,
                enrolled_at=datetime.now(timezone.utc),
            )
            db.add(relation)
            db.flush()
            db.refresh(relation)
            return self._to_dict(relation)

    def unsave_training(self, user_id, training_id):
        """Remove the bookmark for this user+training pair.

        If the row carries no lifecycle state, it is deleted; otherwise only
        the ``saved`` flag is cleared.
        """
        with session_scope() as db:
            relation: Any = db.query(ORMFormationUser).filter(
                ORMFormationUser.user_id == user_id,
                ORMFormationUser.training_id == training_id,
                ORMFormationUser.saved.is_(True),
            ).first()
            if not relation:
                return False
            if relation.type:
                relation.saved = False
                db.add(relation)
            else:
                db.delete(relation)
            return True

    def list_saved(self, user_id, limit=100):
        """List the trainings bookmarked by a user, most recent first."""
        with session_scope() as db:
            rows = db.query(ORMFormationUser).filter(
                ORMFormationUser.user_id == user_id,
                ORMFormationUser.saved.is_(True),
            ).order_by(ORMFormationUser.enrolled_at.desc()).limit(limit).all()
            return [self._to_dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Enrollment
    # ------------------------------------------------------------------

    def enroll(self, user_id, training_id, session_id):
        """Enroll a user in a *session*, checking capacity and reusing interest.

        Enrollment is tracked per **session**, not per training: a user may be
        enrolled in several sessions of the same training (e.g. after accepting
        invitations to distinct dates). The "already enrolled" guard therefore
        applies to the exact session, not to any session of the training.
        """
        with session_scope() as db:
            s: Any = db.query(ORMTrainingSession).filter(
                ORMTrainingSession.id == session_id).first()
            if not s:
                return None, 'session not found'
            if s.status in ('completed', 'cancelled'):
                return None, f'session is {s.status}'
            enrolled_count = db.query(ORMFormationUser).filter(
                ORMFormationUser.session_id == session_id,
                ORMFormationUser.type == 'enrolled',
            ).count()
            if enrolled_count >= s.max_participants:
                return None, 'session is full'

            # Is there already a row pinned to this exact session?
            existing: Any = db.query(ORMFormationUser).filter(
                ORMFormationUser.user_id == user_id,
                ORMFormationUser.session_id == session_id,
            ).first()
            if existing and existing.type == 'enrolled':
                return None, 'already enrolled'
            if existing and existing.type == 'completed':
                return None, 'already completed this session'

            if existing:
                existing.type = 'enrolled'
                existing.enrolled_at = datetime.now(timezone.utc)
                relation = existing
            else:
                # Reuse a session-less interest/bookmark row for this training
                # (e.g. "interested" expressed earlier) and pin it to the
                # session, so the two states share a single row.
                placeholder: Any = db.query(ORMFormationUser).filter(
                    ORMFormationUser.user_id == user_id,
                    ORMFormationUser.training_id == training_id,
                    ORMFormationUser.session_id.is_(None),
                    ORMFormationUser.type != 'enrolled',
                ).first()
                if placeholder:
                    placeholder.session_id = session_id
                    placeholder.type = 'enrolled'
                    placeholder.enrolled_at = datetime.now(timezone.utc)
                    relation = placeholder
                else:
                    relation = ORMFormationUser(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        training_id=training_id,
                        session_id=session_id,
                        type='enrolled',
                        enrolled_at=datetime.now(timezone.utc),
                    )
                    db.add(relation)
            db.flush()
            db.refresh(relation)

            new_count = enrolled_count + 1
            if new_count >= s.max_participants:
                s.status = 'full'
                db.add(s)

            return self._to_dict(relation), None

    def unenroll(self, user_id, session_id):
        """Remove the user's enrollment in a *session* and free a full seat.

        Keyed by session (matching :meth:`enroll`): unenrolling from one
        session leaves enrollments in other sessions of the same training
        untouched.
        """
        with session_scope() as db:
            relation: Any = db.query(ORMFormationUser).filter(
                ORMFormationUser.user_id == user_id,
                ORMFormationUser.session_id == session_id,
                ORMFormationUser.type == 'enrolled',
            ).first()
            if not relation:
                return False
            db.delete(relation)
            db.flush()
            s: Any = db.query(ORMTrainingSession).filter(
                ORMTrainingSession.id == session_id).first()
            if s and s.status == 'full':
                s.status = 'upcoming'
                db.add(s)
            return True

    # ------------------------------------------------------------------
    # Completion management (admin)
    # ------------------------------------------------------------------

    def revoke_completion(self, relation_id):
        """Revert a completed enrollment back to enrolled."""
        with session_scope() as db:
            relation: Any = db.query(ORMFormationUser).filter(
                ORMFormationUser.id == relation_id,
                ORMFormationUser.type == 'completed',
            ).first()
            if not relation:
                return None
            relation.type = 'enrolled'
            relation.completed_at = None
            db.add(relation)
            db.flush()
            db.refresh(relation)
            return self._to_dict(relation)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get(self, relation_id):
        with session_scope() as db:
            relation: Any = db.query(ORMFormationUser).filter(
                ORMFormationUser.id == relation_id).first()
            return self._to_dict(relation) if relation else None

    def get_by_user_training(self, user_id, training_id):
        with session_scope() as db:
            relation: Any = db.query(ORMFormationUser).filter(
                ORMFormationUser.user_id == user_id,
                ORMFormationUser.training_id == training_id,
            ).first()
            return self._to_dict(relation) if relation else None

    def list(self, limit=100):
        with session_scope() as db:
            rows = db.query(ORMFormationUser).order_by(
                ORMFormationUser.enrolled_at.desc()).limit(limit).all()
            return [self._to_dict(r) for r in rows]

    def list_by_user(self, user_id, type_filter=None, limit=100):
        with session_scope() as db:
            q = db.query(ORMFormationUser).filter(
                ORMFormationUser.user_id == user_id)
            if type_filter:
                q = q.filter(ORMFormationUser.type == type_filter)
            rows = q.order_by(ORMFormationUser.enrolled_at.desc()).limit(limit).all()
            return [self._to_dict(r) for r in rows]

    def list_by_training(self, training_id, type_filter=None, limit=100):
        with session_scope() as db:
            q = db.query(ORMFormationUser).filter(
                ORMFormationUser.training_id == training_id)
            if type_filter:
                q = q.filter(ORMFormationUser.type == type_filter)
            rows = q.order_by(ORMFormationUser.enrolled_at.desc()).limit(limit).all()
            return [self._to_dict(r) for r in rows]

    def list_completions(self, user_id=None, limit=500):
        with session_scope() as db:
            q = db.query(ORMFormationUser).filter(
                ORMFormationUser.type == 'completed')
            if user_id:
                q = q.filter(ORMFormationUser.user_id == user_id)
            rows = q.order_by(ORMFormationUser.completed_at.desc()).limit(limit).all()
            return [self._to_dict(r) for r in rows]

    def list_interested(self, training_id=None, limit=500):
        with session_scope() as db:
            q = db.query(ORMFormationUser).filter(
                ORMFormationUser.type == 'interested')
            if training_id:
                q = q.filter(ORMFormationUser.training_id == training_id)
            rows = q.order_by(ORMFormationUser.enrolled_at.desc()).limit(limit).all()
            return [self._to_dict(r) for r in rows]

    def delete(self, relation_id):
        with session_scope() as db:
            relation: Any = db.query(ORMFormationUser).filter(
                ORMFormationUser.id == relation_id).first()
            if not relation:
                return False
            db.delete(relation)
            return True

    def _to_dict(self, relation):
        return {
            'id': relation.id,
            'user_id': relation.user_id,
            'training_id': relation.training_id,
            'session_id': relation.session_id,
            'type': relation.type,
            'saved': bool(relation.saved),
            'enrolled_at': isoformat(relation.enrolled_at),
            'completed_at': isoformat(relation.completed_at),
        }
