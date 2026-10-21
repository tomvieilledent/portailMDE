"""Company 'kind' field — entreprise hébergée vs formateur."""

import pytest

from backend.models.company import Company as DomainCompany


def test_domain_defaults_to_company():
    c = DomainCompany(name='Acme')
    assert c.kind == 'company'


def test_domain_accepts_trainer():
    c = DomainCompany(name='FormaPro', kind='trainer')
    assert c.kind == 'trainer'


def test_domain_normalizes_and_rejects_unknown_kind():
    assert DomainCompany(name='X', kind='TRAINER').kind == 'trainer'
    with pytest.raises(ValueError):
        DomainCompany(name='X', kind='mentor')


def test_create_company_defaults_kind(seeded_context):
    ctx = seeded_context
    res = ctx['client'].post('/companies', headers=ctx['admin_headers'], json={
        'name': 'Hosted Co', 'admin_email': 'company.admin@example.com',
    })
    assert res.status_code == 201, res.get_json()
    assert res.get_json()['company']['kind'] == 'company'


def test_create_trainer(seeded_context):
    ctx = seeded_context
    res = ctx['client'].post('/companies', headers=ctx['admin_headers'], json={
        'name': 'FormaPro', 'kind': 'trainer',
        'admin_email': 'company.admin@example.com',
    })
    assert res.status_code == 201, res.get_json()
    company = res.get_json()['company']
    assert company['kind'] == 'trainer'

    # And it is listed back with its kind preserved.
    listed = ctx['client'].get('/companies', headers=ctx['admin_headers']).get_json()['companies']
    match = next(c for c in listed if c['id'] == company['id'])
    assert match['kind'] == 'trainer'


def test_invalid_kind_is_rejected(seeded_context):
    ctx = seeded_context
    res = ctx['client'].post('/companies', headers=ctx['admin_headers'], json={
        'name': 'Weird', 'kind': 'mentor',
        'admin_email': 'company.admin@example.com',
    })
    assert res.status_code == 400


def test_patch_kind_to_trainer(seeded_context):
    ctx = seeded_context
    created = ctx['client'].post('/companies', headers=ctx['admin_headers'], json={
        'name': 'Switcher', 'admin_email': 'company.admin@example.com',
    }).get_json()['company']
    assert created['kind'] == 'company'

    patched = ctx['client'].patch(
        f"/companies/{created['id']}", headers=ctx['admin_headers'],
        json={'kind': 'trainer'})
    assert patched.status_code == 200
    assert patched.get_json()['company']['kind'] == 'trainer'
