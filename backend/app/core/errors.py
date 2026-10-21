"""Erreurs applicatives et réponses JSON uniformes.

Toutes les erreurs ont la forme ``{"error": {"code", "message", "details"}}``.
"""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = HTTPStatus.BAD_REQUEST
    code = "BAD_REQUEST"

    def __init__(self, message: str, details: object = None):
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND
    code = "NOT_FOUND"


class ConflictError(AppError):
    status_code = HTTPStatus.CONFLICT
    code = "CONFLICT"


class UnauthorizedError(AppError):
    status_code = HTTPStatus.UNAUTHORIZED
    code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    status_code = HTTPStatus.FORBIDDEN
    code = "FORBIDDEN"


def error_response(status: int, code: str, message: str, details: object = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "details": details}},
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return error_response(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException):
        code = HTTPStatus(exc.status_code).name
        return error_response(exc.status_code, code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        details = [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]
        return error_response(422, "VALIDATION_ERROR", "Requête invalide", details)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception):
        logger.exception("Erreur non gérée", exc_info=exc)
        return error_response(500, "INTERNAL_ERROR", "Erreur interne du serveur")
