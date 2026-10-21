import pytest
from fastapi import Depends

from app.api.deps import require_permission, require_super_admin
from app.core.permissions import Permission, can_manage_company, validate_permissions
from app.models.enums import UserRole


@pytest.fixture(autouse=True)
def routes(client):
    @client.app.get("/_users", dependencies=[Depends(require_permission(Permission.MANAGE_USERS))])
    def users_route():
        return {}

    @client.app.get("/_root", dependencies=[Depends(require_super_admin)])
    def root_route():
        return {}


def test_super_admin_has_everything(client, make_user, login):
    make_user(role=UserRole.SUPER_ADMIN)
    headers = login()
    assert client.get("/_users", headers=headers).status_code == 200
    assert client.get("/_root", headers=headers).status_code == 200


def test_staff_only_granted_permissions(client, make_user, login):
    make_user(role=UserRole.STAFF, permissions=["manage_users"])
    headers = login()
    assert client.get("/_users", headers=headers).status_code == 200
    assert client.get("/_root", headers=headers).status_code == 403


def test_staff_without_permission_forbidden(client, make_user, login):
    make_user(role=UserRole.STAFF, permissions=["manage_news"])
    response = client.get("/_users", headers=login())
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_member_forbidden(client, make_user, login):
    make_user()
    assert client.get("/_users", headers=login()).status_code == 403


def test_anonymous_unauthorized(client):
    assert client.get("/_users").status_code == 401


def test_validate_permissions():
    assert validate_permissions([" manage_news", "manage_news", "manage_users"]) == [
        "manage_news",
        "manage_users",
    ]
    assert validate_permissions(None) == []
    with pytest.raises(ValueError):
        validate_permissions(["fly"])


def test_can_manage_company(make_user, make_company):
    mine, other = make_company("Mine"), make_company("Other")
    admin = make_user("a@x.fr", company_id=mine.id, is_company_admin=True)
    plain = make_user("b@x.fr", company_id=mine.id)
    staff = make_user("c@x.fr", role=UserRole.STAFF, permissions=["manage_companies"])
    assert can_manage_company(admin, mine.id)
    assert not can_manage_company(admin, other.id)
    assert not can_manage_company(plain, mine.id)
    assert can_manage_company(staff, other.id)
