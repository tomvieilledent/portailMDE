"""API integration tests for training sessions and formation user endpoints.

Covers:
- TrainingSessionsByTrainingResource (GET/POST /trainings/<id>/sessions)
- TrainingSessionResource (GET/PATCH/DELETE /training-sessions/<id>)
- TrainingSessionEnrollResource (POST/DELETE /training-sessions/<id>/enroll)
- TrainingSessionListResource (GET /training-sessions)
- TrainingInterestResource (POST/DELETE /trainings/<id>/interest)
- TrainingInterestedResource (GET /trainings/<id>/interested)
- TrainingCompletionsResource (GET /trainings/completions)
- CurrentUserTrainingsResource (GET /me/trainings)
- FormationUserResource PATCH (revoke completion)
"""

import pytest

from backend.api.errors import ERROR_CODES
from tests.helpers import assert_error, assert_ok


def admin_headers(seeded_context):
    return seeded_context['admin_headers']


def member_headers(seeded_context):
    return {'Authorization': f"Bearer {seeded_context['member_login']['access_token']}"}


def invite_to_session(seeded_context, session_id, invitee_ids):
    """Invite users to a session (as admin).

    Programmed sessions are now invitation-gated: a non-manager must hold an
    invitation before they can see or enroll in a session.
    """
    return seeded_context['client'].post(
        '/invitations',
        headers=admin_headers(seeded_context),
        json={'target_type': 'session', 'target_id': session_id,
              'invitee_ids': invitee_ids},
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def training(seeded_context):
    """Create a test training as admin."""
    client = seeded_context['client']
    resp = client.post('/trainings', headers=admin_headers(seeded_context), json={
        'title': 'Test Training',
    })
    assert_ok(resp, 201)
    return resp.get_json()['training']


@pytest.fixture()
def session(seeded_context, training):
    """Create a test session for the training."""
    client = seeded_context['client']
    resp = client.post(
        f"/trainings/{training['id']}/sessions",
        headers=admin_headers(seeded_context),
        json={
            'start_date': '2027-06-01T09:00:00',
            'end_date': '2027-06-03T17:00:00',
            'max_participants': 10,
            'location': 'Paris',
        },
    )
    assert_ok(resp, 201)
    sess = resp.get_json()['session']
    # Invite the seeded member so they can enroll (sessions are invite-gated).
    invite_to_session(seeded_context, sess['id'], [seeded_context['member_user']['id']])
    return sess


# ---------------------------------------------------------------------------
# Training session creation
# ---------------------------------------------------------------------------

class TestTrainingSessionCreation:
    def test_admin_can_create_session(self, seeded_context, training):
        client = seeded_context['client']
        resp = client.post(
            f"/trainings/{training['id']}/sessions",
            headers=admin_headers(seeded_context),
            json={
                'start_date': '2027-01-10T09:00:00',
                'end_date': '2027-01-12T17:00:00',
                'max_participants': 20,
            },
        )
        assert_ok(resp, 201)
        sess = resp.get_json()['session']
        assert sess['training_id'] == training['id']
        assert sess['max_participants'] == 20
        assert sess['status'] == 'upcoming'

    def test_member_cannot_create_session(self, seeded_context, training):
        client = seeded_context['client']
        resp = client.post(
            f"/trainings/{training['id']}/sessions",
            headers=member_headers(seeded_context),
            json={
                'start_date': '2027-01-10T09:00:00',
                'end_date': '2027-01-12T17:00:00',
                'max_participants': 5,
            },
        )
        assert_error(resp, 403, ERROR_CODES['FORBIDDEN'])

    def test_missing_start_date_returns_400(self, seeded_context, training):
        client = seeded_context['client']
        resp = client.post(
            f"/trainings/{training['id']}/sessions",
            headers=admin_headers(seeded_context),
            json={'end_date': '2027-01-12T17:00:00', 'max_participants': 5},
        )
        assert_error(resp, 400, ERROR_CODES['BAD_REQUEST'])

    def test_missing_max_participants_returns_400(self, seeded_context, training):
        client = seeded_context['client']
        resp = client.post(
            f"/trainings/{training['id']}/sessions",
            headers=admin_headers(seeded_context),
            json={
                'start_date': '2027-01-10T09:00:00',
                'end_date': '2027-01-12T17:00:00',
            },
        )
        assert_error(resp, 400, ERROR_CODES['BAD_REQUEST'])

    def test_invalid_max_participants_returns_400(self, seeded_context, training):
        client = seeded_context['client']
        # negative value passes the falsy check but fails domain validation
        resp = client.post(
            f"/trainings/{training['id']}/sessions",
            headers=admin_headers(seeded_context),
            json={
                'start_date': '2027-01-10T09:00:00',
                'end_date': '2027-01-12T17:00:00',
                'max_participants': -1,
            },
        )
        assert_error(resp, 400, ERROR_CODES['VALIDATION_ERROR'])

    def test_unknown_training_returns_404(self, seeded_context):
        client = seeded_context['client']
        resp = client.post(
            '/trainings/nonexistent/sessions',
            headers=admin_headers(seeded_context),
            json={
                'start_date': '2027-01-10T09:00:00',
                'end_date': '2027-01-12T17:00:00',
                'max_participants': 5,
            },
        )
        assert_error(resp, 404, ERROR_CODES['NOT_FOUND'])


# ---------------------------------------------------------------------------
# Session listing
# ---------------------------------------------------------------------------

class TestTrainingSessionListing:
    def test_list_sessions_for_training(self, seeded_context, training, session):
        client = seeded_context['client']
        resp = client.get(
            f"/trainings/{training['id']}/sessions",
            headers=admin_headers(seeded_context),
        )
        assert_ok(resp)
        sessions = resp.get_json()['sessions']
        assert any(s['id'] == session['id'] for s in sessions)

    def test_list_all_sessions(self, seeded_context, session):
        client = seeded_context['client']
        resp = client.get('/training-sessions', headers=admin_headers(seeded_context))
        assert_ok(resp)
        assert len(resp.get_json()['sessions']) >= 1

    def test_get_single_session(self, seeded_context, session):
        client = seeded_context['client']
        resp = client.get(
            f"/training-sessions/{session['id']}",
            headers=admin_headers(seeded_context),
        )
        assert_ok(resp)
        assert resp.get_json()['session']['id'] == session['id']


# ---------------------------------------------------------------------------
# Session visibility / access — programmed sessions are invitation-gated
# ---------------------------------------------------------------------------

class TestSessionVisibility:
    def _uninvited_session(self, seeded_context, training):
        """A session the seeded member is NOT invited to."""
        return seeded_context['client'].post(
            f"/trainings/{training['id']}/sessions",
            headers=admin_headers(seeded_context),
            json={'start_date': '2028-01-01T09:00:00',
                  'end_date': '2028-01-02T17:00:00', 'max_participants': 10},
        ).get_json()['session']

    def test_uninvited_member_does_not_see_session(self, seeded_context, training):
        client = seeded_context['client']
        sess = self._uninvited_session(seeded_context, training)
        for url in (f"/trainings/{training['id']}/sessions", '/training-sessions'):
            ids = [s['id'] for s in
                   client.get(url, headers=member_headers(seeded_context)).get_json()['sessions']]
            assert sess['id'] not in ids
        # ...but a manager (super admin) does.
        ids = [s['id'] for s in
               client.get('/training-sessions', headers=admin_headers(seeded_context)).get_json()['sessions']]
        assert sess['id'] in ids

    def test_uninvited_member_cannot_get_session(self, seeded_context, training):
        client = seeded_context['client']
        sess = self._uninvited_session(seeded_context, training)
        resp = client.get(f"/training-sessions/{sess['id']}",
                          headers=member_headers(seeded_context))
        assert_error(resp, 403, ERROR_CODES['FORBIDDEN'])

    def test_uninvited_member_cannot_enroll(self, seeded_context, training):
        client = seeded_context['client']
        sess = self._uninvited_session(seeded_context, training)
        resp = client.post(f"/training-sessions/{sess['id']}/enroll",
                           headers=member_headers(seeded_context))
        assert_error(resp, 403, ERROR_CODES['FORBIDDEN'])

    def test_invited_member_sees_and_enrolls(self, seeded_context, training):
        client = seeded_context['client']
        sess = self._uninvited_session(seeded_context, training)
        invite_to_session(seeded_context, sess['id'],
                          [seeded_context['member_user']['id']])
        # Now visible...
        ids = [s['id'] for s in
               client.get('/training-sessions', headers=member_headers(seeded_context)).get_json()['sessions']]
        assert sess['id'] in ids
        # ...and enrollable.
        resp = client.post(f"/training-sessions/{sess['id']}/enroll",
                           headers=member_headers(seeded_context))
        assert_ok(resp, 201)

    def test_get_missing_session_returns_404(self, seeded_context):
        client = seeded_context['client']
        resp = client.get(
            '/training-sessions/nonexistent',
            headers=admin_headers(seeded_context),
        )
        assert_error(resp, 404, ERROR_CODES['NOT_FOUND'])


# ---------------------------------------------------------------------------
# Session update / completion
# ---------------------------------------------------------------------------

class TestTrainingSessionUpdate:
    def test_admin_can_update_location(self, seeded_context, session):
        client = seeded_context['client']
        resp = client.patch(
            f"/training-sessions/{session['id']}",
            headers=admin_headers(seeded_context),
            json={'location': 'Lyon'},
        )
        assert_ok(resp)
        assert resp.get_json()['session']['location'] == 'Lyon'

    def test_member_cannot_update_session(self, seeded_context, session):
        client = seeded_context['client']
        resp = client.patch(
            f"/training-sessions/{session['id']}",
            headers=member_headers(seeded_context),
            json={'location': 'Nope'},
        )
        assert_error(resp, 403, ERROR_CODES['FORBIDDEN'])

    def test_complete_session_auto_validates_enrolled_users(self, seeded_context, training, session):
        client = seeded_context['client']
        # member enrolls
        client.post(
            f"/training-sessions/{session['id']}/enroll",
            headers=member_headers(seeded_context),
        )
        # admin completes the session
        resp = client.patch(
            f"/training-sessions/{session['id']}",
            headers=admin_headers(seeded_context),
            json={'status': 'completed'},
        )
        assert_ok(resp)
        assert resp.get_json()['session']['status'] == 'completed'
        # completions endpoint should show the member
        completions = client.get(
            '/trainings/completions',
            headers=admin_headers(seeded_context),
        )
        assert any(
            c['user_id'] == seeded_context['member_user']['id']
            for c in completions.get_json()['completions']
        )

    def test_admin_can_cancel_session(self, seeded_context, session):
        client = seeded_context['client']
        resp = client.delete(
            f"/training-sessions/{session['id']}",
            headers=admin_headers(seeded_context),
        )
        assert_ok(resp)
        assert resp.get_json()['msg'] == 'session cancelled'
        # verify status persisted
        get_resp = client.get(
            f"/training-sessions/{session['id']}",
            headers=admin_headers(seeded_context),
        )
        assert get_resp.get_json()['session']['status'] == 'cancelled'


# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------

class TestEnrollment:
    def test_member_can_enroll(self, seeded_context, training, session):
        client = seeded_context['client']
        resp = client.post(
            f"/training-sessions/{session['id']}/enroll",
            headers=member_headers(seeded_context),
        )
        assert_ok(resp, 201)
        enrollment = resp.get_json()['enrollment']
        assert enrollment['type'] == 'enrolled'
        assert enrollment['session_id'] == session['id']

    def test_enroll_upgrades_existing_interest(self, seeded_context, training, session):
        client = seeded_context['client']
        # express interest first
        client.post(
            f"/trainings/{training['id']}/interest",
            headers=member_headers(seeded_context),
        )
        # enroll
        resp = client.post(
            f"/training-sessions/{session['id']}/enroll",
            headers=member_headers(seeded_context),
        )
        assert_ok(resp, 201)
        assert resp.get_json()['enrollment']['type'] == 'enrolled'

    def test_double_enroll_returns_409(self, seeded_context, training, session):
        client = seeded_context['client']
        client.post(
            f"/training-sessions/{session['id']}/enroll",
            headers=member_headers(seeded_context),
        )
        resp = client.post(
            f"/training-sessions/{session['id']}/enroll",
            headers=member_headers(seeded_context),
        )
        assert_error(resp, 409, ERROR_CODES['CONFLICT'])

    def test_enroll_full_session_returns_409(self, seeded_context, training):
        client = seeded_context['client']
        # create a session with capacity 1
        tiny_session = client.post(
            f"/trainings/{training['id']}/sessions",
            headers=admin_headers(seeded_context),
            json={
                'start_date': '2027-03-01T09:00:00',
                'end_date': '2027-03-01T17:00:00',
                'max_participants': 1,
            },
        ).get_json()['session']
        # member fills the seat (must be invited first)
        invite_to_session(seeded_context, tiny_session['id'],
                          [seeded_context['member_user']['id']])
        client.post(
            f"/training-sessions/{tiny_session['id']}/enroll",
            headers=member_headers(seeded_context),
        )
        # second user (also invited) tries to enroll → blocked because full
        from backend.persistence.services import UserService
        user_svc = UserService()
        extra_user = user_svc.register('extra@x.com', 'password123')
        invite_to_session(seeded_context, tiny_session['id'], [extra_user['id']])
        extra_login = client.post(
            '/auth/login', json={'email': 'extra@x.com', 'password': 'password123'})
        extra_token = extra_login.get_json()['access_token']
        resp = client.post(
            f"/training-sessions/{tiny_session['id']}/enroll",
            headers={'Authorization': f'Bearer {extra_token}'},
        )
        assert_error(resp, 409, ERROR_CODES['CONFLICT'])

    def test_unenroll(self, seeded_context, training, session):
        client = seeded_context['client']
        client.post(
            f"/training-sessions/{session['id']}/enroll",
            headers=member_headers(seeded_context),
        )
        resp = client.delete(
            f"/training-sessions/{session['id']}/enroll",
            headers=member_headers(seeded_context),
        )
        assert_ok(resp)
        assert resp.get_json()['msg'] == 'unenrolled'

    def test_unenroll_resets_full_session(self, seeded_context, training):
        client = seeded_context['client']
        sess_resp = client.post(
            f"/trainings/{training['id']}/sessions",
            headers=admin_headers(seeded_context),
            json={
                'start_date': '2027-04-01T09:00:00',
                'end_date': '2027-04-01T17:00:00',
                'max_participants': 1,
            },
        )
        sess_id = sess_resp.get_json()['session']['id']
        invite_to_session(seeded_context, sess_id,
                          [seeded_context['member_user']['id']])
        client.post(
            f"/training-sessions/{sess_id}/enroll",
            headers=member_headers(seeded_context),
        )
        # verify full
        assert client.get(
            f'/training-sessions/{sess_id}',
            headers=admin_headers(seeded_context),
        ).get_json()['session']['status'] == 'full'
        # unenroll
        client.delete(
            f'/training-sessions/{sess_id}/enroll',
            headers=member_headers(seeded_context),
        )
        # verify back to upcoming
        assert client.get(
            f'/training-sessions/{sess_id}',
            headers=admin_headers(seeded_context),
        ).get_json()['session']['status'] == 'upcoming'


# ---------------------------------------------------------------------------
# Interest
# ---------------------------------------------------------------------------

class TestInterest:
    def test_express_interest(self, seeded_context, training):
        client = seeded_context['client']
        resp = client.post(
            f"/trainings/{training['id']}/interest",
            headers=member_headers(seeded_context),
        )
        assert_ok(resp, 201)
        assert resp.get_json()['interest']['type'] == 'interested'

    def test_express_interest_idempotent(self, seeded_context, training):
        client = seeded_context['client']
        r1 = client.post(
            f"/trainings/{training['id']}/interest",
            headers=member_headers(seeded_context),
        ).get_json()['interest']
        r2 = client.post(
            f"/trainings/{training['id']}/interest",
            headers=member_headers(seeded_context),
        ).get_json()['interest']
        assert r1['id'] == r2['id']

    def test_remove_interest(self, seeded_context, training):
        client = seeded_context['client']
        client.post(
            f"/trainings/{training['id']}/interest",
            headers=member_headers(seeded_context),
        )
        resp = client.delete(
            f"/trainings/{training['id']}/interest",
            headers=member_headers(seeded_context),
        )
        assert_ok(resp)
        assert resp.get_json()['msg'] == 'interest removed'

    def test_remove_missing_interest_returns_404(self, seeded_context, training):
        client = seeded_context['client']
        resp = client.delete(
            f"/trainings/{training['id']}/interest",
            headers=member_headers(seeded_context),
        )
        assert_error(resp, 404, ERROR_CODES['NOT_FOUND'])

    def test_admin_can_view_interested_users(self, seeded_context, training):
        client = seeded_context['client']
        client.post(
            f"/trainings/{training['id']}/interest",
            headers=member_headers(seeded_context),
        )
        resp = client.get(
            f"/trainings/{training['id']}/interested",
            headers=admin_headers(seeded_context),
        )
        assert_ok(resp)
        assert any(
            i['user_id'] == seeded_context['member_user']['id']
            for i in resp.get_json()['interested']
        )

    def test_member_cannot_view_interested_users(self, seeded_context, training):
        client = seeded_context['client']
        resp = client.get(
            f"/trainings/{training['id']}/interested",
            headers=member_headers(seeded_context),
        )
        assert_error(resp, 403, ERROR_CODES['FORBIDDEN'])

    def test_interest_nonexistent_training_returns_404(self, seeded_context):
        client = seeded_context['client']
        resp = client.post(
            '/trainings/nonexistent/interest',
            headers=member_headers(seeded_context),
        )
        assert_error(resp, 404, ERROR_CODES['NOT_FOUND'])


# ---------------------------------------------------------------------------
# Saved (bookmark)
# ---------------------------------------------------------------------------

class TestSaved:
    def test_save_training(self, seeded_context, training):
        client = seeded_context['client']
        resp = client.post(
            f"/trainings/{training['id']}/save",
            headers=member_headers(seeded_context),
        )
        assert_ok(resp, 201)
        assert resp.get_json()['saved']['saved'] is True

    def test_save_training_idempotent(self, seeded_context, training):
        client = seeded_context['client']
        r1 = client.post(
            f"/trainings/{training['id']}/save",
            headers=member_headers(seeded_context),
        ).get_json()['saved']
        r2 = client.post(
            f"/trainings/{training['id']}/save",
            headers=member_headers(seeded_context),
        ).get_json()['saved']
        assert r1['id'] == r2['id']

    def test_list_saved_trainings(self, seeded_context, training):
        client = seeded_context['client']
        client.post(
            f"/trainings/{training['id']}/save",
            headers=member_headers(seeded_context),
        )
        resp = client.get(
            '/me/saved-trainings',
            headers=member_headers(seeded_context),
        )
        assert_ok(resp)
        assert any(
            s['training_id'] == training['id']
            for s in resp.get_json()['saved']
        )

    def test_unsave_training(self, seeded_context, training):
        client = seeded_context['client']
        client.post(
            f"/trainings/{training['id']}/save",
            headers=member_headers(seeded_context),
        )
        resp = client.delete(
            f"/trainings/{training['id']}/save",
            headers=member_headers(seeded_context),
        )
        assert_ok(resp)
        assert resp.get_json()['msg'] == 'training unsaved'

    def test_unsave_missing_returns_404(self, seeded_context, training):
        client = seeded_context['client']
        resp = client.delete(
            f"/trainings/{training['id']}/save",
            headers=member_headers(seeded_context),
        )
        assert_error(resp, 404, ERROR_CODES['NOT_FOUND'])

    def test_save_and_interest_coexist(self, seeded_context, training):
        client = seeded_context['client']
        client.post(
            f"/trainings/{training['id']}/save",
            headers=member_headers(seeded_context),
        )
        client.post(
            f"/trainings/{training['id']}/interest",
            headers=member_headers(seeded_context),
        )
        # removing interest keeps the bookmark
        client.delete(
            f"/trainings/{training['id']}/interest",
            headers=member_headers(seeded_context),
        )
        resp = client.get(
            '/me/saved-trainings',
            headers=member_headers(seeded_context),
        )
        saved = resp.get_json()['saved']
        assert any(s['training_id'] == training['id'] for s in saved)

    def test_save_nonexistent_training_returns_404(self, seeded_context):
        client = seeded_context['client']
        resp = client.post(
            '/trainings/nonexistent/save',
            headers=member_headers(seeded_context),
        )
        assert_error(resp, 404, ERROR_CODES['NOT_FOUND'])


# ---------------------------------------------------------------------------
# Completions
# ---------------------------------------------------------------------------

class TestCompletions:
    def test_user_sees_own_completions(self, seeded_context, training, session):
        client = seeded_context['client']
        client.post(
            f"/training-sessions/{session['id']}/enroll",
            headers=member_headers(seeded_context),
        )
        client.patch(
            f"/training-sessions/{session['id']}",
            headers=admin_headers(seeded_context),
            json={'status': 'completed'},
        )
        resp = client.get('/trainings/completions', headers=member_headers(seeded_context))
        assert_ok(resp)
        completions = resp.get_json()['completions']
        assert all(
            c['user_id'] == seeded_context['member_user']['id']
            for c in completions
        )

    def test_admin_sees_all_completions(self, seeded_context, training, session):
        client = seeded_context['client']
        client.post(
            f"/training-sessions/{session['id']}/enroll",
            headers=member_headers(seeded_context),
        )
        client.patch(
            f"/training-sessions/{session['id']}",
            headers=admin_headers(seeded_context),
            json={'status': 'completed'},
        )
        resp = client.get('/trainings/completions', headers=admin_headers(seeded_context))
        assert_ok(resp)
        assert len(resp.get_json()['completions']) >= 1


# ---------------------------------------------------------------------------
# Revoke completion
# ---------------------------------------------------------------------------

class TestRevokeCompletion:
    def test_admin_can_revoke_completion(self, seeded_context, training, session):
        client = seeded_context['client']
        client.post(
            f"/training-sessions/{session['id']}/enroll",
            headers=member_headers(seeded_context),
        )
        client.patch(
            f"/training-sessions/{session['id']}",
            headers=admin_headers(seeded_context),
            json={'status': 'completed'},
        )
        completions = client.get(
            '/trainings/completions',
            headers=admin_headers(seeded_context),
        ).get_json()['completions']
        relation_id = completions[0]['id']
        resp = client.patch(
            f'/formation-users/{relation_id}',
            headers=admin_headers(seeded_context),
        )
        assert_ok(resp)
        assert resp.get_json()['formation_user']['type'] == 'enrolled'

    def test_member_cannot_revoke_completion(self, seeded_context, training, session):
        client = seeded_context['client']
        client.post(
            f"/training-sessions/{session['id']}/enroll",
            headers=member_headers(seeded_context),
        )
        client.patch(
            f"/training-sessions/{session['id']}",
            headers=admin_headers(seeded_context),
            json={'status': 'completed'},
        )
        completions = client.get(
            '/trainings/completions',
            headers=admin_headers(seeded_context),
        ).get_json()['completions']
        relation_id = completions[0]['id']
        resp = client.patch(
            f'/formation-users/{relation_id}',
            headers=member_headers(seeded_context),
        )
        assert_error(resp, 403, ERROR_CODES['FORBIDDEN'])

    def test_revoke_nonexistent_returns_404(self, seeded_context):
        client = seeded_context['client']
        resp = client.patch(
            '/formation-users/nonexistent',
            headers=admin_headers(seeded_context),
        )
        assert_error(resp, 404, ERROR_CODES['NOT_FOUND'])


# ---------------------------------------------------------------------------
# /me/trainings filtering
# ---------------------------------------------------------------------------

class TestMeTrainings:
    def test_filter_by_type_interested(self, seeded_context, training):
        client = seeded_context['client']
        client.post(
            f"/trainings/{training['id']}/interest",
            headers=member_headers(seeded_context),
        )
        resp = client.get(
            '/me/trainings?type=interested',
            headers=member_headers(seeded_context),
        )
        assert_ok(resp)
        enrollments = resp.get_json()['enrollments']
        assert all(e['type'] == 'interested' for e in enrollments)

    def test_filter_by_type_enrolled(self, seeded_context, training, session):
        client = seeded_context['client']
        client.post(
            f"/training-sessions/{session['id']}/enroll",
            headers=member_headers(seeded_context),
        )
        resp = client.get(
            '/me/trainings?type=enrolled',
            headers=member_headers(seeded_context),
        )
        assert_ok(resp)
        enrollments = resp.get_json()['enrollments']
        assert all(e['type'] == 'enrolled' for e in enrollments)

    def test_no_filter_returns_all(self, seeded_context, training, session):
        client = seeded_context['client']
        # create a second training for interest
        training2 = client.post(
            '/trainings',
            headers=admin_headers(seeded_context),
            json={'title': 'Training 2'},
        ).get_json()['training']
        client.post(
            f"/trainings/{training2['id']}/interest",
            headers=member_headers(seeded_context),
        )
        client.post(
            f"/training-sessions/{session['id']}/enroll",
            headers=member_headers(seeded_context),
        )
        resp = client.get('/me/trainings', headers=member_headers(seeded_context))
        assert_ok(resp)
        assert len(resp.get_json()['enrollments']) >= 2


# ---------------------------------------------------------------------------
# Multi-session enrollment (per-session, not per-training) — regression
# ---------------------------------------------------------------------------

class TestMultiSessionEnrollment:
    def _make_session(self, ctx, training, start, invite=True):
        client = ctx['client']
        sess = client.post(
            f"/trainings/{training['id']}/sessions",
            headers=admin_headers(ctx),
            json={
                'start_date': f'{start}T09:00:00',
                'end_date': f'{start}T17:00:00',
                'max_participants': 10,
            },
        ).get_json()['session']
        if invite:
            invite_to_session(ctx, sess['id'], [ctx['member_user']['id']])
        return sess

    def test_enroll_in_two_sessions_of_same_training(self, seeded_context, training):
        """A user can be enrolled in several sessions of the same training."""
        client = seeded_context['client']
        s1 = self._make_session(seeded_context, training, '2030-01-01')
        s2 = self._make_session(seeded_context, training, '2030-02-01')

        r1 = client.post(f"/training-sessions/{s1['id']}/enroll",
                         headers=member_headers(seeded_context))
        assert_ok(r1, 201)
        r2 = client.post(f"/training-sessions/{s2['id']}/enroll",
                         headers=member_headers(seeded_context))
        assert_ok(r2, 201)
        assert r2.get_json()['enrollment']['session_id'] == s2['id']

        enrolled = client.get('/me/trainings?type=enrolled',
                              headers=member_headers(seeded_context)).get_json()['enrollments']
        sids = {e['session_id'] for e in enrolled}
        assert s1['id'] in sids and s2['id'] in sids

    def test_accept_second_session_invitation_enrolls(self, seeded_context, training):
        """Accepting an invitation to a 2nd session enrolls in that session
        even when already enrolled in another session of the same training."""
        client = seeded_context['client']
        member_id = seeded_context['member_user']['id']
        s1 = self._make_session(seeded_context, training, '2030-03-01')
        s2 = self._make_session(seeded_context, training, '2030-04-01', invite=False)

        # already enrolled in s1
        client.post(f"/training-sessions/{s1['id']}/enroll",
                    headers=member_headers(seeded_context))

        # admin invites member to s2, member accepts
        inv = client.post('/invitations', headers=admin_headers(seeded_context), json={
            'target_type': 'session', 'target_id': s2['id'], 'invitee_ids': [member_id],
        }).get_json()['invitations'][0]
        client.patch(f"/invitations/{inv['id']}", headers=member_headers(seeded_context),
                     json={'status': 'accepted'})

        enrolled = client.get('/me/trainings?type=enrolled',
                              headers=member_headers(seeded_context)).get_json()['enrollments']
        sids = {e['session_id'] for e in enrolled}
        assert s2['id'] in sids, f"second session {s2['id']} missing from {sids}"

    def test_unenroll_one_session_keeps_other(self, seeded_context, training):
        client = seeded_context['client']
        s1 = self._make_session(seeded_context, training, '2030-05-01')
        s2 = self._make_session(seeded_context, training, '2030-06-01')
        client.post(f"/training-sessions/{s1['id']}/enroll", headers=member_headers(seeded_context))
        client.post(f"/training-sessions/{s2['id']}/enroll", headers=member_headers(seeded_context))

        client.delete(f"/training-sessions/{s1['id']}/enroll", headers=member_headers(seeded_context))

        enrolled = client.get('/me/trainings?type=enrolled',
                              headers=member_headers(seeded_context)).get_json()['enrollments']
        sids = {e['session_id'] for e in enrolled}
        assert s1['id'] not in sids and s2['id'] in sids
