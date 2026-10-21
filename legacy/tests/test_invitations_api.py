"""Invitation system (RSVP for events and trainings) — API tests."""

from backend.api.errors import ERROR_CODES
from tests.helpers import assert_error, assert_ok


def _create_event(ctx, title='Réunion'):
    res = ctx['client'].post(
        '/events',
        json={'title': title, 'date': '2026-07-01', 'time': '10:00'},
        headers=ctx['admin_headers'],
    )
    assert res.status_code in (200, 201), res.get_json()
    body = res.get_json()
    return body.get('event', body)


def test_create_invitations_for_selected_invitees(seeded_context):
    ctx = seeded_context
    event = _create_event(ctx)

    res = ctx['client'].post(
        '/invitations',
        json={
            'target_type': 'event',
            'target_id': event['id'],
            'target_title': event['title'],
            'invitee_ids': [
                ctx['company_admin_user']['id'],
                ctx['member_user']['id'],
            ],
        },
        headers=ctx['admin_headers'],
    )
    assert res.status_code == 201, res.get_json()
    created = res.get_json()['invitations']
    assert len(created) == 2
    assert all(inv['status'] == 'pending' for inv in created)


def test_invite_everyone_excludes_inviter(seeded_context):
    ctx = seeded_context
    event = _create_event(ctx)

    res = ctx['client'].post(
        '/invitations',
        json={'target_type': 'event', 'target_id': event['id'], 'all': True},
        headers=ctx['admin_headers'],
    )
    assert res.status_code == 201
    created = res.get_json()['invitations']
    invitee_ids = {inv['invitee_id'] for inv in created}
    # admin is the inviter and must not invite themselves
    assert ctx['admin_user']['id'] not in invitee_ids
    assert ctx['company_admin_user']['id'] in invitee_ids
    assert ctx['member_user']['id'] in invitee_ids


def test_reinviting_does_not_duplicate(seeded_context):
    ctx = seeded_context
    event = _create_event(ctx)
    payload = {
        'target_type': 'event', 'target_id': event['id'],
        'invitee_ids': [ctx['member_user']['id']],
    }
    ctx['client'].post('/invitations', json=payload, headers=ctx['admin_headers'])
    res = ctx['client'].post('/invitations', json=payload, headers=ctx['admin_headers'])
    assert res.status_code == 201
    # already invited → skipped, nothing newly created
    assert res.get_json()['invitations'] == []


def test_session_is_a_valid_target_type(seeded_context):
    ctx = seeded_context
    # Invitations now fire when programming a session, so 'session' targets are
    # accepted just like events.
    res = ctx['client'].post(
        '/invitations',
        json={'target_type': 'session', 'target_id': 'sess-123',
              'target_title': 'Marketing Digital',
              'invitee_ids': [ctx['member_user']['id']]},
        headers=ctx['admin_headers'],
    )
    assert res.status_code == 201, res.get_json()
    assert res.get_json()['invitations'][0]['target_type'] == 'session'


def test_bad_target_type_is_rejected(seeded_context):
    ctx = seeded_context
    res = ctx['client'].post(
        '/invitations',
        json={'target_type': 'meeting', 'target_id': 'x'},
        headers=ctx['admin_headers'],
    )
    assert res.status_code == 400


def test_me_invitations_lists_received_and_pending(seeded_context):
    ctx = seeded_context
    event = _create_event(ctx)
    ctx['client'].post(
        '/invitations',
        json={'target_type': 'event', 'target_id': event['id'],
              'invitee_ids': [ctx['member_user']['id']]},
        headers=ctx['admin_headers'],
    )

    res = ctx['client'].get('/me/invitations', headers=ctx['member_headers'])
    assert res.status_code == 200
    body = res.get_json()
    assert body['pending'] == 1
    assert len(body['invitations']) == 1
    assert body['invitations'][0]['target_id'] == event['id']


def test_invitee_can_accept(seeded_context):
    ctx = seeded_context
    event = _create_event(ctx)
    created = ctx['client'].post(
        '/invitations',
        json={'target_type': 'event', 'target_id': event['id'],
              'invitee_ids': [ctx['member_user']['id']]},
        headers=ctx['admin_headers'],
    ).get_json()['invitations']
    inv_id = created[0]['id']

    res = ctx['client'].patch(
        f'/invitations/{inv_id}',
        json={'status': 'accepted'},
        headers=ctx['member_headers'],
    )
    assert res.status_code == 200
    assert res.get_json()['invitation']['status'] == 'accepted'

    # no longer pending
    me = ctx['client'].get('/me/invitations', headers=ctx['member_headers']).get_json()
    assert me['pending'] == 0


def test_non_invitee_cannot_respond(seeded_context):
    ctx = seeded_context
    event = _create_event(ctx)
    created = ctx['client'].post(
        '/invitations',
        json={'target_type': 'event', 'target_id': event['id'],
              'invitee_ids': [ctx['member_user']['id']]},
        headers=ctx['admin_headers'],
    ).get_json()['invitations']
    inv_id = created[0]['id']

    # company_admin is not the invitee → treated as not found
    res = ctx['client'].patch(
        f'/invitations/{inv_id}',
        json={'status': 'accepted'},
        headers=ctx['company_admin_headers'],
    )
    assert res.status_code == 404


def test_invalid_status_rejected(seeded_context):
    ctx = seeded_context
    event = _create_event(ctx)
    created = ctx['client'].post(
        '/invitations',
        json={'target_type': 'event', 'target_id': event['id'],
              'invitee_ids': [ctx['member_user']['id']]},
        headers=ctx['admin_headers'],
    ).get_json()['invitations']
    inv_id = created[0]['id']
    res = ctx['client'].patch(
        f'/invitations/{inv_id}',
        json={'status': 'maybe'},
        headers=ctx['member_headers'],
    )
    assert res.status_code == 400


def test_organizer_sees_responses(seeded_context):
    ctx = seeded_context
    event = _create_event(ctx)
    created = ctx['client'].post(
        '/invitations',
        json={'target_type': 'event', 'target_id': event['id'],
              'invitee_ids': [ctx['member_user']['id'],
                              ctx['company_admin_user']['id']]},
        headers=ctx['admin_headers'],
    ).get_json()['invitations']
    member_inv = next(i for i in created if i['invitee_id'] == ctx['member_user']['id'])
    ctx['client'].patch(
        f"/invitations/{member_inv['id']}",
        json={'status': 'declined'},
        headers=ctx['member_headers'],
    )

    res = ctx['client'].get(
        f"/invitations?target_type=event&target_id={event['id']}",
        headers=ctx['admin_headers'],
    )
    assert res.status_code == 200
    invs = res.get_json()['invitations']
    statuses = {i['invitee_id']: i['status'] for i in invs}
    assert statuses[ctx['member_user']['id']] == 'declined'
    assert statuses[ctx['company_admin_user']['id']] == 'pending'


def test_non_organizer_cannot_view_target_responses(seeded_context):
    ctx = seeded_context
    event = _create_event(ctx)
    ctx['client'].post(
        '/invitations',
        json={'target_type': 'event', 'target_id': event['id'],
              'invitee_ids': [ctx['member_user']['id']]},
        headers=ctx['admin_headers'],
    )
    # member is an invitee, not the inviter, and not super admin → forbidden
    res = ctx['client'].get(
        f"/invitations?target_type=event&target_id={event['id']}",
        headers=ctx['member_headers'],
    )
    assert res.status_code == 403


def _training_and_session(ctx, max_participants=10):
    """Create a training + a session for it (as admin)."""
    t = ctx['client'].post(
        '/trainings', headers=ctx['admin_headers'], json={'title': 'Marketing'}
    ).get_json()['training']
    s = ctx['client'].post(
        f"/trainings/{t['id']}/sessions", headers=ctx['admin_headers'],
        json={'start_date': '2027-06-01T09:00:00', 'end_date': '2027-06-03T17:00:00',
              'max_participants': max_participants},
    ).get_json()['session']
    return t, s


def test_accepting_session_invitation_enrolls_invitee(seeded_context):
    """Accepting a session invitation enrolls the invitee and increments the
    enrolled counter; declining afterwards removes the enrollment."""
    ctx = seeded_context
    training, session = _training_and_session(ctx)

    inv = ctx['client'].post(
        '/invitations',
        json={'target_type': 'session', 'target_id': session['id'],
              'target_title': training['title'],
              'invitee_ids': [ctx['member_user']['id']]},
        headers=ctx['admin_headers'],
    ).get_json()['invitations'][0]

    # Accept → enrolled.
    res = ctx['client'].patch(
        f"/invitations/{inv['id']}", json={'status': 'accepted'},
        headers=ctx['member_headers'])
    assert_ok(res, 200)

    me = ctx['client'].get('/me/trainings?type=enrolled',
                           headers=ctx['member_headers']).get_json()['enrollments']
    assert any(e['session_id'] == session['id'] for e in me)

    # Counter incremented.
    s = ctx['client'].get(f"/training-sessions/{session['id']}",
                          headers=ctx['admin_headers']).get_json()['session']
    assert s['enrolled'] == 1

    # Decline → enrollment removed, counter back to 0.
    ctx['client'].patch(f"/invitations/{inv['id']}", json={'status': 'declined'},
                        headers=ctx['member_headers'])
    me = ctx['client'].get('/me/trainings?type=enrolled',
                           headers=ctx['member_headers']).get_json()['enrollments']
    assert not any(e['session_id'] == session['id'] for e in me)
    s = ctx['client'].get(f"/training-sessions/{session['id']}",
                          headers=ctx['admin_headers']).get_json()['session']
    assert s['enrolled'] == 0


def test_enrollments_list_requires_manage_trainings(seeded_context):
    """Only an admin/staff with manage_trainings may view who is enrolled."""
    ctx = seeded_context
    training, _ = _training_and_session(ctx)
    res = ctx['client'].get(f"/trainings/{training['id']}/enrollments",
                            headers=ctx['member_headers'])
    assert_error(res, 403, ERROR_CODES['FORBIDDEN'])
    res = ctx['client'].get(f"/trainings/{training['id']}/enrollments",
                            headers=ctx['admin_headers'])
    assert_ok(res, 200)
