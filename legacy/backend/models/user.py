#!/usr/bin/env python3
"""Domain model representing application users."""

from .base import BaseModel
from email_validator import validate_email, EmailNotValidError


# Granular platform rights assignable to a "Staff" account. A super admin
# implicitly holds all of them; a staff member holds an explicit subset.
#   - manage_companies : create/update/deactivate/delete hosted companies & trainers
#   - manage_users     : create/deactivate/reactivate/delete user accounts
#   - manage_trainings : manage trainings, ateliers, sessions and agenda events
#   - manage_news      : publish economic-watch news and edit the landing page
STAFF_PERMISSIONS = (
    'manage_companies',
    'manage_users',
    'manage_trainings',
    'manage_news',
)


def validate_permissions(values):
    """Validate and normalise a list of staff permission keys.

    Args:
        values: An iterable of permission keys, or ``None``.

    Returns:
        list[str]: De-duplicated, ordered list of valid permission keys.

    Raises:
        TypeError: If *values* is not an iterable of strings.
        ValueError: If any value is not a known permission key.
    """
    if values is None:
        return []
    if isinstance(values, str) or not hasattr(values, '__iter__'):
        raise TypeError("Permissions must be a list of permission keys.")
    cleaned = []
    for value in values:
        if not isinstance(value, str):
            raise TypeError("Each permission must be a string.")
        key = value.strip()
        if key not in STAFF_PERMISSIONS:
            raise ValueError(f"Unknown permission: {value!r}")
        if key not in cleaned:
            cleaned.append(key)
    return cleaned


class User(BaseModel):
    """User model with property-based validation.

    Password hashing is intentionally not performed at this layer and must
    be handled by the service or facade layer before persistence.

    Attributes:
        email (str): Lowercase validated email address.
        password (str): Plaintext password (8–256 chars). Not hashed here.
        first_name (str | None): Optional first name (max 100 chars).
        last_name (str | None): Optional last name (max 100 chars).
        phone (str | None): Optional phone number.
        profile_picture (str | None): Optional URL/path to profile picture.
        business_card (str | None): Optional URL/path to business card image.
        is_super_admin (bool): Super-admin flag, defaults to False.
        company_id (str | None): Optional owning company UUID.
    """

    def __init__(self, email, password, first_name=None, last_name=None, **kwargs):
        super().__init__(**kwargs)
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.phone = kwargs.get("phone")
        self.profile_picture = kwargs.get("profile_picture")
        self.business_card = kwargs.get("business_card")
        self.is_super_admin = kwargs.get("is_super_admin", False)
        self.company_id = kwargs.get("company_id")

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, email):
        if not isinstance(email, str):
            raise TypeError("Email must be a string.")
        email = email.strip()
        if not email:
            raise ValueError("Email cannot be empty.")
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            raise ValueError("Invalid email address format.")
        if len(email) > 254:
            raise ValueError("Email must be 254 characters or fewer")
        self._email = email.lower()

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, pwd):
        if not isinstance(pwd, str):
            raise TypeError("Password must be a string.")
        if len(pwd) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(pwd) > 256:
            raise ValueError("Password must be 256 characters or fewer")
        self._password = pwd

    @property
    def first_name(self):
        return self._first_name

    @first_name.setter
    def first_name(self, first_name):
        if first_name is None:
            self._first_name = None
            return
        if not isinstance(first_name, str):
            raise TypeError("First name must be a string.")
        first_name = first_name.strip()
        if not first_name:
            raise ValueError("First name cannot be empty.")
        if len(first_name) > 100:
            raise ValueError("First name cannot exceed 100 characters.")
        self._first_name = first_name

    @property
    def last_name(self):
        return self._last_name

    @last_name.setter
    def last_name(self, last_name):
        if last_name is None:
            self._last_name = None
            return
        if not isinstance(last_name, str):
            raise TypeError("Last name must be a string.")
        last_name = last_name.strip()
        if not last_name:
            raise ValueError("Last name cannot be empty.")
        if len(last_name) > 100:
            raise ValueError("Last name cannot exceed 100 characters.")
        self._last_name = last_name

    @staticmethod
    def validate_first_name(value):
        """Validate and normalise a candidate first name.

        Args:
            value (str | None): The first name to validate.

        Returns:
            str | None: Stripped first name, or ``None`` if *value* is ``None``.

        Raises:
            TypeError: If *value* is not a string.
            ValueError: If *value* is empty or exceeds 100 characters.
        """
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("First name must be a string.")
        v = value.strip()
        if not v:
            raise ValueError("First name cannot be empty.")
        if len(v) > 100:
            raise ValueError("First name cannot exceed 100 characters.")
        return v

    @staticmethod
    def validate_last_name(value):
        """Validate and normalise a candidate last name.

        Args:
            value (str | None): The last name to validate.

        Returns:
            str | None: Stripped last name, or ``None`` if *value* is ``None``.

        Raises:
            TypeError: If *value* is not a string.
            ValueError: If *value* is empty or exceeds 100 characters.
        """
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("Last name must be a string.")
        v = value.strip()
        if not v:
            raise ValueError("Last name cannot be empty.")
        if len(v) > 100:
            raise ValueError("Last name cannot exceed 100 characters.")
        return v
