from typing import Any, cast

import pytest

from backend.api.errors import ERROR_CODES
from tests.helpers import assert_error, make_text


def test_home_and_openapi_routes(app_bundle):
    client = app_bundle['client']

    home = client.get('/status')
    spec = client.get('/openapi.json')

    assert home.status_code == 200
    assert home.get_json() == {'ok': True}
    assert spec.status_code == 200
    assert 'openapi' in spec.get_json()


def test_auth_register_login_refresh_logout_and_revoke(app_bundle):
    client = app_bundle['client']

    register = client.post('/auth/register', json={
        'email': 'new.user@example.com',
        'password': 'password123',
        'first_name': 'New',
    })
    assert register.status_code == 201
    register_payload = register.get_json()
    assert register_payload['user']['email'] == 'new.user@example.com'
    assert register_payload['user']['first_name'] == 'New'
    assert 'access_token' in register_payload
    assert 'refresh_token' in register_payload

    duplicate = client.post('/auth/register', json={
        'email': 'new.user@example.com',
        'password': 'password123',
    })
    assert_error(duplicate, 409, ERROR_CODES['CONFLICT'])

    login = client.post('/auth/login', json={
        'email': 'new.user@example.com',
        'password': 'password123',
    })
    assert login.status_code == 200
    login_payload = login.get_json()
    assert login_payload['user']['email'] == 'new.user@example.com'

    refresh = client.post('/auth/refresh', headers={
        'Authorization': f"Bearer {login_payload['refresh_token']}"
    })
    assert refresh.status_code == 200
    assert 'access_token' in refresh.get_json()

    logout = client.post('/auth/logout', headers={
        'Authorization': f"Bearer {login_payload['access_token']}"
    })
    assert logout.status_code == 200
    assert logout.get_json() == {'msg': 'logged out'}

    revoked = client.get('/users/me', headers={
        'Authorization': f"Bearer {login_payload['access_token']}"
    })
    assert revoked.status_code == 401
    assert revoked.get_json()['error']['code'] in {
        ERROR_CODES['TOKEN_REVOKED'],
        ERROR_CODES['INVALID_TOKEN'],
    }


def test_auth_rejects_bad_payloads_and_invalid_credentials(app_bundle):
    client = app_bundle['client']

    missing = client.post(
        '/auth/register', json={'email': 'missing-password@example.com'})
    assert_error(missing, 400, ERROR_CODES['BAD_REQUEST'])

    invalid_email = client.post('/auth/register', json={
        'email': 'bad-email',
        'password': 'password123',
    })
    assert_error(invalid_email, 400, ERROR_CODES['VALIDATION_ERROR'])

    bad_login = client.post('/auth/login', json={
        'email': 'ghost@example.com',
        'password': 'password123',
    })
    assert_error(bad_login, 401, ERROR_CODES['INVALID_CREDENTIALS'])


@pytest.mark.parametrize(
    'payload, status, code',
    [
        ({'email': '', 'password': 'password123'},
         400, ERROR_CODES['BAD_REQUEST']),
        ({'email': 'user@example.com', 'password': ''},
         400, ERROR_CODES['BAD_REQUEST']),
        ({'email': 123, 'password': 'password123'},
         400, ERROR_CODES['VALIDATION_ERROR']),
        ({'email': 'user@example.com', 'password': 123},
         400, ERROR_CODES['VALIDATION_ERROR']),
        ({'email': make_text(255) + '@example.com',
         'password': 'password123'}, 400, ERROR_CODES['VALIDATION_ERROR']),
    ],
)
def test_auth_register_field_validation_cases(app_bundle, payload, status, code):
    client = app_bundle['client']

    response = client.post('/auth/register', json=payload)
    assert_error(response, status, code)


def test_protected_route_requires_auth(app_bundle):
    client = app_bundle['client']

    response = client.get('/users')
    assert_error(response, 401, ERROR_CODES['UNAUTHORIZED'])


def test_user_crud_and_profile_endpoints(seeded_context):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']
    member_id = seeded_context['member_user']['id']

    me = client.get('/users/me', headers=admin_headers)
    assert me.status_code == 200
    assert me.get_json()['user']['email'] == 'admin@example.com'

    updated_me = client.patch('/users/me', headers=admin_headers, json={
        'first_name': 'Updated',
        'last_name': 'Admin',
    })
    assert updated_me.status_code == 200
    assert updated_me.get_json()['user']['first_name'] == 'Updated'

    create_user = client.post('/users', headers=admin_headers, json={
        'email': 'created@example.com',
        'password': 'password123',
        'first_name': 'Created',
        'last_name': 'User',
        'company_id': None,
        'is_super_admin': False,
    })
    assert create_user.status_code == 201
    created_user_id = create_user.get_json()['user']['id']

    list_users = client.get('/users', headers=admin_headers)
    assert list_users.status_code == 200
    assert len(list_users.get_json()['users']) >= 4

    get_user = client.get(f'/users/{created_user_id}', headers=admin_headers)
    assert get_user.status_code == 200
    assert get_user.get_json()['user']['email'] == 'created@example.com'

    replace_user = client.put(f'/users/{created_user_id}', headers=admin_headers, json={
        'first_name': 'Replaced',
        'last_name': 'Name',
    })
    assert replace_user.status_code == 200
    assert replace_user.get_json()['user']['first_name'] == 'Replaced'

    patch_user = client.patch(f'/users/{created_user_id}', headers=admin_headers, json={
        'phone': '+33600000000',
    })
    assert patch_user.status_code == 200
    assert patch_user.get_json()['user']['phone'] == '+33600000000'

    reset_password = client.post(f'/users/{created_user_id}/reset-password', headers=admin_headers, json={
        'password': 'newpassword123',
    })
    assert reset_password.status_code == 200

    deactivate_user = client.patch(
        f'/users/{created_user_id}/deactivate', headers=admin_headers)
    assert deactivate_user.status_code == 200
    assert deactivate_user.get_json() == {'msg': 'deactivated'}

    delete_user = client.delete(
        f'/users/{created_user_id}', headers=admin_headers)
    assert delete_user.status_code == 200
    assert delete_user.get_json() == {'msg': 'user deleted'}

    deleted_user = client.get(
        f'/users/{created_user_id}', headers=admin_headers)
    assert_error(deleted_user, 404, ERROR_CODES['NOT_FOUND'])

    filtered_users = client.get(
        '/users', headers=admin_headers, query_string={'company_id': 'missing-company'})
    assert filtered_users.status_code == 200
    assert filtered_users.get_json()['users'] == []

    member_profile = client.get(f'/users/{member_id}', headers=admin_headers)
    assert member_profile.status_code == 200


@pytest.mark.parametrize(
    'payload, status, code',
    [
        ({'email': 'missing-password@example.com'},
         400, ERROR_CODES['BAD_REQUEST']),
        ({'email': 'bad-email', 'password': 'password123'},
         400, ERROR_CODES['VALIDATION_ERROR']),
        ({'email': 123, 'password': 'password123'},
         400, ERROR_CODES['VALIDATION_ERROR']),
        ({'email': 'user@example.com', 'password': 123},
         400, ERROR_CODES['VALIDATION_ERROR']),
        ({'email': 'user@example.com', 'password': make_text(257)},
         400, ERROR_CODES['VALIDATION_ERROR']),
    ],
)
def test_user_create_field_validation_cases(seeded_context, payload, status, code):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']

    response = client.post('/users', headers=admin_headers, json=payload)
    assert_error(response, status, code)


def test_company_flow_and_admin_email_requirement(seeded_context):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']
    company_admin_id = seeded_context['company_admin_user']['id']

    missing_admin_email = client.post('/companies', headers=admin_headers, json={
        'name': 'No Admin Email',
    })
    assert_error(missing_admin_email, 400, ERROR_CODES['BAD_REQUEST'])

    invalid_admin_email = client.post('/companies', headers=admin_headers, json={
        'name': 'Invalid Email Company',
        'admin_email': 'bad-email',
    })
    assert_error(invalid_admin_email, 400, ERROR_CODES['VALIDATION_ERROR'])

    create_company = client.post('/companies', headers=admin_headers, json={
        'name': 'My Company',
        'description': 'Demo company',
        'website_link': 'https://example.com',
        'admin_email': 'company.admin@example.com',
    })
    assert create_company.status_code == 201
    company = create_company.get_json()['company']
    company_id = company['id']
    assert company['admin_email'] == 'company.admin@example.com'
    assert company['admin_id'] == company_admin_id

    list_companies = client.get('/companies', headers=admin_headers)
    assert list_companies.status_code == 200
    assert len(list_companies.get_json()['companies']) >= 1

    get_company = client.get(f'/companies/{company_id}', headers=admin_headers)
    assert get_company.status_code == 200
    assert get_company.get_json()['company']['id'] == company_id

    patch_company = client.patch(f'/companies/{company_id}', headers=admin_headers, json={
        'description': 'Updated description',
    })
    assert patch_company.status_code == 200
    from backend.persistence.db import SessionLocal
    from backend.persistence.models import Company as ORMCompany

    db = SessionLocal()
    try:
        stored_company = db.query(ORMCompany).filter(
            ORMCompany.id == company_id).first()
        assert stored_company is not None
        stored_company = cast(Any, stored_company)
        assert stored_company.description == 'Updated description'
    finally:
        db.close()

    company_users = client.get(
        f'/companies/{company_id}/users', headers=admin_headers)
    assert company_users.status_code == 200
    # Creating a company assigns its admin to it (auto employee count).
    users_before = company_users.get_json()['users']
    assert len(users_before) == 1
    assert users_before[0]['email'] == 'company.admin@example.com'

    assign_user = client.post(
        f'/companies/{company_id}/users/{seeded_context["member_user"]["id"]}', headers=admin_headers)
    assert assign_user.status_code == 200
    from backend.persistence.db import SessionLocal
    from backend.persistence.models import User as ORMUser

    db = SessionLocal()
    try:
        stored_user = db.query(ORMUser).filter(
            ORMUser.id == seeded_context['member_user']['id']).first()
        assert stored_user is not None
        stored_user = cast(Any, stored_user)
        assert stored_user.company_id == company_id
    finally:
        db.close()

    company_users_after_assign = client.get(
        f'/companies/{company_id}/users', headers=admin_headers)
    assert company_users_after_assign.status_code == 200
    # The company admin + the freshly assigned member.
    assert len(company_users_after_assign.get_json()['users']) == 2

    remove_user = client.delete(
        f'/companies/{company_id}/users/{seeded_context["member_user"]["id"]}', headers=admin_headers)
    assert remove_user.status_code == 200
    db = SessionLocal()
    try:
        stored_user = db.query(ORMUser).filter(
            ORMUser.id == seeded_context['member_user']['id']).first()
        assert stored_user is not None
        stored_user = cast(Any, stored_user)
        assert stored_user.company_id is None
    finally:
        db.close()

    deactivate_company = client.patch(
        f'/companies/{company_id}/deactivate', headers=admin_headers)
    assert deactivate_company.status_code == 200
    assert deactivate_company.get_json() == {'msg': 'company deactivated'}

    list_filtered = client.get(
        '/users', headers=admin_headers, query_string={'company_id': company_id})
    assert list_filtered.status_code == 200


@pytest.mark.parametrize(
    'payload, status, code',
    [
        ({'name': ''}, 400, ERROR_CODES['BAD_REQUEST']),
        ({'name': 'Valid Company'}, 400, ERROR_CODES['BAD_REQUEST']),
        ({'name': 123, 'admin_email': 'admin@example.com'},
         400, ERROR_CODES['VALIDATION_ERROR']),
        ({'name': make_text(201), 'admin_email': 'admin@example.com'},
         400, ERROR_CODES['VALIDATION_ERROR']),
        ({'name': 'Valid Company', 'admin_email': ''},
         400, ERROR_CODES['BAD_REQUEST']),
        ({'name': 'Valid Company', 'admin_email': 123},
         400, ERROR_CODES['VALIDATION_ERROR']),
        ({'name': 'Valid Company', 'admin_email': make_text(255) +
         '@example.com'}, 400, ERROR_CODES['VALIDATION_ERROR']),
        ({'name': 'Valid Company', 'admin_email': 'missing@example.com'},
         400, ERROR_CODES['BAD_REQUEST']),
        ({'name': 'Valid Company', 'admin_email': 'company.admin@example.com',
         'admin_id': 'bad-uuid'}, 400, ERROR_CODES['VALIDATION_ERROR']),
    ],
)
def test_company_create_field_validation_cases(seeded_context, payload, status, code):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']

    response = client.post('/companies', headers=admin_headers, json=payload)
    assert_error(response, status, code)


def test_training_permissions_and_crud(seeded_context):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']
    company_admin_headers = seeded_context['company_admin_headers']

    company = client.post('/companies', headers=admin_headers, json={
        'name': 'Training Company',
        'admin_email': 'company.admin@example.com',
    }).get_json()['company']

    forbidden = client.post('/trainings', headers=company_admin_headers, json={
        'title': 'Docker Basics',
        'company_id': company['id'],
    })
    assert_error(forbidden, 403, ERROR_CODES['FORBIDDEN'])

    create_training = client.post('/trainings', headers=admin_headers, json={
        'title': 'Docker Basics',
        'company_id': company['id'],
        'description': 'Intro to Docker',
    })
    assert create_training.status_code == 201
    training = create_training.get_json()['training']
    training_id = training['id']
    assert training['title'] == 'Docker Basics'
    assert training['company_id'] == company['id']

    list_trainings = client.get('/trainings', headers=admin_headers)
    assert list_trainings.status_code == 200
    assert len(list_trainings.get_json()['trainings']) >= 1

    get_training = client.get(
        f'/trainings/{training_id}', headers=admin_headers)
    assert get_training.status_code == 200

    patch_training = client.patch(f'/trainings/{training_id}', headers=admin_headers, json={
        'description': 'Updated description',
    })
    assert patch_training.status_code == 200
    from backend.persistence.db import SessionLocal
    from backend.persistence.models import Training as ORMTraining

    db = SessionLocal()
    try:
        stored_training = db.query(ORMTraining).filter(
            ORMTraining.id == training_id).first()
        assert stored_training is not None
        stored_training = cast(Any, stored_training)
        assert stored_training.description == 'Updated description'
    finally:
        db.close()


def test_training_category_type_and_documents(seeded_context):
    """Free-text category, formation/atelier type, and document attachments."""
    from io import BytesIO
    from pathlib import Path
    from backend.api.uploads import UPLOAD_ROOT

    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']

    # Free-text category + explicit atelier type persist.
    created = client.post('/trainings', headers=admin_headers, json={
        'title': 'Atelier Cybersécurité', 'category': 'Cybersécurité', 'type': 'atelier',
    })
    assert created.status_code == 201
    training = created.get_json()['training']
    assert training['category'] == 'Cybersécurité'
    assert training['type'] == 'atelier'
    assert training['documents'] == []

    # Type defaults to 'formation' when omitted.
    default_type = client.post('/trainings', headers=admin_headers, json={
        'title': 'Formation Marketing', 'category': 'Marketing',
    }).get_json()['training']
    assert default_type['type'] == 'formation'

    # Invalid type is rejected.
    bad = client.post('/trainings', headers=admin_headers, json={
        'title': 'X', 'type': 'webinaire'})
    assert_error(bad, 400, ERROR_CODES['VALIDATION_ERROR'])

    # Multipart create with an attached document.
    with_doc = client.post('/trainings', headers=admin_headers, data={
        'title': 'Atelier avec plaquette', 'category': 'Design', 'type': 'atelier',
        'document_file': (BytesIO(b'%PDF-1.4 fake brochure'), 'plaquette.pdf'),
    }, content_type='multipart/form-data')
    assert with_doc.status_code == 201
    doc_training = with_doc.get_json()['training']
    assert len(doc_training['documents']) == 1
    doc_path = doc_training['documents'][0]
    assert doc_path.startswith('/uploads/trainings/documents/')
    assert doc_path.endswith('__plaquette.pdf')
    on_disk = UPLOAD_ROOT / Path(doc_path.lstrip('/')).relative_to('uploads')
    assert on_disk.exists()

    # Removing the document detaches it and deletes the file.
    removed = client.delete(f"/trainings/{doc_training['id']}/documents",
                            headers=admin_headers, json={'path': doc_path})
    assert removed.status_code == 200
    assert removed.get_json()['training']['documents'] == []
    assert not on_disk.exists()

    # A non-super-admin cannot remove documents.
    forbidden = client.delete(f"/trainings/{doc_training['id']}/documents",
                              headers=seeded_context['member_headers'], json={'path': doc_path})
    assert_error(forbidden, 403, ERROR_CODES['FORBIDDEN'])


@pytest.mark.parametrize(
    'payload',
    [
        ({'first_name': '', 'last_name': 'Valid'}),
        ({'first_name': '   ', 'last_name': 'Valid'}),
        ({'first_name': 123, 'last_name': 'Valid'}),
        ({'first_name': 'A' * 101, 'last_name': 'Valid'}),
        ({'first_name': 'Valid', 'last_name': ''}),
        ({'first_name': 'Valid', 'last_name': '   '}),
        ({'first_name': 'Valid', 'last_name': 123}),
        ({'first_name': 'Valid', 'last_name': 'B' * 101}),
    ],
)
def test_user_update_name_validation_cases(seeded_context, payload):
    """PUT and PATCH to update user names must validate inputs."""
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']

    # create a user to operate on
    create_user = client.post('/users', headers=admin_headers, json={
        'email': 'to.update@example.com',
        'password': 'password123',
        'first_name': 'Initial',
        'last_name': 'Name',
    })
    assert create_user.status_code == 201
    user_id = create_user.get_json()['user']['id']

    # PUT should reject invalid payloads
    resp_put = client.put(f'/users/{user_id}',
                          headers=admin_headers, json=payload)
    assert_error(resp_put, 400, ERROR_CODES['VALIDATION_ERROR'])

    # PATCH should also reject when provided
    resp_patch = client.patch(
        f'/users/{user_id}', headers=admin_headers, json=payload)
    assert_error(resp_patch, 400, ERROR_CODES['VALIDATION_ERROR'])

    # name validation assertions complete


@pytest.mark.parametrize(
    'payload',
    [
        ({'first_name': ''}),
        ({'first_name': '   '}),
        ({'first_name': 123}),
        ({'first_name': 'A' * 101}),
        ({'last_name': ''}),
        ({'last_name': '   '}),
        ({'last_name': 123}),
        ({'last_name': 'B' * 101}),
    ],
)
def test_me_patch_name_validation_cases(seeded_context, payload):
    """PATCH /users/me should validate name inputs like the user endpoints."""
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']

    resp = client.patch('/users/me', headers=admin_headers, json=payload)
    assert_error(resp, 400, ERROR_CODES['VALIDATION_ERROR'])


@pytest.mark.parametrize(
    'payload, status, code',
    [
        ({}, 400, ERROR_CODES['BAD_REQUEST']),
        ({'title': ''}, 400, ERROR_CODES['BAD_REQUEST']),
        ({'title': 123}, 400, ERROR_CODES['VALIDATION_ERROR']),
        ({'title': make_text(201)}, 400, ERROR_CODES['VALIDATION_ERROR']),
        ({'title': 'Docker Basics', 'description': 123},
         400, ERROR_CODES['VALIDATION_ERROR']),
        ({'title': 'Docker Basics', 'description': make_text(2001)},
         400, ERROR_CODES['VALIDATION_ERROR']),
        ({'title': 'Docker Basics', 'picture': 123},
         400, ERROR_CODES['VALIDATION_ERROR']),
        ({'title': 'Docker Basics', 'picture': make_text(513)},
         400, ERROR_CODES['VALIDATION_ERROR']),
    ],
)
def test_training_create_field_validation_cases(seeded_context, payload, status, code):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']

    response = client.post('/trainings', headers=admin_headers, json=payload)
    assert_error(response, status, code)


def test_user_deactivate_and_delete_permissions(seeded_context):
    """Self-deactivation is allowed; deleting/deactivating others is admin-only."""
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']
    member_headers = seeded_context['member_headers']
    member_id = seeded_context['member_user']['id']
    other_id = seeded_context['company_admin_user']['id']

    # A member may not deactivate another user.
    forbidden = client.patch(f'/users/{other_id}/deactivate', headers=member_headers)
    assert_error(forbidden, 403, ERROR_CODES['FORBIDDEN'])

    # A member may not delete anyone (not even themselves) — delete is super-admin only.
    forbidden_delete = client.delete(f'/users/{member_id}', headers=member_headers)
    assert_error(forbidden_delete, 403, ERROR_CODES['FORBIDDEN'])

    # A member may deactivate their own account.
    self_deactivate = client.patch(f'/users/{member_id}/deactivate', headers=member_headers)
    assert self_deactivate.status_code == 200
    assert self_deactivate.get_json() == {'msg': 'deactivated'}

    # A super admin may delete a user.
    deleted = client.delete(f'/users/{other_id}', headers=admin_headers)
    assert deleted.status_code == 200
    assert deleted.get_json() == {'msg': 'user deleted'}


def test_company_deactivate_and_delete_permissions(seeded_context):
    """Company admin may deactivate their company; only super admin may delete."""
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']
    company_admin_headers = seeded_context['company_admin_headers']
    member_headers = seeded_context['member_headers']
    company_admin_email = seeded_context['company_admin_user']['email']

    created = client.post('/companies', headers=admin_headers, json={
        'name': 'Acme', 'admin_email': company_admin_email,
    })
    assert created.status_code == 201
    company_id = created.get_json()['company']['id']

    # A plain member may neither deactivate nor delete the company.
    assert_error(client.patch(f'/companies/{company_id}/deactivate',
                              headers=member_headers), 403, ERROR_CODES['FORBIDDEN'])
    assert_error(client.delete(f'/companies/{company_id}',
                               headers=member_headers), 403, ERROR_CODES['FORBIDDEN'])

    # The company's own admin may deactivate it, but not delete it.
    assert_error(client.delete(f'/companies/{company_id}',
                               headers=company_admin_headers), 403, ERROR_CODES['FORBIDDEN'])
    deactivated = client.patch(f'/companies/{company_id}/deactivate',
                               headers=company_admin_headers)
    assert deactivated.status_code == 200
    assert deactivated.get_json() == {'msg': 'company deactivated'}

    # A super admin may permanently delete it.
    deleted = client.delete(f'/companies/{company_id}', headers=admin_headers)
    assert deleted.status_code == 200
    assert deleted.get_json() == {'msg': 'company deleted'}
    assert_error(client.get(f'/companies/{company_id}', headers=admin_headers),
                 404, ERROR_CODES['NOT_FOUND'])


def test_company_create_is_super_admin_only_with_location_and_count(seeded_context):
    """Only super admins create companies; location + employee_count are exposed."""
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']
    company_admin_headers = seeded_context['company_admin_headers']
    member_headers = seeded_context['member_headers']
    company_admin_email = seeded_context['company_admin_user']['email']

    # A company admin / member may not create a company.
    for headers in (company_admin_headers, member_headers):
        assert_error(client.post('/companies', headers=headers, json={
            'name': 'Nope', 'admin_email': company_admin_email,
        }), 403, ERROR_CODES['FORBIDDEN'])

    # A super admin can, and location persists.
    created = client.post('/companies', headers=admin_headers, json={
        'name': 'Gamma', 'admin_email': company_admin_email,
        'location': 'Rodez', 'description': 'desc', 'website_link': 'https://g.fr',
    })
    assert created.status_code == 201
    company = created.get_json()['company']
    assert company['location'] == 'Rodez'
    assert company['website_link'] == 'https://g.fr'
    # The admin is auto-attached to the company → employee_count == 1.
    assert company['employee_count'] == 1

    # A super admin keeps full control and may reuse an admin (the
    # single-active-company guard only applies to non-super-admins). A
    # scheme-less link is stored with https:// added automatically.
    no_scheme = client.post('/companies', headers=admin_headers, json={
        'name': 'Delta', 'admin_email': company_admin_email,
        'website_link': 'www.delta.fr',
    })
    assert no_scheme.status_code == 201
    assert no_scheme.get_json()['company']['website_link'] == 'https://www.delta.fr'


def test_company_admin_can_create_employee(seeded_context):
    """A company admin may create employees in their own company. A duplicate
    email returns a clear conflict message (not the generic create failure)."""
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']
    company_admin_email = seeded_context['company_admin_user']['email']
    company_admin_headers = seeded_context['company_admin_headers']
    member_email = seeded_context['member_user']['email']

    # Super admin makes the company_admin user the admin of a company.
    company = client.post('/companies', headers=admin_headers, json={
        'name': 'Patron Co', 'admin_email': company_admin_email,
    }).get_json()['company']

    # The company admin creates an employee -> attached to their company.
    created = client.post('/users', headers=company_admin_headers, json={
        'email': 'employee@patron.co', 'password': 'password123',
        'first_name': 'Emp', 'last_name': 'Loyee',
    })
    assert created.status_code == 201, created.get_json()
    new_user = created.get_json()['user']
    assert new_user['company_id'] == company['id']
    assert new_user['is_company_admin'] is False

    # Re-using an existing email yields a clear, specific 409.
    dup = client.post('/users', headers=company_admin_headers, json={
        'email': member_email, 'password': 'password123', 'first_name': 'Dup',
    })
    assert dup.status_code == 409
    body = dup.get_json()['error']
    assert body['code'] == ERROR_CODES['CONFLICT']
    assert body['message'] == 'a user with this email already exists'


def test_user_reactivate_permissions(seeded_context):
    """Only super admins may reactivate a deactivated user."""
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']
    company_admin_headers = seeded_context['company_admin_headers']
    member_headers = seeded_context['member_headers']
    member_id = seeded_context['member_user']['id']

    # Member deactivates their own account.
    assert client.patch(f'/users/{member_id}/deactivate',
                        headers=member_headers).status_code == 200

    # A non-super (company admin) cannot reactivate.
    assert_error(client.patch(f'/users/{member_id}/reactivate',
                              headers=company_admin_headers), 403, ERROR_CODES['FORBIDDEN'])

    # A super admin can.
    res = client.patch(f'/users/{member_id}/reactivate', headers=admin_headers)
    assert res.status_code == 200
    body = res.get_json()
    assert body['msg'] == 'reactivated'
    assert body['user']['is_active'] is True


def test_user_role_change_and_last_super_admin_guard(seeded_context):
    """Super admins toggle roles; the last active super admin can't be demoted."""
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']
    member_headers = seeded_context['member_headers']
    member_id = seeded_context['member_user']['id']
    admin_id = seeded_context['admin_user']['id']

    # A non-super may not change roles.
    assert_error(client.patch(f'/users/{member_id}/role', headers=member_headers,
                              json={'is_super_admin': True}), 403, ERROR_CODES['FORBIDDEN'])

    # A super admin promotes the member.
    promoted = client.patch(f'/users/{member_id}/role', headers=admin_headers,
                            json={'is_super_admin': True})
    assert promoted.status_code == 200
    assert promoted.get_json()['user']['is_super_admin'] is True

    # ...and can demote them back.
    demoted = client.patch(f'/users/{member_id}/role', headers=admin_headers,
                           json={'is_super_admin': False})
    assert demoted.status_code == 200
    assert demoted.get_json()['user']['is_super_admin'] is False

    # The seed admin is now the sole active super admin and cannot be demoted.
    assert_error(client.patch(f'/users/{admin_id}/role', headers=admin_headers,
                              json={'is_super_admin': False}), 403, ERROR_CODES['FORBIDDEN'])


def test_company_reactivate_permissions(seeded_context):
    """A company admin may reactivate their own company; a member may not."""
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']
    company_admin_headers = seeded_context['company_admin_headers']
    member_headers = seeded_context['member_headers']
    company_admin_email = seeded_context['company_admin_user']['email']

    created = client.post('/companies', headers=admin_headers, json={
        'name': 'Beta', 'admin_email': company_admin_email,
    })
    company_id = created.get_json()['company']['id']
    assert client.patch(f'/companies/{company_id}/deactivate',
                        headers=company_admin_headers).status_code == 200

    # A plain member cannot reactivate it.
    assert_error(client.patch(f'/companies/{company_id}/reactivate',
                              headers=member_headers), 403, ERROR_CODES['FORBIDDEN'])

    # The company's own admin can.
    res = client.patch(f'/companies/{company_id}/reactivate', headers=company_admin_headers)
    assert res.status_code == 200
    body = res.get_json()
    assert body['msg'] == 'company reactivated'
    assert body['company']['is_active'] is True
