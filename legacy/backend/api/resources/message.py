"""Message-related API resources."""

from flask import request
from flask_jwt_extended import get_jwt_identity
from flask_restful import Resource

from backend.api.errors import ERROR_CODES, error_response
from backend.api.jwt_helpers import jwt_required
from backend.api.socket_events.message import notify_message_deleted
from backend.api.state import online_user_ids
from backend.api.uploads import save_message_attachment
from backend.models.message import Message as DomainMessage
from backend.persistence.services import ConversationService, MessageService


message_service = MessageService()
conversation_service = ConversationService()


class MessageListResource(Resource):
    """List messages, optionally filtered by conversation or author."""

    @jwt_required()
    def get(self):
        """Return messages with optional filters.

        Query parameters:
            conversation_id (str): Filter by conversation UUID.
            author_id (str): Filter by author UUID.
            limit (int): Max messages to return (default 100).

        Returns:
            tuple[dict, int]: ``{messages}`` and 200.
        """
        limit = request.args.get('limit', default=100, type=int)
        conversation_id = request.args.get('conversation_id')
        author_id = request.args.get('author_id')
        identity = get_jwt_identity()
        if conversation_id:
            if not conversation_service.facade.is_participant(conversation_id, identity):
                return error_response(ERROR_CODES['NOT_FOUND'], 'conversation not found', 404)
            return {'messages': message_service.facade.list_by_conversation(
                conversation_id, limit=limit)}
        # Otherwise a user may only read messages they authored themselves.
        if author_id and author_id != identity:
            return error_response(ERROR_CODES['FORBIDDEN'], 'forbidden', 403)
        return {'messages': message_service.facade.list_by_author(identity, limit=limit)}


class DirectMessagesResource(Resource):
    """Return the direct-message thread between the caller and another user."""

    @jwt_required()
    def get(self, user_id):
        """Return all direct messages exchanged with ``user_id``.

        Args:
            user_id (str): The other participant's UUID path parameter.

        Returns:
            tuple[dict, int]: ``{messages}`` (oldest first) and 200.
        """
        limit = request.args.get('limit', default=100, type=int)
        identity = get_jwt_identity()
        return {'messages': message_service.facade.list_direct(
            identity, user_id, limit=limit)}

    @jwt_required()
    def post(self, user_id):
        """Mark every direct message from ``user_id`` to the caller as read.

        Args:
            user_id (str): The sender's UUID path parameter.

        Returns:
            tuple[dict, int]: ``{updated}`` (count newly marked) and 200.
        """
        identity = get_jwt_identity()
        updated = message_service.facade.mark_direct_read(identity, user_id)
        return {'updated': updated}


class MessageResource(Resource):
    """Delete a single message by id."""

    @jwt_required()
    def delete(self, message_id):
        """Soft-delete a message (only its author may do so).

        Args:
            message_id (str): Message UUID path parameter.

        Returns:
            tuple[dict, int]: ``{msg}`` and 200, or 404.
        """
        message = message_service.facade.get(message_id)
        if not message:
            return error_response(ERROR_CODES['NOT_FOUND'], 'message not found', 404)
        if message.get('author_id') != get_jwt_identity():
            return error_response(ERROR_CODES['NOT_FOUND'], 'message not found', 404)
        if not message_service.facade.deactivate(message_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'message not found', 404)
        # Notify conversation members in real time so the message disappears.
        notify_message_deleted(message)
        return {'msg': 'message deleted'}


class MessageAttachmentResource(Resource):
    """Upload a file attachment for a message."""

    @jwt_required()
    def post(self):
        """Accept a multipart file upload and return its public URL.

        Returns:
            tuple[dict, int]: ``{file_url, file_name}`` and 200.
        """
        uploaded = request.files.get('file')
        if not uploaded or not uploaded.filename:
            return error_response(ERROR_CODES['VALIDATION_ERROR'], 'no file provided', 400)
        try:
            file_url, file_name = save_message_attachment(uploaded)
        except ValueError as exc:
            return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)
        return {'file_url': file_url, 'file_name': file_name}


class PresenceResource(Resource):
    """Report which users are currently connected over Socket.IO."""

    @jwt_required()
    def get(self):
        """Return the list of online user ids.

        Returns:
            tuple[dict, int]: ``{online: [user_id, ...]}`` and 200.
        """
        return {'online': online_user_ids()}


class UnreadCountResource(Resource):
    """Report the authenticated user's unread message counts."""

    @jwt_required()
    def get(self):
        """Return unread counts for the current user.

        Returns:
            tuple[dict, int]: ``{unread, conversations, direct}`` and 200.
        """
        identity = get_jwt_identity()
        conversations = conversation_service.facade.list_by_participant(
            identity, limit=1000)
        conversation_ids = [c['id'] for c in conversations]
        conversation_unread = message_service.facade.count_unread_for_conversations(
            conversation_ids, identity)
        direct_unread = message_service.facade.count_unread_dms(identity)
        return {
            'unread': conversation_unread + direct_unread,
            'conversations': conversation_unread,
            'direct': direct_unread,
            # Per-sender breakdown for direct messages (author_id -> count),
            # used by the chat UI to badge which contact has unread messages.
            'by_sender': message_service.facade.count_unread_dms_by_sender(identity),
        }


class MessageReadResource(Resource):
    """Mark a single message as read."""

    @jwt_required()
    def post(self, message_id):
        """Mark a message as read on behalf of the authenticated user.

        Args:
            message_id (str): Message UUID path parameter.

        Returns:
            tuple[dict, int]: ``{message}`` and 200, or 404.
        """
        identity = get_jwt_identity()
        message = message_service.facade.get(message_id)
        if not message:
            return error_response(ERROR_CODES['NOT_FOUND'], 'message not found', 404)
        conversation_id = message.get('conversation_id')
        if conversation_id:
            if not conversation_service.facade.is_participant(conversation_id, identity):
                return error_response(ERROR_CODES['NOT_FOUND'], 'message not found', 404)
        elif message.get('recipient_id') != identity:
            return error_response(ERROR_CODES['NOT_FOUND'], 'message not found', 404)
        return {'message': message_service.facade.mark_read(message_id, identity)}


class ConversationReadResource(Resource):
    """Mark every message in a conversation as read for the caller."""

    @jwt_required()
    def post(self, conversation_id):
        """Mark a conversation's messages as read for the current user.

        Args:
            conversation_id (str): Conversation UUID path parameter.

        Returns:
            tuple[dict, int]: ``{updated}`` and 200, or 404.
        """
        identity = get_jwt_identity()
        if not conversation_service.facade.is_participant(conversation_id, identity):
            return error_response(ERROR_CODES['NOT_FOUND'], 'conversation not found', 404)
        updated = message_service.facade.mark_conversation_read(
            conversation_id, identity)
        return {'updated': updated}


class ConversationMessagesResource(Resource):
    """List or post messages within a specific conversation."""

    @jwt_required()
    def get(self, conversation_id):
        """Return messages for a conversation in chronological order.

        Args:
            conversation_id (str): Conversation UUID path parameter.

        Query parameters:
            limit (int): Max messages to return (default 100).

        Returns:
            tuple[dict, int]: ``{messages}`` and 200.
        """
        if not conversation_service.facade.is_participant(conversation_id, get_jwt_identity()):
            return error_response(ERROR_CODES['NOT_FOUND'], 'conversation not found', 404)
        limit = request.args.get('limit', default=100, type=int)
        return {'messages': message_service.facade.list_by_conversation(
            conversation_id, limit=limit)}

    @jwt_required()
    def post(self, conversation_id):
        """Create a message in a conversation.

        Args:
            conversation_id (str): Conversation UUID path parameter.

        Expected JSON body:
            content (str): Message text.
            recipient_id (str | None): Optional direct recipient UUID.
            author_id (str | None): Optional author UUID (defaults to the
                authenticated user).

        Returns:
            tuple[dict, int]: ``{message}`` and 201.
        """
        if not conversation_service.facade.is_participant(conversation_id, get_jwt_identity()):
            return error_response(ERROR_CODES['NOT_FOUND'], 'conversation not found', 404)
        data = request.get_json(silent=True) or {}
        content = data.get('content')
        try:
            dm = DomainMessage()
            dm.content = content
        except Exception as exc:
            return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)
        message = message_service.facade.create(
            author_id=get_jwt_identity(),
            content=content,
            recipient_id=data.get('recipient_id'),
            conversation_id=conversation_id,
        )
        return {'message': message}, 201
