"""Shared request/upload helpers used across multiple API resource modules."""

from flask import request

from backend.api.uploads import delete_uploaded_file


def _request_payload():
    """Return the request body as a flat dict for both JSON and multipart."""
    if request.mimetype and request.mimetype.startswith('multipart/form-data'):
        return request.form.to_dict(flat=True)
    return request.get_json(silent=True) or {}


def _cleanup_replaced_upload(previous_path, new_path):
    """Delete the previous upload file when it has been replaced."""
    if new_path and previous_path and previous_path != new_path:
        delete_uploaded_file(previous_path)


def _can(user, permission):
    """Return ``True`` if *user* (a user dict) may perform *permission*.

    A super admin implicitly holds every permission; a staff member holds the
    explicit subset listed in their ``permissions`` list.

    Args:
        user (dict | None): The current user dict from ``UserService``.
        permission (str): One of ``backend.models.user.STAFF_PERMISSIONS``.

    Returns:
        bool: Whether the user is authorised for *permission*.
    """
    if not user:
        return False
    if user.get('is_super_admin'):
        return True
    return permission in (user.get('permissions') or [])
