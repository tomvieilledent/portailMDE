"""API integration tests for platform staff accounts and granular rights.

Covers:
- A super admin creating another super admin (POST /users {is_super_admin}).
- A super admin creating a staff account with a subset of permissions.
- Staff/permission flags are ignored when the requester is not a super admin.
- PATCH /users/<id>/permissions (super admin only).
- Permission enforcement: a staff member with ``manage_companies`` may create
  a company, while one without it is forbidden; staff cannot mint super admins.
"""

from backend.api.errors import ERROR_CODES
from tests.helpers import assert_error, assert_ok


def _create(client, headers, email, **over):
    body = {'email': email, 'password': 'password123'}
    body.update(over)
    return client.post('/users', headers=headers, json=body)


def _login(client, email, password='password123'):
    resp = client.post('/auth/login', json={'email': email, 'password': password})
    assert resp.status_code == 200
    token = resp.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def test_super_admin_creates_super_admin(seeded_context):
    client = seeded_context['client']
    resp = _create(client, seeded_context['admin_headers'],
                   'super2@example.com', is_super_admin=True)
    assert_ok(resp, 201)
    user = resp.get_json()['user']
    assert user['is_super_admin'] is True
    # The new super admin can in turn create accounts.
    headers = _login(client, 'super2@example.com')
    assert_ok(_create(client, headers, 'created.by.super2@example.com'), 201)


def test_super_admin_creates_staff_with_permissions(seeded_context):
    client = seeded_context['client']
    resp = _create(client, seeded_context['admin_headers'], 'staff@example.com',
                   is_staff=True, permissions=['manage_companies', 'manage_users'])
    assert_ok(resp, 201)
    user = resp.get_json()['user']
    assert user['is_staff'] is True
    assert user['is_super_admin'] is False
    assert sorted(user['permissions']) == ['manage_companies', 'manage_users']


def test_create_rejects_unknown_permission(seeded_context):
    client = seeded_context['client']
    resp = _create(client, seeded_context['admin_headers'], 'staff2@example.com',
                   is_staff=True, permissions=['manage_everything'])
    assert_error(resp, 400, ERROR_CODES['VALIDATION_ERROR'])


def test_non_super_admin_cannot_set_privileged_flags(seeded_context):
    """A staff member with manage_users cannot escalate created accounts."""
    client = seeded_context['client']
    # Seed a staff member who may manage users.
    staff = _create(client, seeded_context['admin_headers'], 'usermgr@example.com',
                    is_staff=True, permissions=['manage_users']).get_json()['user']
    assert staff['permissions'] == ['manage_users']
    headers = _login(client, 'usermgr@example.com')
    # They try to mint a super admin + staff — flags must be ignored.
    resp = _create(client, headers, 'escalated@example.com',
                   is_super_admin=True, is_staff=True,
                   permissions=['manage_companies'])
    assert_ok(resp, 201)
    created = resp.get_json()['user']
    assert created['is_super_admin'] is False
    assert created['is_staff'] is False
    assert created['permissions'] == []


def test_permissions_endpoint_super_admin_only(seeded_context):
    client = seeded_context['client']
    member_id = seeded_context['member_user']['id']
    # Member cannot assign rights.
    resp = client.patch(f'/users/{member_id}/permissions',
                        headers=seeded_context['member_headers'],
                        json={'is_staff': True, 'permissions': ['manage_news']})
    assert_error(resp, 403, ERROR_CODES['FORBIDDEN'])
    # Super admin promotes the member to staff.
    resp = client.patch(f'/users/{member_id}/permissions',
                        headers=seeded_context['admin_headers'],
                        json={'is_staff': True, 'permissions': ['manage_news']})
    assert_ok(resp, 200)
    assert resp.get_json()['user']['permissions'] == ['manage_news']
    # Clearing is_staff drops the permissions.
    resp = client.patch(f'/users/{member_id}/permissions',
                        headers=seeded_context['admin_headers'],
                        json={'is_staff': False, 'permissions': ['manage_news']})
    assert_ok(resp, 200)
    assert resp.get_json()['user']['is_staff'] is False
    assert resp.get_json()['user']['permissions'] == []


def test_staff_manage_companies_permission_enforced(seeded_context):
    client = seeded_context['client']
    # Staff WITH manage_companies can create a company.
    _create(client, seeded_context['admin_headers'], 'cmgr@example.com',
            is_staff=True, permissions=['manage_companies'])
    headers = _login(client, 'cmgr@example.com')
    resp = client.post('/companies', headers=headers,
                       json={'name': 'Staff Co', 'admin_email': 'member@example.com'})
    assert_ok(resp, 201)

    # Staff WITHOUT manage_companies is forbidden.
    _create(client, seeded_context['admin_headers'], 'newsmgr@example.com',
            is_staff=True, permissions=['manage_news'])
    headers2 = _login(client, 'newsmgr@example.com')
    resp2 = client.post('/companies', headers=headers2,
                        json={'name': 'Nope Co', 'admin_email': 'nc@example.com'})
    assert_error(resp2, 403, ERROR_CODES['FORBIDDEN'])


def test_staff_cannot_delete_or_deactivate_super_admin(seeded_context):
    """A staff member with manage_users may manage regular users but must not
    delete or deactivate a super-admin account."""
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']

    # Staff member holding manage_users.
    _create(client, admin_headers, 'umgr@example.com',
            is_staff=True, permissions=['manage_users'])
    staff_headers = _login(client, 'umgr@example.com')

    # A second super admin to target.
    target = _create(client, admin_headers, 'super.target@example.com',
                     is_super_admin=True).get_json()['user']

    # Staff cannot delete the super admin.
    resp = client.delete(f"/users/{target['id']}", headers=staff_headers)
    assert_error(resp, 403, ERROR_CODES['FORBIDDEN'])

    # Staff cannot deactivate the super admin either.
    resp = client.patch(f"/users/{target['id']}/deactivate", headers=staff_headers)
    assert_error(resp, 403, ERROR_CODES['FORBIDDEN'])

    # But the staff member CAN delete a regular user.
    regular = _create(client, admin_headers, 'regular@example.com').get_json()['user']
    resp = client.delete(f"/users/{regular['id']}", headers=staff_headers)
    assert_ok(resp, 200)

    # And a super admin can still delete another super admin.
    resp = client.delete(f"/users/{target['id']}", headers=admin_headers)
    assert_ok(resp, 200)
