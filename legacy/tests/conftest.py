import importlib
import sys

import pytest


def _clear_backend_modules():
    for module_name in list(sys.modules):
        if module_name == 'backend' or module_name.startswith('backend.'):
            del sys.modules[module_name]


@pytest.fixture()
def app_bundle(monkeypatch, tmp_path):
    db_path = tmp_path / 'test.db'
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{db_path}')
    monkeypatch.setenv('JWT_SECRET_KEY', 'test-secret-key-for-pytest-suite')
    # Force "SMTP not configured" in tests so the mail-based flows use their
    # dev fallback and never attempt a real network send. An empty (but set)
    # value survives load_dotenv(override=False) even when a real .env exists.
    monkeypatch.setenv('SMTP_HOST', '')

    _clear_backend_modules()

    db_module = importlib.import_module('backend.persistence.db')
    models_module = importlib.import_module('backend.persistence.models')
    # Ensure a clean test schema matching the current models
    models_module.Base.metadata.drop_all(bind=db_module.engine)
    models_module.Base.metadata.create_all(bind=db_module.engine)

    app_module = importlib.import_module('backend.api.app')
    app = app_module.create_app()
    app.config['TESTING'] = True

    yield {
        'app': app,
        'client': app.test_client(),
        'engine': db_module.engine,
    }

    db_module.engine.dispose()


@pytest.fixture()
def seeded_context(app_bundle):
    from backend.persistence.services import UserService

    client = app_bundle['client']
    user_service = UserService()

    admin_user = user_service.register(
        'admin@example.com',
        'password123',
        first_name='Admin',
        is_super_admin=True,
    )
    company_admin_user = user_service.register(
        'company.admin@example.com',
        'password123',
        first_name='Company',
        last_name='Admin',
    )
    member_user = user_service.register(
        'member@example.com',
        'password123',
        first_name='Member',
        last_name='User',
    )

    def login(email, password):
        response = client.post(
            '/auth/login', json={'email': email, 'password': password})
        assert response.status_code == 200
        return response.get_json()

    admin_login = login('admin@example.com', 'password123')
    company_admin_login = login('company.admin@example.com', 'password123')
    member_login = login('member@example.com', 'password123')

    return {
        'client': client,
        'admin_user': admin_user,
        'company_admin_user': company_admin_user,
        'member_user': member_user,
        'admin_login': admin_login,
        'company_admin_login': company_admin_login,
        'member_login': member_login,
        'admin_headers': {'Authorization': f"Bearer {admin_login['access_token']}"},
        'company_admin_headers': {'Authorization': f"Bearer {company_admin_login['access_token']}"},
        'member_headers': {'Authorization': f"Bearer {member_login['access_token']}"},
        'admin_refresh_headers': {'Authorization': f"Bearer {admin_login['refresh_token']}"},
        'company_admin_refresh_headers': {'Authorization': f"Bearer {company_admin_login['refresh_token']}"},
        'member_refresh_headers': {'Authorization': f"Bearer {member_login['refresh_token']}"},
    }
