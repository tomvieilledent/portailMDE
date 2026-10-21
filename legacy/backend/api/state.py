"""In-memory shared state used by JWT callbacks and Socket.IO handlers.

Exposes `BLOCKLIST` (revoked token JTIs) and live presence tracking.
In production both should be replaced by a persistent / shared store
(e.g. Redis) so they survive restarts and work across instances.
"""

BLOCKLIST = set()

# Presence: user_id -> number of currently open socket connections.
ONLINE_USERS: dict[str, int] = {}


def mark_online(user_id):
    """Register a new connection for a user.

    Returns:
        bool: ``True`` if the user just transitioned from offline to online.
    """
    count = ONLINE_USERS.get(user_id, 0)
    ONLINE_USERS[user_id] = count + 1
    return count == 0


def mark_offline(user_id):
    """Drop one connection for a user.

    Returns:
        bool: ``True`` if the user just transitioned to fully offline.
    """
    count = ONLINE_USERS.get(user_id, 0)
    if count <= 1:
        ONLINE_USERS.pop(user_id, None)
        return count == 1
    ONLINE_USERS[user_id] = count - 1
    return False


def is_online(user_id):
    """Return whether the given user has at least one open connection."""
    return user_id in ONLINE_USERS


def online_user_ids():
    """Return the list of currently connected user ids."""
    return list(ONLINE_USERS.keys())
