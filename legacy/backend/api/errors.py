"""Centralised API error codes and response helpers."""

from __future__ import annotations

from typing import Any


ERROR_CODES = {
    'BAD_REQUEST': 'BAD_REQUEST',
    'UNAUTHORIZED': 'UNAUTHORIZED',
    'FORBIDDEN': 'FORBIDDEN',
    'NOT_FOUND': 'NOT_FOUND',
    'CONFLICT': 'CONFLICT',
    'VALIDATION_ERROR': 'VALIDATION_ERROR',
    'INVALID_CREDENTIALS': 'INVALID_CREDENTIALS',
    'INVALID_TOKEN': 'INVALID_TOKEN',
    'TOKEN_EXPIRED': 'TOKEN_EXPIRED',
    'TOKEN_REVOKED': 'TOKEN_REVOKED',
    'NOT_IMPLEMENTED': 'NOT_IMPLEMENTED',
    'INTERNAL_ERROR': 'INTERNAL_ERROR',
}


def error_response(code: str, message: str, status: int = 400, details: Any = None):
    """Build a standardised JSON error payload.

    Args:
        code (str): One of the keys in :data:`ERROR_CODES`.
        message (str): Human-readable error description.
        status (int): HTTP status code to return. Defaults to 400.
        details (Any | None): Optional extra information included in the
            ``error`` object.

    Returns:
        tuple[dict, int]: JSON-serialisable payload and HTTP status code.
    """
    payload: dict[str, Any] = {'error': {'code': code, 'message': message}}
    if details is not None:
        payload['error']['details'] = details
    return payload, status
