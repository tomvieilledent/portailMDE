#!/usr/bin/env python3
"""Domain model for companies."""

import re
import uuid

from email_validator import EmailNotValidError, validate_email

from .base import BaseModel

# Matches an explicit URL scheme like "http://", "https://", "ftp://".
_URL_SCHEME_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9+.-]*://')


class Company(BaseModel):
    """Company model with field validation.

    Attributes:
        name (str): Company display name (required, max 200 chars).
        description (str | None): Optional description (max 2000 chars).
        website_link (str | None): Optional website URL (max 512 chars).
        company_picture (str | None): Optional picture path/URL (max 512 chars).
        admin_email (str | None): Optional admin email used to resolve an admin user.
        admin_id (str | None): Optional resolved admin user UUID.
    """

    def __init__(
        self,
        name,
        admin_email=None,
        admin_id=None,
        description=None,
        location=None,
        website_link=None,
        company_picture=None,
        kind='company',
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.name = name
        self.description = description
        self.location = location
        self.website_link = website_link
        self.company_picture = company_picture
        self.admin_email = admin_email
        self.admin_id = admin_id
        self.kind = kind

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        if value is None:
            self._location = None
            return
        if not isinstance(value, str):
            raise TypeError("Location must be a string")
        if len(value) > 200:
            raise ValueError("Location must be 200 characters or fewer")
        self._location = value.strip()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise TypeError("Company name must be a string")
        value = value.strip()
        if not value:
            raise ValueError("Company name cannot be empty")
        if len(value) > 200:
            raise ValueError("Company name must be 200 characters or fewer")
        self._name = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        if value is None:
            self._description = None
            return
        if not isinstance(value, str):
            raise TypeError("Description must be a string")
        if len(value) > 2000:
            raise ValueError("Description must be 2000 characters or fewer")
        self._description = value.strip()

    @property
    def website_link(self):
        return self._website_link

    @website_link.setter
    def website_link(self, value):
        if value is None:
            self._website_link = None
            return
        if not isinstance(value, str):
            raise TypeError("Website link must be a string URL")
        value = value.strip()
        if not value:
            self._website_link = None
            return
        # Accept links typed without a scheme (e.g. "www.exemple.com") by
        # defaulting to https://, so the stored URL is absolute and clickable.
        if not _URL_SCHEME_RE.match(value):
            value = 'https://' + value
        if len(value) > 512:
            raise ValueError("Website link must be 512 characters or fewer")
        self._website_link = value

    @property
    def company_picture(self):
        return self._company_picture

    @company_picture.setter
    def company_picture(self, value):
        if value is None:
            self._company_picture = None
            return
        if not isinstance(value, str):
            raise TypeError("Company picture must be a string address")
        value = value.strip()
        if not value:
            raise ValueError("Company picture cannot be empty")
        if len(value) > 512:
            raise ValueError("Company picture must be 512 characters or fewer")
        self._company_picture = value

    @property
    def kind(self):
        return self._kind

    @kind.setter
    def kind(self, value):
        # Distingue une entreprise hébergée d'un formateur. Défaut : 'company'.
        if value is None or value == '':
            self._kind = 'company'
            return
        if not isinstance(value, str):
            raise TypeError("Kind must be a string")
        value = value.strip().lower()
        if value not in ('company', 'trainer'):
            raise ValueError("Kind must be 'company' or 'trainer'")
        self._kind = value

    @property
    def admin_id(self):
        return self._admin_id

    @admin_id.setter
    def admin_id(self, value):
        if value is None:
            self._admin_id = None
            return
        if isinstance(value, uuid.UUID):
            self._admin_id = str(value)
            return
        if not isinstance(value, str):
            raise TypeError("Admin ID must be a string UUID")
        value = value.strip()
        if not value:
            raise ValueError("Admin ID cannot be empty")
        try:
            uuid.UUID(value)
        except ValueError as exc:
            raise ValueError("Admin ID must be a valid UUID") from exc
        self._admin_id = value

    @property
    def admin_email(self):
        return self._admin_email

    @admin_email.setter
    def admin_email(self, value):
        if value is None:
            self._admin_email = None
            return
        if not isinstance(value, str):
            raise TypeError("Admin email must be a string")
        value = value.strip()
        if not value:
            raise ValueError("Admin email cannot be empty")
        if len(value) > 254:
            raise ValueError("Admin email must be 254 characters or fewer")
        try:
            validate_email(value, check_deliverability=False)
        except EmailNotValidError as exc:
            raise ValueError("Admin email must be a valid email address") from exc
        self._admin_email = value.lower()
