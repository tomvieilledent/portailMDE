"""API integration tests for agenda events and user-creation rules.

Covers:
- EventListResource (GET/POST /events)
- EventResource (PATCH/DELETE /events/<id>) — creator or super admin only
- UserListResource POST authorization (super admin / company admin)
- UserDeactivateResource guard (company admin must be reassigned first)
"""

from backend.api.errors import ERROR_CODES
from tests.helpers import assert_error, assert_ok


def _event_payload(**over):
    base = {'title': 'Réunion', 'date': '2027-06-15', 'time': '09:00',
            'color': 'bg-blue-500', 'description': 'Point hebdo'}
    base.update(over)
    return base


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

def test_event_list_starts_empty(seeded_context):
    client = seeded_context['client']
    resp = client.get('/events', headers=seeded_context['member_headers'])
    assert_ok(resp, 200)
    assert resp.get_json()['events'] == []


def test_event_visible_to_creator_invitees_and_managers_only(seeded_context):
    client = seeded_context['client']
    # A regular member creates an event...
    created = client.post('/events', headers=seeded_context['member_headers'],
                          json=_event_payload())
    assert_ok(created, 201)
    event = created.get_json()['event']
    assert event['title'] == 'Réunion'
    assert event['created_by'] == seeded_context['member_user']['id']

    def event_ids(headers):
        resp = client.get('/events', headers=headers)
        assert_ok(resp, 200)
        return [e['id'] for e in resp.get_json()['events']]

    # The creator sees their own event.
    assert event['id'] in event_ids(seeded_context['member_headers'])
    # The super admin (a manager) sees every event.
    assert event['id'] in event_ids(seeded_context['admin_headers'])
    # A non-invited regular user (company admin) does NOT see it.
    assert event['id'] not in event_ids(seeded_context['company_admin_headers'])

    # Once invited, that user sees it.
    invited = client.post('/invitations', headers=seeded_context['member_headers'],
                          json={'target_type': 'event', 'target_id': event['id'],
                                'invitee_ids': [seeded_context['company_admin_user']['id']]})
    assert_ok(invited, 201)
    assert event['id'] in event_ids(seeded_context['company_admin_headers'])


def test_non_creator_cannot_edit_or_delete(seeded_context):
    client = seeded_context['client']
    event = client.post('/events', headers=seeded_context['member_headers'],
                        json=_event_payload()).get_json()['event']
    # company_admin is neither the creator nor a super admin.
    patched = client.patch(f"/events/{event['id']}",
                           headers=seeded_context['company_admin_headers'],
                           json={'title': 'Hack'})
    assert_error(patched, 403, ERROR_CODES['FORBIDDEN'])
    deleted = client.delete(f"/events/{event['id']}",
                            headers=seeded_context['company_admin_headers'])
    assert_error(deleted, 403, ERROR_CODES['FORBIDDEN'])


def test_creator_can_edit_and_super_admin_can_delete(seeded_context):
    client = seeded_context['client']
    event = client.post('/events', headers=seeded_context['member_headers'],
                        json=_event_payload()).get_json()['event']
    # Creator edits.
    patched = client.patch(f"/events/{event['id']}",
                           headers=seeded_context['member_headers'],
                           json={'title': 'Réunion (maj)'})
    assert_ok(patched, 200)
    assert patched.get_json()['event']['title'] == 'Réunion (maj)'
    # Super admin deletes any event.
    deleted = client.delete(f"/events/{event['id']}",
                            headers=seeded_context['admin_headers'])
    assert_ok(deleted, 200)
    listed = client.get('/events', headers=seeded_context['member_headers'])
    assert event['id'] not in [e['id'] for e in listed.get_json()['events']]


def test_event_requires_title_and_date(seeded_context):
    client = seeded_context['client']
    resp = client.post('/events', headers=seeded_context['member_headers'],
                       json={'date': '2027-06-15'})
    assert_error(resp, 400, ERROR_CODES['VALIDATION_ERROR'])


# ---------------------------------------------------------------------------
# User creation authorization
# ---------------------------------------------------------------------------

def _make_company(seeded_context, admin_email):
    client = seeded_context['client']
    resp = client.post('/companies', headers=seeded_context['admin_headers'],
                       json={'name': 'Acme', 'admin_email': admin_email})
    assert_ok(resp, 201)
    return resp.get_json()['company']


def test_member_cannot_create_users(seeded_context):
    client = seeded_context['client']
    resp = client.post('/users', headers=seeded_context['member_headers'],
                       json={'email': 'x@example.com', 'password': 'password123'})
    assert_error(resp, 403, ERROR_CODES['FORBIDDEN'])


def test_super_admin_creates_company_admin(seeded_context):
    client = seeded_context['client']
    company = _make_company(seeded_context, 'company.admin@example.com')
    resp = client.post('/users', headers=seeded_context['admin_headers'], json={
        'email': 'boss@acme.com', 'password': 'password123',
        'company_id': company['id'], 'is_company_admin': True,
    })
    assert_ok(resp, 201)
    new_admin = resp.get_json()['user']
    assert new_admin['company_id'] == company['id']
    # The company now points to the freshly created admin.
    refreshed = client.get(f"/companies/{company['id']}",
                           headers=seeded_context['admin_headers']).get_json()['company']
    assert refreshed['admin_id'] == new_admin['id']


def test_company_admin_creates_user_in_own_company_only(seeded_context):
    client = seeded_context['client']
    # company.admin@example.com administers Acme.
    company = _make_company(seeded_context, 'company.admin@example.com')
    # Company admin creates a salarié; company_id is forced to their own.
    resp = client.post('/users', headers=seeded_context['company_admin_headers'], json={
        'email': 'employee@acme.com', 'password': 'password123',
        'company_id': 'some-other-id',
    })
    assert_ok(resp, 201)
    assert resp.get_json()['user']['company_id'] == company['id']


def test_cannot_deactivate_company_admin_before_reassign(seeded_context):
    client = seeded_context['client']
    company = _make_company(seeded_context, 'company.admin@example.com')
    admin_id = company['admin_id']
    assert admin_id
    resp = client.patch(f"/users/{admin_id}/deactivate",
                        headers=seeded_context['admin_headers'])
    assert_error(resp, 409, ERROR_CODES['CONFLICT'])
