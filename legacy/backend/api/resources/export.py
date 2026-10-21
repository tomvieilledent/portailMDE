"""Monthly agenda export endpoints (super-admin)."""

from flask import request
from flask_jwt_extended import get_jwt_identity
from flask_restful import Resource

from backend.api.errors import ERROR_CODES, error_response
from backend.api.jwt_helpers import jwt_required
from backend.persistence.services import UserService
from backend.services import agenda_export

user_service = UserService()


def _require_super_admin():
    """Return the current user dict if super admin, else ``None``."""
    current = user_service.get_by_id(get_jwt_identity())
    if current and current.get('is_super_admin'):
        return current
    return None


class MonthlyExportResource(Resource):
    """List stored monthly sheets or generate one on demand."""

    @jwt_required()
    def get(self):
        """Return the list of stored monthly sheets (most recent first).

        Returns:
            tuple[dict, int]: ``{exports}`` and 200, or 403.
        """
        if not _require_super_admin():
            return error_response(ERROR_CODES['FORBIDDEN'], 'super admin only', 403)
        return {'exports': agenda_export.list_exports()}

    @jwt_required()
    def post(self):
        """Generate (or regenerate) the sheet for a given month.

        Expected JSON body (both optional; default = next month):
            year (int): Target year.
            month (int): Target month (1-12).

        Returns:
            tuple[dict, int]: ``{export}`` and 201, or 400/403.
        """
        if not _require_super_admin():
            return error_response(ERROR_CODES['FORBIDDEN'], 'super admin only', 403)
        data = request.get_json(silent=True) or {}
        default_year, default_month = agenda_export.next_month()
        try:
            year = int(data.get('year', default_year))
            month = int(data.get('month', default_month))
        except (TypeError, ValueError):
            return error_response(ERROR_CODES['BAD_REQUEST'],
                                  'year and month must be integers', 400)
        if not 1 <= month <= 12:
            return error_response(ERROR_CODES['BAD_REQUEST'],
                                  'month must be between 1 and 12', 400)
        export = agenda_export.generate_and_store(year, month)
        return {'export': export}, 201
