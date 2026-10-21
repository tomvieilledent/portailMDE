"""Shared test utility functions used across multiple test modules."""


def assert_error(response, status, code):
    """Assert that a response carries an expected HTTP status and error code."""
    payload = response.get_json()
    assert response.status_code == status
    assert payload['error']['code'] == code
    return payload


def assert_ok(response, expected_status=200):
    """Assert that a response has a successful HTTP status."""
    assert response.status_code == expected_status, response.get_json()


def make_text(length, char='a'):
    """Return a string of *length* repetitions of *char*."""
    return char * length
