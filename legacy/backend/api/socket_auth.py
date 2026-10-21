from flask_jwt_extended import decode_token
from flask_jwt_extended.exceptions import JWTExtendedException

from backend.api.state import BLOCKLIST


def verify_token(token: str):
    """Verify a JWT token and return the identity (user id).

    Raises an exception on invalid or revoked tokens.
    """
    if not token:
        raise Exception('token missing')
    try:
        decoded = decode_token(token)
    except Exception as exc:
        raise Exception('invalid token') from exc

    jti = decoded.get('jti')
    if jti and jti in BLOCKLIST:
        raise Exception('token revoked')

    # identity is stored in 'sub' by flask-jwt-extended
    identity = decoded.get('sub') or decoded.get('identity')
    return identity
