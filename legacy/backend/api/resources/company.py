"""Company-related API resources."""

import uuid

from flask import request
from flask_jwt_extended import get_jwt_identity
from flask_restful import Resource

from backend.api.errors import ERROR_CODES, error_response
from backend.api.jwt_helpers import jwt_required
from backend.api.uploads import save_image_upload
from backend.api.resources._helpers import _can, _cleanup_replaced_upload, _request_payload
from backend.models.company import Company as DomainCompany
from backend.persistence.services import CompanyService, UserService


company_service = CompanyService()
user_service = UserService()


def _administers_active_company(user_id, exclude_company_id=None):
    """Return an active company *user_id* administers (by ``admin_id``), if any.

    Used to prevent detaching an admin from their company, which would leave it
    without an administrator. ``exclude_company_id`` skips the company we are
    (re)assigning them to.
    """
    if not user_id:
        return None
    for company in company_service.facade.list(limit=1000):
        if (company.get('admin_id') == user_id
                and company.get('is_active')
                and company.get('id') != exclude_company_id):
            return company
    return None


def _extract_company_picture(payload):
    uploaded_file = (request.files.get('company_picture_file')
                     or request.files.get('company_picture'))
    if uploaded_file and uploaded_file.filename:
        return save_image_upload(uploaded_file, 'companies')
    return payload.get('company_picture')


class CompanyListResource(Resource):
    """List companies or create a new one."""

    @jwt_required()
    def get(self):
        """Return a list of companies.

        Query parameters:
            limit (int): Max companies to return (default 100).

        Returns:
            tuple[dict, int]: ``{companies}`` and 200.
        """
        limit = request.args.get('limit', default=100, type=int)
        return {'companies': company_service.facade.list(limit=limit)}

    @jwt_required()
    def post(self):
        """Create a company.

        Expected JSON body:
            name (str): Company display name.
            admin_email (str): Email of the admin user.
            description (str | None): Optional description.
            website_link (str | None): Optional website URL.
            admin_id (str | None): Optional explicit admin UUID.

        Returns:
            tuple[dict, int]: ``{company}`` and 201.
        """
        current = user_service.get_by_id(get_jwt_identity())
        if not _can(current, 'manage_companies'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'not allowed to create companies', 403)
        data = _request_payload()
        name = data.get('name')
        admin_email = data.get('admin_email')
        if not name:
            return error_response(ERROR_CODES['BAD_REQUEST'], 'name is required', 400)
        if not admin_email:
            return error_response(ERROR_CODES['BAD_REQUEST'], 'admin_email is required', 400)
        admin_id = data.get('admin_id')
        if admin_id:
            try:
                uuid.UUID(str(admin_id))
            except Exception:
                return error_response(ERROR_CODES['VALIDATION_ERROR'], 'Admin ID must be a valid UUID', 400)

        company_picture = _extract_company_picture(data)

        try:
            domain = DomainCompany(
                name=name,
                description=data.get('description'),
                location=data.get('location'),
                website_link=data.get('website_link'),
                company_picture=company_picture,
                admin_email=admin_email,
                admin_id=admin_id,
                kind=data.get('kind', 'company'),
            )
        except Exception as exc:
            return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)
        try:
            company = company_service.facade.create(
                name,
                admin_email=admin_email,
                admin_id=admin_id,
                description=data.get('description'),
                location=data.get('location'),
                website_link=domain.website_link,
                company_picture=company_picture,
                kind=domain.kind,
                # A super admin keeps full control and may reuse an admin.
                enforce_single_admin=not current.get('is_super_admin'),
            )
        except ValueError as exc:
            return error_response(ERROR_CODES['BAD_REQUEST'], str(exc), 400)
        except Exception as exc:
            return error_response(ERROR_CODES['CONFLICT'], 'could not create company', 409, str(exc))
        return {'company': company}, 201


class CompanyResource(Resource):
    """Retrieve, update or deactivate a single company."""

    @jwt_required()
    def get(self, company_id):
        """Return company details.

        Args:
            company_id (str): Company UUID path parameter.

        Returns:
            tuple[dict, int]: ``{company}`` and 200, or 404.
        """
        company = company_service.facade.get(company_id)
        if not company:
            return error_response(ERROR_CODES['NOT_FOUND'], 'company not found', 404)
        return {'company': company}

    @jwt_required()
    def patch(self, company_id):
        """Partially update a company's fields.

        Args:
            company_id (str): Company UUID path parameter.

        Returns:
            tuple[dict, int]: ``{company}`` and 200.
        """
        data = _request_payload()
        update_data: dict[str, object] = {}

        current = company_service.facade.get(company_id)
        if not current:
            return error_response(ERROR_CODES['NOT_FOUND'], 'company not found', 404)
        # Seuls un super admin ou un responsable de cette entreprise peuvent
        # modifier sa fiche.
        current_user = user_service.get_by_id(get_jwt_identity())
        if not _can_manage_company(current_user, current):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'not allowed to edit this company', 403)
        previous_company_picture = current.get('company_picture')

        try:
            domain = DomainCompany(
                name=current.get('name'),
                description=current.get('description'),
                location=current.get('location'),
                website_link=current.get('website_link'),
                company_picture=current.get('company_picture'),
                admin_email=current.get('admin_email'),
                admin_id=current.get('admin_id'),
            )
            for k, v in data.items():
                if hasattr(domain, k):
                    setattr(domain, k, v)
            uploaded_file = (request.files.get('company_picture_file')
                             or request.files.get('company_picture'))
            if uploaded_file and uploaded_file.filename:
                update_data['company_picture'] = save_image_upload(uploaded_file, 'companies')
            elif 'company_picture' in data:
                update_data['company_picture'] = data.get('company_picture')
            for field in ('name', 'description', 'location', 'website_link',
                          'admin_email', 'admin_id', 'is_active'):
                if field in data:
                    update_data[field] = data.get(field)
            if 'kind' in data:
                update_data['kind'] = domain.kind
            # Persist the normalized link (scheme added if the user omitted it).
            if 'website_link' in data:
                update_data['website_link'] = domain.website_link
        except Exception as exc:
            return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)

        company = company_service.facade.update(company_id, **update_data)
        if not company:
            return error_response(ERROR_CODES['NOT_FOUND'], 'company not found', 404)
        _cleanup_replaced_upload(previous_company_picture, update_data.get('company_picture'))
        return {'company': company}

    @jwt_required()
    def delete(self, company_id):
        """Permanently delete a company (super admins only).

        Args:
            company_id (str): Company UUID path parameter.

        Returns:
            tuple[dict, int]: ``{msg}`` and 200, 403, or 404.
        """
        current = user_service.get_by_id(get_jwt_identity())
        if not _can(current, 'manage_companies'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'not allowed to delete companies', 403)
        if not company_service.facade.delete(company_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'company not found', 404)
        return {'msg': 'company deleted'}


def _can_manage_company(user, company):
    """Return ``True`` if *user* may deactivate *company*.

    Allowed for super admins (any company) and for the company's own admin
    (matched by ``admin_id`` or, as a fallback, ``admin_email``).
    """
    if not user or not company:
        return False
    if _can(user, 'manage_companies'):
        return True
    # Co-responsable : porte le flag is_company_admin pour cette entreprise.
    if user.get('is_company_admin') and user.get('company_id') == company.get('id'):
        return True
    if company.get('admin_id') and company['admin_id'] == user.get('id'):
        return True
    admin_email = (company.get('admin_email') or '').lower().strip()
    user_email = (user.get('email') or '').lower().strip()
    return bool(admin_email) and admin_email == user_email


class CompanyDeactivateResource(Resource):
    """Soft-deactivate a company without removing the database row."""

    @jwt_required()
    def patch(self, company_id):
        """Deactivate a company by id.

        Allowed for a super admin (any company) or for the company's own
        admin. A hard delete is reserved for super admins (see
        :class:`CompanyResource`).

        Args:
            company_id (str): Company UUID path parameter.

        Returns:
            tuple[dict, int]: ``{msg}`` and 200, 403, or 404.
        """
        identity = get_jwt_identity()
        current = user_service.get_by_id(identity)
        company = company_service.facade.get(company_id)
        if not company:
            return error_response(ERROR_CODES['NOT_FOUND'], 'company not found', 404)
        if not _can_manage_company(current, company):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'not allowed to deactivate this company', 403)
        if not company_service.facade.deactivate(company_id, by=identity):
            return error_response(ERROR_CODES['NOT_FOUND'], 'company not found', 404)
        return {'msg': 'company deactivated'}


class CompanyReactivateResource(Resource):
    """Re-activate a previously deactivated company."""

    @jwt_required()
    def patch(self, company_id):
        """Set ``is_active`` back to True for the given company.

        Allowed for a super admin (any company) or for the company's own
        admin, mirroring :class:`CompanyDeactivateResource`.

        Args:
            company_id (str): Company UUID path parameter.

        Returns:
            tuple[dict, int]: ``{msg, company}`` and 200, 403, or 404.
        """
        identity = get_jwt_identity()
        current = user_service.get_by_id(identity)
        company = company_service.facade.get(company_id)
        if not company:
            return error_response(ERROR_CODES['NOT_FOUND'], 'company not found', 404)
        if not _can_manage_company(current, company):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'not allowed to reactivate this company', 403)
        updated = company_service.facade.update(company_id, is_active=True)
        if not updated:
            return error_response(ERROR_CODES['NOT_FOUND'], 'company not found', 404)
        return {'msg': 'company reactivated', 'company': updated}


class CompanyUsersResource(Resource):
    """List users that belong to a specific company."""

    @jwt_required()
    def get(self, company_id):
        """Return users for a company.

        Args:
            company_id (str): Company UUID path parameter.

        Returns:
            tuple[dict, int]: ``{users}`` and 200, or 404.
        """
        if not company_service.facade.get(company_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'company not found', 404)
        return {'users': user_service.list_users_by_company(company_id)}


class CompanyAssignUserResource(Resource):
    """Assign or remove a user from a company."""

    @jwt_required()
    def post(self, company_id, user_id):
        """Assign a user to a company.

        Args:
            company_id (str): Target company UUID.
            user_id (str): User UUID to assign.

        Returns:
            tuple[dict, int]: ``{user}`` and 200, or 404.
        """
        if not company_service.facade.get(company_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'company not found', 404)
        current = user_service.get_by_id(get_jwt_identity())
        # A super admin keeps full control; others can't orphan a company.
        if not (current or {}).get('is_super_admin'):
            administered = _administers_active_company(user_id, exclude_company_id=company_id)
            if administered is not None:
                return error_response(
                    ERROR_CODES['CONFLICT'],
                    "Cet utilisateur administre l'entreprise "
                    f"« {administered['name']} ». Réassignez d'abord un autre "
                    "administrateur à celle-ci avant de le déplacer.", 409)
        updated = user_service.update(user_id, company_id=company_id)
        if not updated:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        return {'user': updated}, 200

    @jwt_required()
    def delete(self, company_id, user_id):
        """Remove a user from a company.

        Args:
            company_id (str): Company UUID (used for routing only).
            user_id (str): User UUID to remove.

        Returns:
            tuple[dict, int]: ``{user}`` and 200, or 404.
        """
        current = user_service.get_by_id(get_jwt_identity())
        # A super admin keeps full control; others can't orphan a company.
        if not (current or {}).get('is_super_admin'):
            administered = _administers_active_company(user_id)
            if administered is not None:
                return error_response(
                    ERROR_CODES['CONFLICT'],
                    "Cet utilisateur administre l'entreprise "
                    f"« {administered['name']} ». Réassignez d'abord un autre "
                    "administrateur avant de le retirer.", 409)
        updated = user_service.update(user_id, company_id=None)
        if not updated:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        return {'user': updated}, 200
