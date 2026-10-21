"""JWT decorator returning consistent JSON error responses."""

from functools import wraps

from flask_jwt_extended.exceptions import JWTExtendedException, NoAuthorizationError

from backend.api.errors import ERROR_CODES, error_response


def jwt_required(refresh: bool = False):
    """Enforce JWT presence and return structured JSON errors on failure.

    Args:
        refresh (bool): When ``True``, requires a refresh token instead of
            an access token. Defaults to ``False``.

    Returns:
        Callable: A decorator usable on Flask-RESTful resource methods.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from flask_jwt_extended import verify_jwt_in_request

            try:
                verify_jwt_in_request(refresh=refresh)
            except NoAuthorizationError as exc:
                return error_response(ERROR_CODES['UNAUTHORIZED'], str(exc), 401)
            except JWTExtendedException as exc:
                return error_response(ERROR_CODES['INVALID_TOKEN'], str(exc), 401)
            return fn(*args, **kwargs)

        return wrapper

    return decorator
