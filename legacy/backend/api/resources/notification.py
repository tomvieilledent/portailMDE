"""Notification API resources."""

from flask import request
from flask_jwt_extended import get_jwt_identity
from flask_restful import Resource

from backend.api.errors import ERROR_CODES, error_response
from backend.api.jwt_helpers import jwt_required
from backend.models.notification import Notification as DomainNotification
from backend.persistence.services import NotificationService


notification_service = NotificationService()


class NotificationListResource(Resource):
    """List or create notifications."""

    @jwt_required()
    def get(self):
        """Return notifications for the current user or a specified recipient.

        Query parameters:
            recipient_id (str): Recipient UUID (defaults to authenticated user).
            is_read (str): ``"true"`` or ``"false"`` to filter by read state.
            limit (int): Max notifications to return (default 100).

        Returns:
            tuple[dict, int]: ``{notifications}`` and 200.
        """
        limit = request.args.get('limit', default=100, type=int)
        recipient_id = request.args.get('recipient_id') or get_jwt_identity()
        is_read = request.args.get('is_read')
        if recipient_id:
            notifications = notification_service.facade.list_by_recipient(
                recipient_id, limit=limit)
            if is_read in ('true', 'false'):
                want_read = is_read == 'true'
                notifications = [n for n in notifications if n['is_read'] == want_read]
            return {'notifications': notifications}
        return {'notifications': notification_service.facade.list(limit=limit)}

    @jwt_required()
    def post(self):
        """Create a notification.

        Expected JSON body:
            recipient_id (str): Recipient user UUID.
            content (str): Notification body text.

        Returns:
            tuple[dict, int]: ``{notification}`` and 201.
        """
        data = request.get_json(silent=True) or {}
        recipient_id = data.get('recipient_id')
        content = data.get('content')
        if not recipient_id or not content:
            return error_response(
                ERROR_CODES['BAD_REQUEST'],
                'recipient_id and content are required', 400)
        try:
            notification = DomainNotification()
            notification.content = content
        except Exception as exc:
            return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)
        notification = notification_service.facade.create(
            recipient_id, content, is_read=data.get('is_read', False))
        return {'notification': notification}, 201


class NotificationResource(Resource):
    """Retrieve, mark as read, or delete a single notification."""

    @jwt_required()
    def patch(self, notification_id):
        """Mark a notification as read.

        Args:
            notification_id (str): Notification UUID path parameter.

        Expected JSON body:
            is_read (bool): Must be ``true``.

        Returns:
            tuple[dict, int]: ``{notification}`` and 200, or 400/404.
        """
        data = request.get_json(silent=True) or {}
        if data.get('is_read') is True:
            if not notification_service.facade.mark_read(notification_id):
                return error_response(ERROR_CODES['NOT_FOUND'], 'notification not found', 404)
            notification = notification_service.facade.get(notification_id)
            return {'notification': notification}
        return error_response(ERROR_CODES['BAD_REQUEST'], 'nothing to update', 400)

    @jwt_required()
    def delete(self, notification_id):
        """Permanently delete a notification.

        Args:
            notification_id (str): Notification UUID path parameter.

        Returns:
            tuple[dict, int]: ``{msg}`` and 200, or 404.
        """
        if not notification_service.facade.delete(notification_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'notification not found', 404)
        return {'msg': 'notification deleted'}
