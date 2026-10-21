"""Tests for the contact form and the email-based password reset flow."""

from backend.api.errors import ERROR_CODES
from tests.helpers import assert_error


def test_contact_requires_all_fields(app_bundle):
    client = app_bundle['client']
    resp = client.post('/contact', json={'name': 'Jean'})
    assert_error(resp, 400, ERROR_CODES['VALIDATION_ERROR'])


def test_contact_rejects_invalid_email(app_bundle):
    client = app_bundle['client']
    resp = client.post('/contact', json={
        'name': 'Jean Dupont',
        'email': 'not-an-email',
        'subject': 'incubateur',
        'message': 'Bonjour',
    })
    assert_error(resp, 400, ERROR_CODES['VALIDATION_ERROR'])


def test_contact_accepts_valid_submission(app_bundle):
    client = app_bundle['client']
    resp = client.post('/contact', json={
        'name': 'Jean Dupont',
        'email': 'jean@example.com',
        'phone': '+33600000000',
        'subject': 'incubateur',
        'message': 'Je souhaite des informations.',
    })
    # No SMTP/CONTACT_RECIPIENT configured in tests -> accepted silently.
    assert resp.status_code == 200
    assert 'msg' in resp.get_json()


def test_forgot_password_returns_token_without_smtp(app_bundle):
    client = app_bundle['client']
    client.post('/auth/register', json={
        'email': 'reset.me@example.com', 'password': 'password123'})

    resp = client.post('/auth/forgot-password', json={'email': 'reset.me@example.com'})
    assert resp.status_code == 200
    assert resp.get_json().get('reset_token')


def test_forgot_password_unknown_email_is_generic(app_bundle):
    client = app_bundle['client']
    resp = client.post('/auth/forgot-password', json={'email': 'nobody@example.com'})
    assert resp.status_code == 200
    assert 'reset_token' not in resp.get_json()


def test_reset_password_updates_credentials(app_bundle):
    client = app_bundle['client']
    client.post('/auth/register', json={
        'email': 'change.me@example.com', 'password': 'oldpassword'})

    forgot = client.post('/auth/forgot-password', json={'email': 'change.me@example.com'})
    token = forgot.get_json()['reset_token']

    reset = client.post('/auth/reset-password', json={
        'reset_token': token, 'password': 'brandnewpass'})
    assert reset.status_code == 200

    # old password no longer works, new one does
    old = client.post('/auth/login', json={
        'email': 'change.me@example.com', 'password': 'oldpassword'})
    assert old.status_code == 401
    new = client.post('/auth/login', json={
        'email': 'change.me@example.com', 'password': 'brandnewpass'})
    assert new.status_code == 200


def test_reset_password_rejects_bad_token(app_bundle):
    client = app_bundle['client']
    resp = client.post('/auth/reset-password', json={
        'reset_token': 'garbage', 'password': 'whateverpass'})
    assert_error(resp, 401, ERROR_CODES['INVALID_TOKEN'])
