import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.permissions import validate_permissions
from app.models.enums import UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    first_name: str | None
    last_name: str | None
    job_title: str | None
    phone: str | None
    avatar_path: str | None
    business_card_path: str | None
    role: UserRole
    is_company_admin: bool
    permissions: list[str]
    company_id: uuid.UUID | None
    is_active: bool
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    job_title: str | None = Field(None, max_length=120)
    phone: str | None = Field(None, max_length=30)
    company_id: uuid.UUID | None = None
    is_company_admin: bool = False
    role: UserRole = UserRole.MEMBER
    permissions: list[str] = []

    _check_permissions = field_validator("permissions")(lambda v: validate_permissions(v))


class UserUpdate(BaseModel):
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    job_title: str | None = Field(None, max_length=120)
    phone: str | None = Field(None, max_length=30)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=256)


class RoleUpdate(BaseModel):
    role: UserRole
    permissions: list[str] = []

    _check_permissions = field_validator("permissions")(lambda v: validate_permissions(v))


class CompanyAdminUpdate(BaseModel):
    is_company_admin: bool
