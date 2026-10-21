"""User-related API resources."""

from typing import Any

from flask import request
from flask_jwt_extended import get_jwt_identity
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from backend.api.errors import ERROR_CODES, error_response
from backend.api.jwt_helpers import jwt_required
from backend.api.uploads import save_image_upload
from backend.api.resources._helpers import _can, _cleanup_replaced_upload, _request_payload
from backend.models.user import User as DomainUser, validate_permissions
from backend.persistence.services import CompanyService, UserService


service = UserService()
company_service = CompanyService()


def _administered_company(user):
    """Return the company *user* administers, or ``None``.

    A user administers a company when its ``admin_id`` matches their id or,
    as a fallback, its ``admin_email`` matches their email (case-insensitive).
    """
    if not user:
        return None
    email = (user.get('email') or '').lower().strip()
    for company in company_service.facade.list(limit=1000):
        if company.get('admin_id') and company['admin_id'] == user.get('id'):
            return company
        admin_email = (company.get('admin_email') or '').lower().strip()
        if admin_email and admin_email == email:
            return company
    return None


def _extract_profile_picture(payload):
    uploaded_file = request.files.get(
        'profile_picture_file') or request.files.get('profile_picture')
    if uploaded_file and uploaded_file.filename:
        return save_image_upload(uploaded_file, 'users/profile_pictures')
    return payload.get('profile_picture')


def _extract_business_card(payload):
    uploaded_file = request.files.get(
        'business_card_file') or request.files.get('business_card')
    if uploaded_file and uploaded_file.filename:
        return save_image_upload(uploaded_file, 'users/business_cards')
    return payload.get('business_card')


class UserListResource(Resource):
    """List users or create a new user."""

    @jwt_required()
    def get(self):
        """Return users, optionally filtered by company.

        Query parameters:
            limit (int): Max users to return (default 100).
            company_id (str): Filter by company UUID.

        Returns:
            tuple[dict, int]: ``{users}`` and 200.
        """
        limit = request.args.get('limit', default=100, type=int)
        company_id = request.args.get('company_id')
        if company_id:
            return {'users': service.list_users_by_company(company_id, limit=limit)}
        return {'users': service.list_users(limit=limit)}

    @jwt_required()
    def post(self):
        """Create a new user. Restricted to super admins and company admins.

        A super admin can create a user in any company and, when
        ``is_company_admin`` is set, promote them to that company's admin. A
        company admin can only create users inside their own company.

        Expected JSON body:
            email (str): Valid email address.
            password (str): Password (min 8 chars).
            first_name (str | None): Optional first name.
            last_name (str | None): Optional last name.
            phone (str | None): Optional phone number.
            company_id (str | None): Target company (super admin only;
                forced to their own company for a company admin).
            is_company_admin (bool): When set by a super admin, the new user
                becomes the admin of ``company_id``.

        Returns:
            tuple[dict, int]: ``{user}`` and 201, or 400/403/409.
        """
        current = service.get_by_id(get_jwt_identity())
        is_super_admin = bool(current and current.get('is_super_admin'))
        # A super admin and any staff member holding ``manage_users`` may
        # create platform-wide accounts; a company admin is limited to their
        # own company.
        can_manage_users = _can(current, 'manage_users')
        admin_company = None if can_manage_users else _administered_company(current)
        if not can_manage_users and not admin_company:
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'only super admins, staff or company admins can create users', 403)

        data = _request_payload()
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        job_title = data.get('job_title')
        phone = data.get('phone')
        profile_picture = _extract_profile_picture(data)
        business_card = _extract_business_card(data)
        if not email or not password:
            return error_response(ERROR_CODES['BAD_REQUEST'], 'email and password required', 400)

        # Determine the target company: a company admin is locked to their own.
        if can_manage_users:
            company_id = data.get('company_id')
            make_company_admin = bool(data.get('is_company_admin'))
        else:
            company_id = admin_company['id']
            make_company_admin = False

        # Privileged accounts (super admin / staff with rights) may only be
        # minted by a super admin — staff cannot escalate their own reach.
        make_super = is_super_admin and bool(data.get('is_super_admin'))
        make_staff = is_super_admin and bool(data.get('is_staff'))
        permissions = []
        if make_staff:
            try:
                permissions = validate_permissions(data.get('permissions'))
            except Exception as exc:
                return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)

        try:
            DomainUser(email=email, password=password, first_name=first_name)
        except Exception as exc:
            return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)
        if make_company_admin and not company_id:
            return error_response(
                ERROR_CODES['BAD_REQUEST'],
                'company_id is required to set a company admin', 400)
        try:
            user = service.register(
                email, password,
                first_name=first_name,
                last_name=last_name,
                job_title=job_title,
                phone=phone,
                company_id=company_id,
                is_company_admin=make_company_admin,
                is_super_admin=make_super,
                is_staff=make_staff,
                permissions=permissions,
                profile_picture=profile_picture,
                business_card=business_card,
            )
        except IntegrityError:
            return error_response(
                ERROR_CODES['CONFLICT'],
                'a user with this email already exists', 409)
        except Exception as exc:
            return error_response(ERROR_CODES['CONFLICT'], 'could not create user', 409, str(exc))

        # Promote the freshly created user to company admin when requested.
        if make_company_admin:
            company_service.facade.update(
                company_id, admin_id=user['id'], admin_email=user['email'])
        return {'user': user}, 201


class UserMeResource(Resource):
    """Operations on the currently authenticated user."""

    @jwt_required()
    def get(self):
        """Return the current user's profile.

        Returns:
            tuple[dict, int]: ``{user}`` and 200.
        """
        user = service.get_by_id(get_jwt_identity())
        if not user:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        return {'user': user}

    @jwt_required()
    def patch(self):
        """Partially update the current user's profile.

        Accepts JSON or multipart form data. Updatable fields: ``first_name``,
        ``last_name``, ``profile_picture``, ``business_card``.

        Returns:
            tuple[dict, int]: ``{user}`` and 200.
        """
        data = _request_payload()
        current_user = service.get_by_id(get_jwt_identity())
        if not current_user:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        update_data: dict[str, Any] = {}
        previous_profile_picture = current_user.get('profile_picture')
        previous_business_card = current_user.get('business_card')
        try:
            if 'first_name' in data:
                fn = DomainUser.validate_first_name(data.get('first_name'))
                if fn is not None:
                    update_data['first_name'] = fn
            if 'last_name' in data:
                ln = DomainUser.validate_last_name(data.get('last_name'))
                if ln is not None:
                    update_data['last_name'] = ln
            if 'phone' in data:
                update_data['phone'] = data.get('phone')
            if 'job_title' in data:
                update_data['job_title'] = data.get('job_title')
            uploaded_file = (request.files.get('profile_picture_file')
                             or request.files.get('profile_picture'))
            if uploaded_file and uploaded_file.filename:
                update_data['profile_picture'] = save_image_upload(
                    uploaded_file, 'users/profile_pictures')
            elif 'profile_picture' in data:
                update_data['profile_picture'] = data.get('profile_picture')
            uploaded_file = (request.files.get('business_card_file')
                             or request.files.get('business_card'))
            if uploaded_file and uploaded_file.filename:
                update_data['business_card'] = save_image_upload(
                    uploaded_file, 'users/business_cards')
            elif 'business_card' in data:
                update_data['business_card'] = data.get('business_card')
        except Exception as exc:
            return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)

        # Changement de mot de passe self-service (la confirmation est faite
        # côté client). On valide la longueur via le modèle de domaine.
        new_password = data.get('password')
        if new_password:
            try:
                DomainUser(email=current_user.get('email'), password=new_password)
            except Exception as exc:
                return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)
            service.facade.reset_password(get_jwt_identity(), new_password)

        user = service.update(get_jwt_identity(), **update_data) if update_data \
            else service.get_by_id(get_jwt_identity())
        if not user:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        _cleanup_replaced_upload(previous_profile_picture, update_data.get('profile_picture'))
        _cleanup_replaced_upload(previous_business_card, update_data.get('business_card'))
        return {'user': user}


class UserResource(Resource):
    """CRUD operations on a specific user identified by ``user_id``."""

    @jwt_required()
    def get(self, user_id):
        """Retrieve a user by id.

        Args:
            user_id (str): User UUID path parameter.

        Returns:
            tuple[dict, int]: ``{user}`` and 200, or 404.
        """
        u = service.get_by_id(user_id)
        if not u:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        return {'user': u}

    @jwt_required()
    def put(self, user_id):
        """Replace a user's name fields.

        Args:
            user_id (str): User UUID path parameter.

        Returns:
            tuple[dict, int]: ``{user}`` and 200.
        """
        data = _request_payload()
        current_user = service.get_by_id(user_id)
        if not current_user:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        first_name: Any = data.get('first_name')
        last_name: Any = data.get('last_name')
        try:
            fn = DomainUser.validate_first_name(first_name)
            ln = DomainUser.validate_last_name(last_name)
        except Exception as exc:
            return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)

        update_data: dict[str, Any] = {'first_name': fn, 'last_name': ln}
        previous_profile_picture = current_user.get('profile_picture')
        previous_business_card = current_user.get('business_card')
        uploaded_file = (request.files.get('profile_picture_file')
                         or request.files.get('profile_picture'))
        if uploaded_file and uploaded_file.filename:
            update_data['profile_picture'] = save_image_upload(
                uploaded_file, 'users/profile_pictures')
        elif 'profile_picture' in data:
            update_data['profile_picture'] = data.get('profile_picture')
        uploaded_file = (request.files.get('business_card_file')
                         or request.files.get('business_card'))
        if uploaded_file and uploaded_file.filename:
            update_data['business_card'] = save_image_upload(
                uploaded_file, 'users/business_cards')
        elif 'business_card' in data:
            update_data['business_card'] = data.get('business_card')
        user = service.update(user_id, **update_data)
        if not user:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        _cleanup_replaced_upload(previous_profile_picture, update_data.get('profile_picture'))
        _cleanup_replaced_upload(previous_business_card, update_data.get('business_card'))
        return {'user': user}

    @jwt_required()
    def patch(self, user_id):
        """Partially update a user's profile fields.

        Args:
            user_id (str): User UUID path parameter.

        Returns:
            tuple[dict, int]: ``{user}`` and 200.
        """
        data = _request_payload()
        current_user = service.get_by_id(user_id)
        if not current_user:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        update_data: dict[str, Any] = {}
        previous_profile_picture = current_user.get('profile_picture')
        previous_business_card = current_user.get('business_card')
        try:
            if 'first_name' in data:
                fn = DomainUser.validate_first_name(data.get('first_name'))
                if fn is not None:
                    update_data['first_name'] = fn
            if 'last_name' in data:
                ln = DomainUser.validate_last_name(data.get('last_name'))
                if ln is not None:
                    update_data['last_name'] = ln
            if 'phone' in data:
                update_data['phone'] = data.get('phone')
            uploaded_file = (request.files.get('profile_picture_file')
                             or request.files.get('profile_picture'))
            if uploaded_file and uploaded_file.filename:
                update_data['profile_picture'] = save_image_upload(
                    uploaded_file, 'users/profile_pictures')
            elif 'profile_picture' in data:
                update_data['profile_picture'] = data.get('profile_picture')
            uploaded_file = (request.files.get('business_card_file')
                             or request.files.get('business_card'))
            if uploaded_file and uploaded_file.filename:
                update_data['business_card'] = save_image_upload(
                    uploaded_file, 'users/business_cards')
            elif 'business_card' in data:
                update_data['business_card'] = data.get('business_card')
        except Exception as exc:
            return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)

        user = service.update(user_id, **update_data)
        if not user:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        _cleanup_replaced_upload(previous_profile_picture, update_data.get('profile_picture'))
        _cleanup_replaced_upload(previous_business_card, update_data.get('business_card'))
        return {'user': user}

    @jwt_required()
    def delete(self, user_id):
        """Permanently delete a user (super admins only).

        Args:
            user_id (str): User UUID path parameter.

        Returns:
            tuple[dict, int]: ``{msg}`` and 200, 403, or 404.
        """
        current = service.get_by_id(get_jwt_identity())
        if not _can(current, 'manage_users'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'not allowed to delete users', 403)
        target = service.get_by_id(user_id)
        if not target:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        # A super-admin account may never be deleted by a non-super-admin
        # (e.g. a staff member holding ``manage_users``).
        if target.get('is_super_admin') and not current.get('is_super_admin'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'cannot delete a super admin account', 403)
        if not service.delete(user_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        return {'msg': 'user deleted'}


class UserDeactivateResource(Resource):
    """Soft-deactivate a user without removing the database row."""

    @jwt_required()
    def patch(self, user_id):
        """Deactivate a user by id.

        Allowed for a super admin (any user) or for a user deactivating
        their own account.

        Args:
            user_id (str): User UUID path parameter.

        Returns:
            tuple[dict, int]: ``{msg}`` and 200, 403, or 404.
        """
        identity = get_jwt_identity()
        current = service.get_by_id(identity)
        if identity != user_id and not _can(current, 'manage_users'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'not allowed to deactivate this user', 403)
        # A super-admin account may not be deactivated by a non-super-admin
        # (a staff member with ``manage_users``); only the super admin
        # themselves or another super admin may do so.
        target = service.get_by_id(user_id)
        if (target and target.get('is_super_admin') and identity != user_id
                and not current.get('is_super_admin')):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'cannot deactivate a super admin account', 403)
        # A company admin cannot be deactivated while still administering an
        # active company — a replacement must be assigned first
        # (PATCH /companies/<id> {admin_email}).
        for company in company_service.facade.list(limit=1000):
            if (company.get('admin_id') == user_id
                    and company.get('is_active')):
                return error_response(
                    ERROR_CODES['CONFLICT'],
                    'reassign the company admin before deactivating this user',
                    409)
        if not service.deactivate(user_id, by='api'):
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        return {'msg': 'deactivated'}


class UserReactivateResource(Resource):
    """Re-activate a previously deactivated user (super admins only)."""

    @jwt_required()
    def patch(self, user_id):
        """Set ``is_active`` back to True for the given user.

        Args:
            user_id (str): User UUID path parameter.

        Returns:
            tuple[dict, int]: ``{msg, user}`` and 200, 403, or 404.
        """
        current = service.get_by_id(get_jwt_identity())
        if not _can(current, 'manage_users'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'not allowed to reactivate users', 403)
        user = service.update(user_id, is_active=True)
        if not user:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        return {'msg': 'reactivated', 'user': user}


class UserRoleResource(Resource):
    """Promote or demote a user's super-admin role (super admins only)."""

    @jwt_required()
    def patch(self, user_id):
        """Set a user's ``is_super_admin`` flag.

        Expected JSON body:
            is_super_admin (bool): Target role.

        Refuses to demote the last remaining active super admin so the
        platform always keeps at least one.

        Args:
            user_id (str): User UUID path parameter.

        Returns:
            tuple[dict, int]: ``{user}`` and 200, 400, 403, or 404.
        """
        current = service.get_by_id(get_jwt_identity())
        if not current or not current.get('is_super_admin'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'only super admins can change roles', 403)
        data = request.get_json(silent=True) or {}
        if 'is_super_admin' not in data:
            return error_response(ERROR_CODES['BAD_REQUEST'], 'is_super_admin is required', 400)
        target = service.get_by_id(user_id)
        if not target:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        make_super = bool(data.get('is_super_admin'))
        # Never leave the platform without an active super admin.
        if target.get('is_super_admin') and not make_super:
            active_supers = [
                u for u in service.list_users(limit=1000)
                if u.get('is_super_admin') and u.get('is_active')
                and u.get('id') != user_id
            ]
            if not active_supers:
                return error_response(
                    ERROR_CODES['FORBIDDEN'],
                    'cannot demote the last active super admin', 403)
        user = service.update(user_id, is_super_admin=make_super)
        if not user:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        return {'user': user}


class UserPermissionsResource(Resource):
    """Manage a user's staff status and granular rights (super admins only)."""

    @jwt_required()
    def patch(self, user_id):
        """Set a user's ``is_staff`` flag and ``permissions`` list.

        Expected JSON body:
            is_staff (bool): Whether the account is a platform staff member.
            permissions (list[str]): Subset of
                ``backend.models.user.STAFF_PERMISSIONS``. Ignored (cleared)
                when ``is_staff`` is false.

        Args:
            user_id (str): User UUID path parameter.

        Returns:
            tuple[dict, int]: ``{user}`` and 200, 400, 403, or 404.
        """
        current = service.get_by_id(get_jwt_identity())
        if not current or not current.get('is_super_admin'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'only super admins can assign staff rights', 403)
        target = service.get_by_id(user_id)
        if not target:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        data = request.get_json(silent=True) or {}
        make_staff = bool(data.get('is_staff'))
        try:
            permissions = validate_permissions(data.get('permissions')) if make_staff else []
        except Exception as exc:
            return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)
        user = service.update(
            user_id, is_staff=make_staff, permissions=permissions)
        if not user:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        return {'user': user}


def _is_company_admin_of(user, company_id):
    """Return ``True`` if *user* administers the company ``company_id``.

    A user administers a company when they carry the ``is_company_admin``
    flag for that company, or (legacy) when they are its ``admin_id`` /
    ``admin_email``.
    """
    if not user or not company_id:
        return False
    if user.get('is_company_admin') and user.get('company_id') == company_id:
        return True
    company = company_service.facade.get(company_id)
    if not company:
        return False
    if company.get('admin_id') and company['admin_id'] == user.get('id'):
        return True
    email = (user.get('email') or '').lower().strip()
    admin_email = (company.get('admin_email') or '').lower().strip()
    return bool(email) and email == admin_email


class UserCompanyAdminResource(Resource):
    """Promote or demote a company co-administrator.

    Allowed for a super admin (any company) or for a company admin acting on
    a member of their own company. The target keeps its ``company_id``; only
    the ``is_company_admin`` flag changes.
    """

    @jwt_required()
    def patch(self, user_id):
        """Set a user's ``is_company_admin`` flag.

        Expected JSON body:
            is_company_admin (bool): Target company-admin role.

        Args:
            user_id (str): User UUID path parameter.

        Returns:
            tuple[dict, int]: ``{user}`` and 200, 400, 403, or 404.
        """
        current = service.get_by_id(get_jwt_identity())
        if not current:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        target = service.get_by_id(user_id)
        if not target:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        data = request.get_json(silent=True) or {}
        if 'is_company_admin' not in data:
            return error_response(
                ERROR_CODES['BAD_REQUEST'], 'is_company_admin is required', 400)

        is_super_admin = bool(current.get('is_super_admin'))
        company_id = target.get('company_id')
        same_company = bool(company_id) and current.get('company_id') == company_id
        if not is_super_admin and not (
                same_company and _is_company_admin_of(current, company_id)):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'not allowed to change this user role', 403)
        if not is_super_admin and not company_id:
            return error_response(
                ERROR_CODES['BAD_REQUEST'],
                'user has no company', 400)

        make_admin = bool(data.get('is_company_admin'))
        # Une entreprise doit toujours garder au moins un responsable : on
        # refuse de rétrograder le dernier responsable encore en place.
        if not make_admin and company_id:
            admins = [
                u for u in service.list_users(limit=1000)
                if u.get('company_id') == company_id
                and _is_company_admin_of(u, company_id)
                and u.get('id') != user_id
            ]
            if not admins:
                return error_response(
                    ERROR_CODES['CONFLICT'],
                    'une entreprise doit garder au moins un responsable', 409)

        user = service.update(user_id, is_company_admin=make_admin)
        if not user:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        return {'user': user}


class UserResetPasswordResource(Resource):
    """Reset a user's password."""

    @jwt_required()
    def post(self, user_id):
        """Set a new password for the given user.

        Args:
            user_id (str): User UUID path parameter.

        Expected JSON body:
            password (str): New plaintext password.

        Returns:
            tuple[dict, int]: ``{msg}`` and 200, or 404.
        """
        data = request.get_json(silent=True) or {}
        password = data.get('password')
        if not password:
            return error_response(ERROR_CODES['BAD_REQUEST'], 'password is required', 400)
        if not service.reset_password(user_id, password):
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        return {'msg': 'password updated'}
