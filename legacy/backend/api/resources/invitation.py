"""Invitation API resources (RSVP for events and trainings)."""

from flask import request
from flask_jwt_extended import get_jwt_identity
from flask_restful import Resource

from backend.api.errors import ERROR_CODES, error_response
from backend.api.jwt_helpers import jwt_required
from backend.api.socket_events.message import notify_invitation
from backend.persistence.services import (
    FormationUserService,
    InvitationService,
    TrainingSessionService,
    UserService,
)


invitation_service = InvitationService()
user_service = UserService()
session_service = TrainingSessionService()
formation_service = FormationUserService()

TARGET_TYPES = ('event', 'training', 'session')
RSVP_STATUSES = ('accepted', 'declined')


class InvitationListResource(Resource):
    """Create invitations for an event or training."""

    @jwt_required()
    def post(self):
        """Invite users to a target. Any authenticated user (the inviter) may.

        Expected JSON body:
            target_type (str): ``'event'`` or ``'training'``.
            target_id (str): UUID of the event/training.
            target_title (str | None): Title shown in the invitation.
            invitee_ids (list[str] | None): Users to invite.
            all (bool): When true, invite every other active user.

        Returns:
            tuple[dict, int]: ``{invitations}`` (newly created) and 201.
        """
        data = request.get_json(silent=True) or {}
        target_type = data.get('target_type')
        target_id = data.get('target_id')
        if target_type not in TARGET_TYPES:
            return error_response(ERROR_CODES['BAD_REQUEST'],
                                  'target_type must be event, training or session', 400)
        if not target_id:
            return error_response(ERROR_CODES['BAD_REQUEST'], 'target_id is required', 400)

        inviter_id = get_jwt_identity()
        if data.get('all'):
            invitee_ids = [u['id'] for u in user_service.list_users(limit=1000)
                           if u.get('is_active', True) and u['id'] != inviter_id]
        else:
            invitee_ids = data.get('invitee_ids') or []
            if not isinstance(invitee_ids, list):
                return error_response(ERROR_CODES['BAD_REQUEST'],
                                      'invitee_ids must be a list', 400)

        created = invitation_service.facade.create_many(
            target_type=target_type,
            target_id=target_id,
            target_title=data.get('target_title'),
            inviter_id=inviter_id,
            invitee_ids=invitee_ids,
        )
        for inv in created:
            notify_invitation(inv['invitee_id'], inv)
        return {'invitations': created}, 201

    @jwt_required()
    def get(self):
        """Return invitations for a target (organizer view of responses).

        Query parameters:
            target_type (str), target_id (str): The target to inspect.

        Only the inviter (or a super admin) may view a target's responses.

        Returns:
            tuple[dict, int]: ``{invitations}`` and 200, or 400/403.
        """
        target_type = request.args.get('target_type')
        target_id = request.args.get('target_id')
        if target_type not in TARGET_TYPES or not target_id:
            return error_response(ERROR_CODES['BAD_REQUEST'],
                                  'target_type and target_id are required', 400)
        invitations = invitation_service.facade.list_for_target(target_type, target_id)
        current = user_service.get_by_id(get_jwt_identity())
        is_super = bool(current and current.get('is_super_admin'))
        is_inviter = any(inv['inviter_id'] == get_jwt_identity() for inv in invitations)
        if not is_super and not is_inviter:
            return error_response(ERROR_CODES['FORBIDDEN'],
                                  'not allowed to view these invitations', 403)
        return {'invitations': invitations}


class CurrentUserInvitationsResource(Resource):
    """List the current user's received invitations (notification bell)."""

    @jwt_required()
    def get(self):
        """Return the caller's invitations and their pending count."""
        identity = get_jwt_identity()
        invitations = invitation_service.facade.list_for_invitee(identity)
        pending = invitation_service.facade.count_pending(identity)
        return {'invitations': invitations, 'pending': pending}

    @jwt_required()
    def post(self):
        """Mark all of the caller's invitations as read (clears the badge dot)."""
        invitation_service.facade.mark_all_read(get_jwt_identity())
        return {'msg': 'invitations marked read'}


class InvitationResource(Resource):
    """Respond to a single invitation (accept / decline)."""

    @jwt_required()
    def patch(self, invitation_id):
        """Set the RSVP status. Only the invitee may respond.

        Expected JSON body:
            status (str): ``'accepted'`` or ``'declined'``.

        Returns:
            tuple[dict, int]: ``{invitation}`` and 200, or 400/404.
        """
        data = request.get_json(silent=True) or {}
        status = data.get('status')
        if status not in RSVP_STATUSES:
            return error_response(ERROR_CODES['BAD_REQUEST'],
                                  'status must be accepted or declined', 400)
        invitation = invitation_service.facade.respond(
            invitation_id, get_jwt_identity(), status)
        if not invitation:
            return error_response(ERROR_CODES['NOT_FOUND'], 'invitation not found', 404)

        # Accepting a session invitation enrolls the invitee in that session
        # (so the counter increments and they can no longer self-enroll);
        # declining removes any enrollment created by a previous acceptance.
        if invitation['target_type'] == 'session':
            sess = session_service.facade.get(invitation['target_id'])
            if sess:
                if status == 'accepted':
                    # Ignore "already enrolled"/"session full" — the RSVP stands.
                    formation_service.facade.enroll(
                        invitation['invitee_id'], sess['training_id'], sess['id'])
                elif status == 'declined':
                    formation_service.facade.unenroll(
                        invitation['invitee_id'], sess['id'])
        return {'invitation': invitation}
