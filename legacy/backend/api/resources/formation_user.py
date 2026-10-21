"""Endpoints for managing formation-user relations (admin only)."""

from flask import request
from flask_jwt_extended import get_jwt_identity
from flask_restful import Resource

from backend.api.errors import ERROR_CODES, error_response
from backend.api.jwt_helpers import jwt_required
from backend.persistence.services import FormationUserService, UserService


formation_service = FormationUserService()
user_service = UserService()


class FormationUserListResource(Resource):
    """List all formation-user relations (super admin only)."""

    @jwt_required()
    def get(self):
        """Return all formation-user relations.

        Query parameters:
            limit (int): Max rows to return (default 100).

        Returns:
            tuple[dict, int]: ``{formation_users}`` and 200, or 403.
        """
        current_user = user_service.get_by_id(get_jwt_identity())
        if not current_user or not current_user.get('is_super_admin'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'only super admins can list all relations', 403)
        limit = request.args.get('limit', default=100, type=int)
        return {'formation_users': formation_service.facade.list(limit=limit)}


class FormationUserResource(Resource):
    """Retrieve, revoke completion, or delete a formation-user relation."""

    @jwt_required()
    def get(self, relation_id):
        """Return a formation-user relation by id.

        Args:
            relation_id (str): FormationUser UUID path parameter.

        Returns:
            tuple[dict, int]: ``{formation_user}`` and 200, or 404.
        """
        relation = formation_service.facade.get(relation_id)
        if not relation:
            return error_response(ERROR_CODES['NOT_FOUND'], 'enrollment not found', 404)
        return {'formation_user': relation}

    @jwt_required()
    def patch(self, relation_id):
        """Revoke a completed enrollment, setting it back to enrolled.

        Only super admins can perform this operation. Used when an admin
        determines a user was marked as completed in error (absent).

        Args:
            relation_id (str): FormationUser UUID path parameter.

        Returns:
            tuple[dict, int]: ``{formation_user}`` and 200, or 403/404.
        """
        current_user = user_service.get_by_id(get_jwt_identity())
        if not current_user or not current_user.get('is_super_admin'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'only super admins can revoke completions', 403)
        result = formation_service.facade.revoke_completion(relation_id)
        if not result:
            return error_response(
                ERROR_CODES['NOT_FOUND'],
                'completed enrollment not found', 404)
        return {'formation_user': result}

    @jwt_required()
    def delete(self, relation_id):
        """Permanently delete a formation-user relation.

        Args:
            relation_id (str): FormationUser UUID path parameter.

        Returns:
            tuple[dict, int]: ``{msg}`` and 200, or 403/404.
        """
        current_user = user_service.get_by_id(get_jwt_identity())
        if not current_user or not current_user.get('is_super_admin'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'only super admins can delete relations', 403)
        if not formation_service.facade.delete(relation_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'enrollment not found', 404)
        return {'msg': 'enrollment deleted'}
