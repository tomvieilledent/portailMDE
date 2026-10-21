"""Invitation persistence facade (SQLAlchemy).

One row per (target, invitee). Tracks RSVP status so the inviter can see who
accepted or declined.
"""

from datetime import datetime, timezone
from typing import Any

from backend.persistence.models import Invitation as ORMInvitation
from ._common_sql import isoformat, session_scope


class InvitationFacade:
    """CRUD + RSVP for invitations to events and trainings."""

    def create_many(self, target_type, target_id, target_title,
                    inviter_id, invitee_ids):
        """Create invitations for several invitees (idempotent per target).

        Skips the inviter themselves and anyone already invited to the same
        target, so re-inviting does not create duplicates.

        Returns:
            list[dict]: The invitations now existing for those invitees.
        """
        with session_scope() as db:
            existing = {
                row.invitee_id
                for row in db.query(ORMInvitation).filter(
                    ORMInvitation.target_type == target_type,
                    ORMInvitation.target_id == target_id).all()
            }
            created = []
            for invitee_id in dict.fromkeys(invitee_ids):  # de-dup, keep order
                if not invitee_id or invitee_id == inviter_id:
                    continue
                if invitee_id in existing:
                    continue
                row = ORMInvitation(
                    target_type=target_type,
                    target_id=target_id,
                    target_title=target_title,
                    inviter_id=inviter_id,
                    invitee_id=invitee_id,
                    status='pending',
                    created_at=datetime.now(timezone.utc),
                )
                db.add(row)
                created.append(row)
            db.flush()
            return [self._to_dict(r) for r in created]

    def get(self, invitation_id):
        with session_scope() as db:
            row: Any = db.query(ORMInvitation).filter(
                ORMInvitation.id == invitation_id).first()
            return self._to_dict(row) if row else None

    def list_for_invitee(self, invitee_id, limit=100):
        """Invitations addressed to a user, newest first."""
        with session_scope() as db:
            rows = db.query(ORMInvitation).filter(
                ORMInvitation.invitee_id == invitee_id).order_by(
                ORMInvitation.created_at.desc()).limit(limit).all()
            return [self._to_dict(r) for r in rows]

    def count_pending(self, invitee_id):
        """Number of invitations still awaiting a response (badge count)."""
        with session_scope() as db:
            return db.query(ORMInvitation).filter(
                ORMInvitation.invitee_id == invitee_id,
                ORMInvitation.status == 'pending').count()

    def target_ids_for_invitee(self, invitee_id, target_type):
        """Set of *target_id*s a user is invited to for a given target type.

        Used to gate visibility/access: a non-manager may only see events or
        sessions they were invited to (any RSVP status, including pending).

        Returns:
            set[str]: The target ids the invitee has an invitation for.
        """
        with session_scope() as db:
            rows = db.query(ORMInvitation.target_id).filter(
                ORMInvitation.invitee_id == invitee_id,
                ORMInvitation.target_type == target_type).all()
            return {r[0] for r in rows}

    def list_for_target(self, target_type, target_id):
        """Every invitation for a target (organizer view of responses)."""
        with session_scope() as db:
            rows = db.query(ORMInvitation).filter(
                ORMInvitation.target_type == target_type,
                ORMInvitation.target_id == target_id).order_by(
                ORMInvitation.created_at.asc()).all()
            return [self._to_dict(r) for r in rows]

    def respond(self, invitation_id, invitee_id, status):
        """Set an invitation's RSVP status. Only the invitee may respond.

        Returns:
            dict | None: Updated invitation, or ``None`` if not found / not the
                invitee.
        """
        with session_scope() as db:
            row: Any = db.query(ORMInvitation).filter(
                ORMInvitation.id == invitation_id).first()
            if not row or row.invitee_id != invitee_id:
                return None
            row.status = status
            row.is_read = True
            row.responded_at = datetime.now(timezone.utc)
            db.add(row)
            db.flush()
            return self._to_dict(row)

    def mark_all_read(self, invitee_id):
        """Mark a user's invitations as read (clears the 'new' state)."""
        with session_scope() as db:
            db.query(ORMInvitation).filter(
                ORMInvitation.invitee_id == invitee_id,
                ORMInvitation.is_read == False).update(  # noqa: E712
                {ORMInvitation.is_read: True})
            return True

    def _to_dict(self, row):
        return {
            'id': row.id,
            'target_type': row.target_type,
            'target_id': row.target_id,
            'target_title': row.target_title,
            'inviter_id': row.inviter_id,
            'invitee_id': row.invitee_id,
            'status': row.status,
            'is_read': bool(row.is_read),
            'created_at': isoformat(row.created_at),
            'responded_at': isoformat(getattr(row, 'responded_at', None)),
        }
