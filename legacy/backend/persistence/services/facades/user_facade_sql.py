"""User persistence facade (SQLAlchemy)."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from backend.persistence.db import SessionLocal
from backend.persistence.models import User as ORMUser
from ._common_sql import isoformat, to_csv, from_csv


class UserFacade:
    """SQLAlchemy-backed facade encapsulating common user database operations.

    All public methods return plain dicts suitable for JSON serialisation.
    Password hashing and verification are handled here so that service and
    API layers remain free of cryptographic concerns.
    """

    def create_user(self, email, password, first_name=None, last_name=None, **kwargs):
        """Persist a new user row with a hashed password.

        Args:
            email (str): User email address (stored lowercase).
            password (str): Plaintext password; hashed before storage.
            first_name (str | None): Optional first name.
            last_name (str | None): Optional last name.
            **kwargs: Optional fields — ``phone``, ``profile_picture``,
                ``business_card``, ``is_super_admin``, ``company_id``,
                ``is_active``.

        Returns:
            dict: Newly created user as a serialisable dict.

        Raises:
            sqlalchemy.exc.IntegrityError: If the email already exists.
        """
        db = SessionLocal()
        try:
            password_hash = generate_password_hash(password)
            user = ORMUser(
                email=email.lower().strip(),
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                job_title=kwargs.get('job_title'),
                phone=kwargs.get('phone'),
                profile_picture=kwargs.get('profile_picture'),
                business_card=kwargs.get('business_card'),
                is_super_admin=kwargs.get('is_super_admin', False),
                is_company_admin=kwargs.get('is_company_admin', False),
                is_staff=kwargs.get('is_staff', False),
                permissions=to_csv(kwargs.get('permissions')),
                company_id=kwargs.get('company_id'),
                is_active=kwargs.get('is_active', True),
                created_at=datetime.now(timezone.utc),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return self._to_dict(user)
        except IntegrityError:
            db.rollback()
            raise
        finally:
            db.close()

    def get_by_email(self, email):
        """Retrieve a user by email address.

        Args:
            email (str): Email to look up (compared lowercase).

        Returns:
            dict | None: User dict, or ``None`` if not found.
        """
        db = SessionLocal()
        u: Any = db.query(ORMUser).filter(
            ORMUser.email == email.lower().strip()).first()
        db.close()
        return self._to_dict(u) if u else None

    def get_by_id(self, user_id):
        """Retrieve a user by primary key.

        Args:
            user_id (str): UUID string of the user.

        Returns:
            dict | None: User dict, or ``None`` if not found.
        """
        db = SessionLocal()
        u: Any = db.query(ORMUser).filter(ORMUser.id == user_id).first()
        db.close()
        return self._to_dict(u) if u else None

    def list_users(self, limit=100, company_id=None):
        """Return a list of users, optionally filtered by company.

        Args:
            limit (int): Maximum number of rows to return. Defaults to 100.
            company_id (str | None): Filter users by this company id.

        Returns:
            list[dict]: Serialised user dicts.
        """
        db = SessionLocal()
        query = db.query(ORMUser)
        if company_id:
            query = query.filter(ORMUser.company_id == company_id)
        rows = query.limit(limit).all()
        db.close()
        return [self._to_dict(row) for row in rows]

    def check_password(self, email, password):
        """Verify a plaintext password against the stored hash.

        Args:
            email (str): User email.
            password (str): Plaintext password to verify.

        Returns:
            bool: ``True`` if the credentials are valid, ``False`` otherwise.
        """
        db = SessionLocal()
        u: Any = db.query(ORMUser).filter(
            ORMUser.email == email.lower().strip()).first()
        db.close()
        if not u:
            return False
        return check_password_hash(u.password_hash, password)

    def deactivate(self, identifier, by=None):
        """Soft-deactivate a user by email or id.

        If *identifier* contains ``@`` it is treated as an email address;
        otherwise it is treated as a primary key.

        Args:
            identifier (str): Email or user id.
            by (str | None): Id of the actor performing the deactivation.

        Returns:
            bool: ``True`` if a user was deactivated, ``False`` if not found.
        """
        db = SessionLocal()
        u: Any
        if isinstance(identifier, str) and '@' in identifier:
            u = db.query(ORMUser).filter(
                ORMUser.email == identifier.lower().strip()).first()
        else:
            u = db.query(ORMUser).filter(ORMUser.id == identifier).first()
        if not u:
            db.close()
            return False
        u.is_active = False
        u.deactivate_by = by
        u.updated_at = datetime.now(timezone.utc)
        db.add(u)
        db.commit()
        db.close()
        return True

    def update(self, user_id, **kwargs):
        """Partially update a user's mutable fields.

        Args:
            user_id (str): Primary key of the user to update.
            **kwargs: Fields to update — ``first_name``, ``last_name``,
                ``phone``, ``profile_picture``, ``business_card``,
                ``company_id``, ``is_super_admin``, ``is_active``.

        Returns:
            dict | None: Updated user dict, or ``None`` if not found.
        """
        db = SessionLocal()
        try:
            u: Any = db.query(ORMUser).filter(ORMUser.id == user_id).first()
            if not u:
                return None
            for field in ('first_name', 'last_name', 'job_title', 'phone',
                          'profile_picture', 'business_card', 'company_id'):
                if field in kwargs:
                    setattr(u, field, kwargs.get(field))
            if 'is_super_admin' in kwargs:
                u.is_super_admin = bool(kwargs.get('is_super_admin'))
            if 'is_company_admin' in kwargs:
                u.is_company_admin = bool(kwargs.get('is_company_admin'))
            if 'is_staff' in kwargs:
                u.is_staff = bool(kwargs.get('is_staff'))
            if 'permissions' in kwargs:
                u.permissions = to_csv(kwargs.get('permissions'))
            if 'is_active' in kwargs:
                u.is_active = bool(kwargs.get('is_active'))
            u.updated_at = datetime.now(timezone.utc)
            db.add(u)
            db.commit()
            db.refresh(u)
            return self._to_dict(u)
        finally:
            db.close()

    def delete(self, user_id):
        """Permanently delete a user row.

        Args:
            user_id (str): Primary key of the user.

        Returns:
            bool: ``True`` when deleted, ``False`` when not found.
        """
        db = SessionLocal()
        try:
            user: Any = db.query(ORMUser).filter(ORMUser.id == user_id).first()
            if not user:
                return False
            db.delete(user)
            db.commit()
            return True
        finally:
            db.close()

    def reset_password(self, user_id, password):
        """Replace a user's password hash.

        Args:
            user_id (str): Primary key of the user.
            password (str): New plaintext password to hash and store.

        Returns:
            bool | None: ``True`` on success, ``None`` if user not found.
        """
        db = SessionLocal()
        try:
            u: Any = db.query(ORMUser).filter(ORMUser.id == user_id).first()
            if not u:
                return None
            u.password_hash = generate_password_hash(password)
            u.updated_at = datetime.now(timezone.utc)
            db.add(u)
            db.commit()
            return True
        finally:
            db.close()

    def _to_dict(self, u):
        return {
            'id': u.id,
            'email': u.email,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'job_title': getattr(u, 'job_title', None),
            'phone': u.phone,
            'profile_picture': u.profile_picture,
            'business_card': u.business_card,
            'is_super_admin': u.is_super_admin,
            'is_company_admin': getattr(u, 'is_company_admin', False),
            'is_staff': getattr(u, 'is_staff', False),
            'permissions': from_csv(getattr(u, 'permissions', None)),
            'is_active': u.is_active,
            'company_id': getattr(u, 'company_id', None),
            'created_at': isoformat(u.created_at),
            'updated_at': isoformat(getattr(u, 'updated_at', None)),
            'deactivate_by': getattr(u, 'deactivate_by', None),
            'delete_by': getattr(u, 'delete_by', None),
            'uploaded_at': isoformat(getattr(u, 'uploaded_at', None)),
        }
