"""API resources for conversations (chat rooms)."""

from flask import request
from flask_jwt_extended import get_jwt_identity
from flask_restful import Resource

from backend.api.errors import ERROR_CODES, error_response
from backend.api.jwt_helpers import jwt_required
from backend.api.socket_events.message import (
    join_user_sockets, leave_user_sockets, notify_conversation_added,
    notify_conversation_removed, notify_conversation_updated)
from backend.models.conversation import Conversation as DomainConversation
from backend.persistence.services import ConversationService, MessageService


conversation_service = ConversationService()
message_service = MessageService()


def _enrich(conversation, user_id):
    """Augment a conversation dict with last message and unread count.

    Lets the chat inbox render WhatsApp-style rows (preview + badge)
    without an extra request per conversation.
    """
    msgs = message_service.facade.list_by_conversation(conversation['id'], limit=200)
    conversation['last_message'] = msgs[-1] if msgs else None
    conversation['unread'] = message_service.facade.count_unread_for_conversations(
        [conversation['id']], user_id)
    return conversation


class ConversationListResource(Resource):
    """List or create conversations."""

    @jwt_required()
    def get(self):
        """Return a list of conversations.

        Query parameters:
            limit (int): Max conversations to return (default 100).

        Returns:
            tuple[dict, int]: ``{conversations}`` and 200.
        """
        limit = request.args.get('limit', default=100, type=int)
        identity = get_jwt_identity()
        conversations = conversation_service.facade.list_by_participant(
            identity, limit=limit)
        conversations = [_enrich(c, identity) for c in conversations]
        return {'conversations': conversations}

    @jwt_required()
    def post(self):
        """Create a new conversation.

        Expected JSON body:
            participant_ids (list[str] | None): Initial participant UUIDs.
            title (str | None): Optional group name.

        Returns:
            tuple[dict, int]: ``{conversation}`` and 201.
        """
        data = request.get_json(silent=True) or {}
        participant_ids = data.get('participant_ids') or []
        title = data.get('title')
        try:
            domain = DomainConversation(participant_ids=participant_ids, title=title)
        except Exception as exc:
            return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)
        # Always include the creator so they don't lock themselves out.
        identity = get_jwt_identity()
        if identity not in participant_ids:
            participant_ids = [identity, *participant_ids]
        conversation = conversation_service.facade.create(
            participant_ids=participant_ids, title=domain.title,
            creator_id=identity)
        # Catch up any participants who are already online so they receive
        # this brand-new group's messages without re-opening the chat panel,
        # and push the group into their list live.
        for pid in participant_ids:
            join_user_sockets(pid, conversation['id'])
            notify_conversation_added(pid, _enrich(dict(conversation), pid))
        return {'conversation': conversation}, 201


class ConversationResource(Resource):
    """Retrieve, update or deactivate a single conversation."""

    @jwt_required()
    def get(self, conversation_id):
        """Return a conversation by id.

        Args:
            conversation_id (str): Conversation UUID path parameter.

        Returns:
            tuple[dict, int]: ``{conversation}`` and 200, or 404.
        """
        conversation = conversation_service.facade.get(conversation_id)
        if not conversation:
            return error_response(ERROR_CODES['NOT_FOUND'], 'conversation not found', 404)
        if not conversation_service.facade.is_participant(conversation_id, get_jwt_identity()):
            return error_response(ERROR_CODES['NOT_FOUND'], 'conversation not found', 404)
        return {'conversation': conversation}

    @jwt_required()
    def patch(self, conversation_id):
        """Add/remove a participant or rename a conversation.

        Args:
            conversation_id (str): Conversation UUID path parameter.

        Permissions:
            Only the group creator may rename it or add/remove other members.
            Any participant may remove *themselves* (i.e. leave the group).

        Expected JSON body (one of):
            participant_id (str) + action ("add"|"remove"): membership change.
            title (str): rename the group (empty string clears the name).

        Returns:
            tuple[dict, int]: ``{conversation}`` and 200, 403, or 404.
        """
        identity = get_jwt_identity()
        if not conversation_service.facade.is_participant(conversation_id, identity):
            return error_response(ERROR_CODES['NOT_FOUND'], 'conversation not found', 404)
        is_creator = conversation_service.facade.is_creator(conversation_id, identity)
        data = request.get_json(silent=True) or {}

        # Rename (title in payload) takes precedence over membership changes.
        if 'title' in data:
            if not is_creator:
                return error_response(
                    ERROR_CODES['FORBIDDEN'],
                    'only the group creator can rename the conversation', 403)
            try:
                domain = DomainConversation(title=data.get('title'))
            except Exception as exc:
                return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)
            conversation = conversation_service.facade.set_title(
                conversation_id, domain.title)
            if not conversation:
                return error_response(ERROR_CODES['NOT_FOUND'], 'conversation not found', 404)
            # Reflect the new name live for every member with the panel open.
            notify_conversation_updated(conversation)
            return {'conversation': conversation}

        participant_id = data.get('participant_id')
        if participant_id is not None:
            if not isinstance(participant_id, str):
                return error_response(ERROR_CODES['VALIDATION_ERROR'],
                                      'participant_id must be a string', 400)
            participant_id = participant_id.strip()
        action = data.get('action')

        # Leaving the group: any participant may remove themselves.
        is_self_leave = action == 'remove' and participant_id == identity
        if not is_self_leave and not is_creator:
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'only the group creator can manage members', 403)

        if participant_id and action == 'add':
            conversation = conversation_service.facade.add_participant(
                conversation_id, participant_id)
            # Newly added member starts receiving messages live if online, and
            # the group appears in their list without a manual refresh.
            if conversation:
                join_user_sockets(participant_id, conversation_id)
                notify_conversation_added(
                    participant_id, _enrich(dict(conversation), participant_id))
        elif participant_id and action == 'remove':
            conversation = conversation_service.facade.remove_participant(
                conversation_id, participant_id)
            # Removed member (or one who left) stops receiving messages live and
            # the group disappears from their list.
            if conversation:
                leave_user_sockets(participant_id, conversation_id)
                notify_conversation_removed(participant_id, conversation_id)
        else:
            conversation = None
        if not conversation:
            return error_response(ERROR_CODES['NOT_FOUND'], 'conversation not found', 404)
        return {'conversation': conversation}

    @jwt_required()
    def delete(self, conversation_id):
        """Soft-deactivate a conversation.

        Args:
            conversation_id (str): Conversation UUID path parameter.

        Returns:
            tuple[dict, int]: ``{msg}`` and 200, or 404.
        """
        if not conversation_service.facade.is_participant(conversation_id, get_jwt_identity()):
            return error_response(ERROR_CODES['NOT_FOUND'], 'conversation not found', 404)
        if not conversation_service.facade.deactivate(conversation_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'conversation not found', 404)
        return {'msg': 'conversation deactivated'}
