"""Company persistence facade (SQLAlchemy)."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError

from backend.persistence.db import SessionLocal
from backend.persistence.models import Company as ORMCompany, User as ORMUser
from ._common_sql import isoformat


class CompanyFacade:
    """SQLAlchemy-backed facade for company entities.

    Admin resolution is performed during creation: when *admin_id* is not
    provided, the facade looks up the user whose email matches *admin_email*.
    """

    def create(self, name, admin_email=None, admin_id=None,
               enforce_single_admin=True, **kwargs):
        """Persist a new company, resolving admin_id from admin_email if needed.

        Args:
            name (str): Company display name.
            admin_email (str | None): Admin email used to resolve *admin_id*.
            admin_id (str | None): Explicit admin user UUID; overrides lookup.
            **kwargs: Optional fields — ``description``, ``website_link``,
                ``company_picture``.

        Returns:
            dict: Newly created company as a serialisable dict.

        Raises:
            ValueError: If *admin_email* is missing or not found in the DB.
            sqlalchemy.exc.IntegrityError: On database constraint violation.
        """
        db = SessionLocal()
        try:
            resolved_admin_id = admin_id
            normalized_admin_email = admin_email.lower().strip() if admin_email else None
            if not normalized_admin_email:
                raise ValueError('admin_email is required')
            if resolved_admin_id is None:
                admin_user = db.query(ORMUser).filter(
                    ORMUser.email == normalized_admin_email).first()
                if not admin_user:
                    raise ValueError('admin_email not found')
                resolved_admin_id = admin_user.id
            # An admin can only run a single active company: reassigning one who
            # already administers another would leave that one without an admin.
            # A super admin may override this (caller passes enforce=False).
            if enforce_single_admin:
                already_admin = db.query(ORMCompany).filter(
                    ORMCompany.admin_id == resolved_admin_id,
                    ORMCompany.is_active.is_(True),
                ).first()
                if already_admin is not None:
                    raise ValueError(
                        "Cet utilisateur administre déjà l'entreprise "
                        f"« {already_admin.name} ». Réassignez d'abord un autre "
                        "administrateur à celle-ci avant de le désigner ici.")
            c = ORMCompany(
                name=name.strip(),
                admin_email=normalized_admin_email,
                admin_id=resolved_admin_id,
                description=kwargs.get('description'),
                location=kwargs.get('location'),
                website_link=kwargs.get('website_link'),
                company_picture=kwargs.get('company_picture'),
                kind=kwargs.get('kind') or 'company',
                created_at=datetime.now(timezone.utc),
            )
            db.add(c)
            db.flush()  # assign c.id before linking the admin
            # The admin belongs to the company they administer (counts as an
            # employee and drives the « patron » role on the frontend).
            admin_user = db.query(ORMUser).filter(ORMUser.id == resolved_admin_id).first()
            if admin_user is not None:
                admin_user.company_id = c.id
                db.add(admin_user)
            db.commit()
            db.refresh(c)
            return self._to_dict(c, self._count_employees(db, c.id))
        except IntegrityError:
            db.rollback()
            raise
        except ValueError:
            db.rollback()
            raise
        finally:
            db.close()

    def get(self, company_id):
        """Retrieve a company by primary key.

        Args:
            company_id (str): Company UUID.

        Returns:
            dict | None: Company dict, or ``None`` if not found.
        """
        db = SessionLocal()
        try:
            c: Any = db.query(ORMCompany).filter(ORMCompany.id == company_id).first()
            if not c:
                return None
            return self._to_dict(c, self._count_employees(db, c.id))
        finally:
            db.close()

    def list(self, limit=100):
        """Return a list of companies.

        Args:
            limit (int): Maximum number of rows. Defaults to 100.

        Returns:
            list[dict]: Serialised company dicts.
        """
        db = SessionLocal()
        try:
            rows = db.query(ORMCompany).limit(limit).all()
            return [self._to_dict(r, self._count_employees(db, r.id)) for r in rows]
        finally:
            db.close()

    def update(self, company_id, **kwargs):
        """Partially update a company's mutable fields.

        Args:
            company_id (str): Primary key of the company.
            **kwargs: Fields to update — ``name``, ``description``,
                ``website_link``, ``company_picture``, ``admin_email``,
                ``admin_id``, ``is_active``.

        Returns:
            dict | None: Updated company dict, or ``None`` if not found.
        """
        db = SessionLocal()
        try:
            company: Any = db.query(ORMCompany).filter(
                ORMCompany.id == company_id).first()
            if not company:
                return None
            for field in ('name', 'description', 'location', 'website_link',
                          'company_picture', 'admin_email', 'admin_id', 'kind'):
                if field in kwargs:
                    setattr(company, field, kwargs.get(field))
            if 'is_active' in kwargs:
                company.is_active = bool(kwargs.get('is_active'))
            company.updated_at = datetime.now(timezone.utc)
            db.add(company)
            db.commit()
            db.refresh(company)
            return self._to_dict(company, self._count_employees(db, company.id))
        finally:
            db.close()

    def deactivate(self, company_id, by=None):
        """Soft-deactivate a company.

        Args:
            company_id (str): Company UUID.
            by (str | None): Id of the actor performing the action.

        Returns:
            dict | None: Updated company dict, or ``None`` if not found.
        """
        return self.update(company_id, is_active=False)

    def delete(self, company_id):
        """Permanently delete a company row.

        Args:
            company_id (str): Company UUID.

        Returns:
            bool: ``True`` when deleted, ``False`` when not found.
        """
        db = SessionLocal()
        try:
            company: Any = db.query(ORMCompany).filter(
                ORMCompany.id == company_id).first()
            if not company:
                return False
            db.delete(company)
            db.commit()
            return True
        finally:
            db.close()

    def _count_employees(self, db, company_id):
        """Number of users attached to *company_id* (auto employee count)."""
        return db.query(ORMUser).filter(ORMUser.company_id == company_id).count()

    def _to_dict(self, c, employee_count=0):
        return {
            'id': c.id,
            'name': c.name,
            'admin_email': c.admin_email,
            'admin_id': c.admin_id,
            'description': c.description,
            'location': getattr(c, 'location', None),
            'website_link': c.website_link,
            'company_picture': c.company_picture,
            'kind': getattr(c, 'kind', None) or 'company',
            'employee_count': employee_count,
            'is_active': c.is_active,
            'created_at': isoformat(c.created_at),
            'updated_at': isoformat(getattr(c, 'updated_at', None)),
            'deactivate_by': getattr(c, 'deactivate_by', None),
            'delete_by': getattr(c, 'delete_by', None),
            'uploaded_at': isoformat(getattr(c, 'uploaded_at', None)),
        }
