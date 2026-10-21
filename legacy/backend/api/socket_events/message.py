from flask import request
from flask_socketio import emit, join_room, leave_room
# socket auth helper verifies JWT for socket connections
from backend.api.socket_auth import verify_token
from backend.api.sockets import socketio
from backend.api.state import mark_offline, mark_online, online_user_ids
from backend.persistence.services import MessageService
from backend.persistence.services.facades import ConversationFacade
# Use the built-in ConnectionRefusedError exception


connected_users = {}
# Membership is read from the conversation's participant_ids CSV (source of
# truth), which is what the REST API writes — not the conversation_participants
# table, which the public API never populates.
conversation_facade = ConversationFacade()
message_service = MessageService()


def conversation_room(conversation_id):
    return f"conversation:{conversation_id}"


def user_room(user_id):
    """Personal room a user auto-joins on connect, used for direct messages.

    Joining ``user:<id>`` lets us deliver 1-to-1 messages (and read
    receipts) to every device the user is connected from.
    """
    return f"user:{user_id}"


def join_user_sockets(user_id, conversation_id):
    """Add all of an *already-connected* user's sockets to a conversation room.

    Called from the REST layer when a conversation is created or a participant
    is added, so a user who is online but has never opened the chat panel still
    starts receiving group messages (and notifications) immediately — without
    waiting for them to emit ``join_conversation``. ``handle_connect`` only
    auto-joins the rooms that exist at connection time, so newly created groups
    need this catch-up.
    """
    if not user_id or not conversation_id:
        return
    room = conversation_room(conversation_id)
    for sid, uid in list(connected_users.items()):
        if uid == user_id:
            socketio.server.enter_room(sid, room, namespace='/')


def leave_user_sockets(user_id, conversation_id):
    """Remove a connected user's sockets from a conversation room.

    Mirror of :func:`join_user_sockets`, called when a participant is removed
    (or leaves) so they immediately stop receiving the group's messages.
    """
    if not user_id or not conversation_id:
        return
    room = conversation_room(conversation_id)
    for sid, uid in list(connected_users.items()):
        if uid == user_id:
            socketio.server.leave_room(sid, room, namespace='/')


def notify_invitation(invitee_id, invitation):
    """Push a new invitation to an invitee in real time (notification bell).

    Delivered on the personal room (always joined at connect), so the bell
    updates live without a refresh.
    """
    if not invitee_id or not invitation:
        return
    socketio.emit('invitation', {'invitation': invitation},
                  to=user_room(invitee_id))


def notify_conversation_added(user_id, conversation):
    """Tell a user (on all their devices) that a group was added for them.

    Lets an open chat panel insert the new group into its list live, instead of
    only seeing it after a manual refresh. Delivered on the personal room, which
    is always joined at connect, so it reaches the user even before they are in
    the conversation room itself.
    """
    if not user_id or not conversation:
        return
    socketio.emit('conversation_added', {'conversation': conversation},
                  to=user_room(user_id))


def notify_conversation_removed(user_id, conversation_id):
    """Tell a user that a group was removed for them (they left / were removed).

    Lets an open chat panel drop the group from its list live.
    """
    if not user_id or not conversation_id:
        return
    socketio.emit('conversation_removed', {'conversation_id': conversation_id},
                  to=user_room(user_id))


def notify_conversation_updated(conversation):
    """Broadcast a group metadata change (e.g. a rename) to its room.

    Members with the chat panel open update the displayed group name live.
    """
    if not conversation:
        return
    socketio.emit('conversation_updated', {'conversation': conversation},
                  to=conversation_room(conversation['id']))


def notify_message_deleted(message):
    """Broadcast a ``message_deleted`` event for a (soft-)deleted message.

    Conversation messages are announced to the conversation room; direct
    messages are announced to both parties' personal rooms. Called from the
    REST delete handler so connected clients drop the message live.
    """
    conversation_id = message.get('conversation_id')
    if conversation_id:
        socketio.emit('message_deleted',
                      {'message_id': message['id'], 'conversation_id': conversation_id},
                      to=conversation_room(conversation_id))
        return
    for uid in (message.get('recipient_id'), message.get('author_id')):
        if uid:
            socketio.emit('message_deleted', {'message_id': message['id']},
                          to=user_room(uid))


@socketio.on("connect")
def handle_connect(auth):
    if not auth:
        raise ConnectionRefusedError("auth missing")

    token = auth.get("token")
    if not token:
        raise ConnectionRefusedError("token missing")

    try:
        user_id = verify_token(token)
    except Exception:
        raise ConnectionRefusedError("invalid token")

    if not user_id:
        raise ConnectionRefusedError("invalid token")

    sid = request.sid  # type: ignore[attr-defined]
    connected_users[sid] = user_id
    # Join a personal room so direct messages reach all of the user's devices.
    join_room(user_room(user_id))
    # Auto-join every group conversation the user belongs to, so group
    # messages reach them in real time (badges, toasts) even before they
    # open the chat panel — mirroring the always-on DM personal room.
    try:
        for conv in conversation_facade.list_by_participant(user_id):
            join_room(conversation_room(conv['id']))
    except Exception as exc:
        print('Failed to auto-join conversation rooms:', exc)
    # Announce presence only on the first connection for this user.
    if mark_online(user_id):
        socketio.emit('presence', {'user_id': user_id, 'online': True})
    print(f"Client connecté : user={user_id}, sid={sid}")


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid  # type: ignore[attr-defined]
    user_id = connected_users.pop(sid, None)
    # Announce going offline only when the user's last connection drops.
    if user_id and mark_offline(user_id):
        socketio.emit('presence', {'user_id': user_id, 'online': False})
    print(f"Client déconnecté : user={user_id}, sid={sid}")


@socketio.on("join_conversation")
def handle_join_conversation(data):
    conversation_id = (data or {}).get('conversation_id')
    if not conversation_id:
        return
    sid = request.sid  # type: ignore[attr-defined]
    user_id = connected_users.get(sid)
    if not user_id:
        return
    if not conversation_facade.is_participant(conversation_id, user_id):
        emit('error', {'message': 'not a participant in this conversation'}, to=sid)
        return
    room = conversation_room(conversation_id)
    join_room(room)
    print(f"User {user_id} joined room {room}")
    emit('joined_conversation', {'conversation_id': conversation_id}, to=sid)


@socketio.on("leave_conversation")
def handle_leave_conversation(data):
    conversation_id = (data or {}).get('conversation_id')
    if not conversation_id:
        return
    sid = request.sid  # type: ignore[attr-defined]
    user_id = connected_users.get(sid)
    if not user_id:
        return
    room = conversation_room(conversation_id)
    leave_room(room)
    print(f"User {user_id} left room {room}")
    emit('left_conversation', {'conversation_id': conversation_id}, to=sid)


@socketio.on("typing")
def handle_typing(data):
    """Relay a typing indicator to the other participants.

    Payload: ``{conversation_id|recipient_id, is_typing}``. The notice is
    never echoed back to the sender.
    """
    sid = request.sid  # type: ignore[attr-defined]
    user_id = connected_users.get(sid)
    if not user_id:
        return
    payload = data or {}
    is_typing = bool(payload.get('is_typing'))
    conversation_id = payload.get('conversation_id')
    recipient_id = payload.get('recipient_id')

    if conversation_id:
        if not conversation_facade.is_participant(conversation_id, user_id):
            return
        emit('typing',
             {'conversation_id': conversation_id, 'user_id': user_id, 'is_typing': is_typing},
             to=conversation_room(conversation_id), include_self=False)
    elif recipient_id:
        socketio.emit('typing', {'user_id': user_id, 'is_typing': is_typing},
                      to=user_room(recipient_id))


@socketio.on("who_is_online")
def handle_who_is_online():
    """Return the list of currently connected user ids to the requester."""
    sid = request.sid  # type: ignore[attr-defined]
    if not connected_users.get(sid):
        return
    emit('online_users', {'user_ids': online_user_ids()}, to=sid)


@socketio.on("send_message")
def handle_send_message(data):
    sid = request.sid  # type: ignore[attr-defined]
    user_id = connected_users.get(sid)
    if not user_id:
        return
    payload = data or {}
    content = payload.get('content', '').strip()
    file_url = payload.get('file_url')
    file_name = payload.get('file_name')
    conversation_id = payload.get('conversation_id')
    recipient_id = payload.get('recipient_id')
    # A message must have either text content or an attachment.
    if not content and not file_url:
        return
    # Use the filename as content when the user sends a file without a caption.
    if not content and file_name:
        content = file_name
    if conversation_id and not conversation_facade.is_participant(conversation_id, user_id):
        emit('error', {'message': 'not a participant in this conversation'}, to=sid)
        return

    if not conversation_id and not recipient_id:
        emit('error', {'message': 'recipient_id or conversation_id required'}, to=sid)
        return

    try:
        message = message_service.facade.create(
            author_id=user_id,
            content=content,
            recipient_id=recipient_id,
            conversation_id=conversation_id,
            file_url=file_url,
            file_name=file_name,
        )
    except Exception as exc:
        print('Failed to persist message:', exc)
        return

    if conversation_id:
        room = conversation_room(conversation_id)
        socketio.emit('new_message', {'message': message}, to=room)
    else:
        # Direct message: deliver to the recipient and back to the author's
        # own devices via their personal rooms.
        socketio.emit('new_message', {'message': message}, to=user_room(recipient_id))
        socketio.emit('new_message', {'message': message}, to=user_room(user_id))


@socketio.on("mark_read")
def handle_mark_read(data):
    """Mark messages as read and broadcast a read receipt.

    Payload accepts either ``conversation_id`` (marks the whole conversation
    read for the caller) or ``message_id`` (marks a single direct message).
    """
    sid = request.sid  # type: ignore[attr-defined]
    user_id = connected_users.get(sid)
    if not user_id:
        return
    payload = data or {}
    conversation_id = payload.get('conversation_id')
    message_id = payload.get('message_id')

    if conversation_id:
        if not conversation_facade.is_participant(conversation_id, user_id):
            emit('error', {'message': 'not a participant in this conversation'}, to=sid)
            return
        updated = message_service.facade.mark_conversation_read(conversation_id, user_id)
        if updated:
            socketio.emit('messages_read',
                          {'conversation_id': conversation_id, 'reader_id': user_id},
                          to=conversation_room(conversation_id))
        return

    if message_id:
        message = message_service.facade.mark_read(message_id, user_id)
        if not message:
            return
        # Notify the original author (on their personal room) that it was read.
        socketio.emit('messages_read',
                      {'message_id': message_id, 'reader_id': user_id},
                      to=user_room(message['author_id']))
