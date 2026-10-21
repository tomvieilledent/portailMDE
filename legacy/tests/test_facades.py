"""Integration tests for SQL persistence facades.

Each test uses a fresh in-memory (tmp_path) SQLite database via the
``app_bundle`` fixture defined in conftest.py.
"""

import importlib
import sys
from datetime import datetime, timezone

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2027, 1, 10, 9, 0, tzinfo=timezone.utc)
_END = datetime(2027, 1, 12, 17, 0, tzinfo=timezone.utc)


@pytest.fixture()
def facades(app_bundle):
    """Return initialised facade instances wired to the test database."""
    from backend.persistence.services.facades.user_facade_sql import UserFacade
    from backend.persistence.services.facades.company_facade_sql import CompanyFacade
    from backend.persistence.services.facades.training_facade_sql import TrainingFacade
    from backend.persistence.services.facades.training_session_facade_sql import TrainingSessionFacade
    from backend.persistence.services.facades.formation_user_facade_sql import FormationUserFacade
    from backend.persistence.services.facades.message_facade_sql import MessageFacade
    from backend.persistence.services.facades.notification_facade_sql import NotificationFacade
    from backend.persistence.services.facades.news_facade_sql import NewsFacade

    return {
        'user': UserFacade(),
        'company': CompanyFacade(),
        'training': TrainingFacade(),
        'session': TrainingSessionFacade(),
        'formation': FormationUserFacade(),
        'message': MessageFacade(),
        'notification': NotificationFacade(),
        'news': NewsFacade(),
    }


# ---------------------------------------------------------------------------
# UserFacade
# ---------------------------------------------------------------------------

class TestUserFacade:
    def test_create_and_get_by_email(self, facades):
        f = facades['user']
        user = f.create_user('alice@example.com', 'password123', first_name='Alice')
        assert user['email'] == 'alice@example.com'
        assert user['first_name'] == 'Alice'
        found = f.get_by_email('alice@example.com')
        assert found['id'] == user['id']

    def test_get_by_id_returns_none_for_missing(self, facades):
        assert facades['user'].get_by_id('nonexistent') is None

    def test_check_password_correct(self, facades):
        f = facades['user']
        f.create_user('bob@example.com', 'securepass')
        assert f.check_password('bob@example.com', 'securepass') is True
        assert f.check_password('bob@example.com', 'wrongpass') is False

    def test_check_password_unknown_user(self, facades):
        assert facades['user'].check_password('no@one.com', 'x') is False

    def test_update_fields(self, facades):
        f = facades['user']
        user = f.create_user('carol@example.com', 'password123')
        updated = f.update(user['id'], first_name='Carol', last_name='Smith')
        assert updated['first_name'] == 'Carol'
        assert updated['last_name'] == 'Smith'

    def test_update_missing_user_returns_none(self, facades):
        assert facades['user'].update('missing') is None

    def test_deactivate_by_email(self, facades):
        f = facades['user']
        f.create_user('dave@example.com', 'password123')
        assert f.deactivate('dave@example.com') is True
        user = f.get_by_email('dave@example.com')
        assert user['is_active'] is False

    def test_deactivate_missing_returns_false(self, facades):
        assert facades['user'].deactivate('missing') is False

    def test_delete_user(self, facades):
        f = facades['user']
        user = f.create_user('eve@example.com', 'password123')
        assert f.delete(user['id']) is True
        assert f.get_by_id(user['id']) is None

    def test_delete_missing_returns_false(self, facades):
        assert facades['user'].delete('missing') is False

    def test_reset_password(self, facades):
        f = facades['user']
        user = f.create_user('frank@example.com', 'oldpassword')
        assert f.reset_password(user['id'], 'newpassword') is True
        assert f.check_password('frank@example.com', 'newpassword') is True

    def test_list_users_with_company_filter(self, facades):
        f = facades['user']
        u1 = f.create_user('u1@x.com', 'password123', company_id='c-1')
        u2 = f.create_user('u2@x.com', 'password123', company_id='c-2')
        result = f.list_users(company_id='c-1')
        ids = [u['id'] for u in result]
        assert u1['id'] in ids
        assert u2['id'] not in ids


# ---------------------------------------------------------------------------
# TrainingFacade
# ---------------------------------------------------------------------------

class TestTrainingFacade:
    def test_create_and_get(self, facades):
        f = facades['training']
        t = f.create('Python 101', description='Intro')
        assert t['title'] == 'Python 101'
        assert t['description'] == 'Intro'
        found = f.get(t['id'])
        assert found['id'] == t['id']

    def test_get_missing_returns_none(self, facades):
        assert facades['training'].get('missing') is None

    def test_list_returns_all(self, facades):
        f = facades['training']
        f.create('T1')
        f.create('T2')
        rows = f.list()
        assert len(rows) >= 2

    def test_update_title(self, facades):
        f = facades['training']
        t = f.create('Old Title')
        updated = f.update(t['id'], title='New Title')
        assert updated['title'] == 'New Title'

    def test_deactivate(self, facades):
        f = facades['training']
        t = f.create('To deactivate')
        result = f.deactivate(t['id'])
        assert result['is_active'] is False

    def test_delete(self, facades):
        f = facades['training']
        t = f.create('To delete')
        assert f.delete(t['id']) is True
        assert f.get(t['id']) is None


# ---------------------------------------------------------------------------
# TrainingSessionFacade
# ---------------------------------------------------------------------------

class TestTrainingSessionFacade:
    def test_create_and_get(self, facades):
        sf = facades['session']
        sess = sf.create('t-1', _NOW, _END, max_participants=15)
        assert sess['training_id'] == 't-1'
        assert sess['max_participants'] == 15
        assert sess['status'] == 'upcoming'
        found = sf.get(sess['id'])
        assert found['id'] == sess['id']

    def test_get_missing_returns_none(self, facades):
        assert facades['session'].get('missing') is None

    def test_list_filters_by_training(self, facades):
        sf = facades['session']
        sf.create('tr-A', _NOW, _END, 10)
        sf.create('tr-B', _NOW, _END, 10)
        rows = sf.list(training_id='tr-A')
        assert all(r['training_id'] == 'tr-A' for r in rows)

    def test_list_filters_by_status(self, facades):
        sf = facades['session']
        sf.create('tr-X', _NOW, _END, 5)
        sf.create('tr-X', _NOW, _END, 5)
        rows = sf.list(status='upcoming')
        assert all(r['status'] == 'upcoming' for r in rows)

    def test_update_status(self, facades):
        sf = facades['session']
        sess = sf.create('t-2', _NOW, _END, 10)
        updated = sf.update(sess['id'], status='cancelled')
        assert updated['status'] == 'cancelled'

    def test_count_enrolled(self, facades):
        tf = facades['training']
        uf = facades['user']
        sf = facades['session']
        ff = facades['formation']

        training = tf.create('Counting Training')
        user1 = uf.create_user('cnt1@x.com', 'password123')
        user2 = uf.create_user('cnt2@x.com', 'password123')
        sess = sf.create(training['id'], _NOW, _END, 10)

        assert sf.count_enrolled(sess['id']) == 0
        ff.enroll(user1['id'], training['id'], sess['id'])
        assert sf.count_enrolled(sess['id']) == 1
        ff.enroll(user2['id'], training['id'], sess['id'])
        assert sf.count_enrolled(sess['id']) == 2

    def test_complete_bulk_updates_enrollments(self, facades):
        tf = facades['training']
        uf = facades['user']
        sf = facades['session']
        ff = facades['formation']

        training = tf.create('Completable Training')
        user = uf.create_user('bulk@x.com', 'password123')
        sess = sf.create(training['id'], _NOW, _END, 10)
        ff.enroll(user['id'], training['id'], sess['id'])

        completed_sess = sf.complete(sess['id'])
        assert completed_sess['status'] == 'completed'

        completions = ff.list_completions(user_id=user['id'])
        assert len(completions) == 1
        assert completions[0]['type'] == 'completed'


# ---------------------------------------------------------------------------
# FormationUserFacade
# ---------------------------------------------------------------------------

class TestFormationUserFacade:
    def _setup(self, facades):
        tf = facades['training']
        uf = facades['user']
        sf = facades['session']
        training = tf.create('FU Training')
        user = uf.create_user('futest@x.com', 'password123')
        sess = sf.create(training['id'], _NOW, _END, 5)
        return training, user, sess

    def test_express_interest_creates_record(self, facades):
        training, user, _ = self._setup(facades)
        ff = facades['formation']
        result = ff.express_interest(user['id'], training['id'])
        assert result['type'] == 'interested'
        assert result['session_id'] is None

    def test_express_interest_is_idempotent(self, facades):
        training, user, _ = self._setup(facades)
        ff = facades['formation']
        r1 = ff.express_interest(user['id'], training['id'])
        r2 = ff.express_interest(user['id'], training['id'])
        assert r1['id'] == r2['id']

    def test_remove_interest(self, facades):
        training, user, _ = self._setup(facades)
        ff = facades['formation']
        ff.express_interest(user['id'], training['id'])
        assert ff.remove_interest(user['id'], training['id']) is True
        assert ff.get_by_user_training(user['id'], training['id']) is None

    def test_remove_interest_missing_returns_false(self, facades):
        assert facades['formation'].remove_interest('u', 't') is False

    def test_enroll_creates_record(self, facades):
        training, user, sess = self._setup(facades)
        ff = facades['formation']
        result, err = ff.enroll(user['id'], training['id'], sess['id'])
        assert err is None
        assert result['type'] == 'enrolled'
        assert result['session_id'] == sess['id']

    def test_enroll_upgrades_interest_to_enrolled(self, facades):
        training, user, sess = self._setup(facades)
        ff = facades['formation']
        interest = ff.express_interest(user['id'], training['id'])
        enrolled, err = ff.enroll(user['id'], training['id'], sess['id'])
        assert err is None
        assert enrolled['id'] == interest['id']
        assert enrolled['type'] == 'enrolled'

    def test_enroll_rejects_double_enrollment(self, facades):
        training, user, sess = self._setup(facades)
        ff = facades['formation']
        ff.enroll(user['id'], training['id'], sess['id'])
        result, err = ff.enroll(user['id'], training['id'], sess['id'])
        assert result is None
        assert 'already enrolled' in err

    def test_enroll_marks_session_full(self, facades):
        tf = facades['training']
        uf = facades['user']
        sf = facades['session']
        ff = facades['formation']
        training = tf.create('Tiny Training')
        sess = sf.create(training['id'], _NOW, _END, max_participants=1)
        user = uf.create_user('tiny1@x.com', 'password123')
        ff.enroll(user['id'], training['id'], sess['id'])
        updated_sess = sf.get(sess['id'])
        assert updated_sess['status'] == 'full'

    def test_enroll_rejects_full_session(self, facades):
        tf = facades['training']
        uf = facades['user']
        sf = facades['session']
        ff = facades['formation']
        training = tf.create('Full Training')
        sess = sf.create(training['id'], _NOW, _END, max_participants=1)
        user1 = uf.create_user('full1@x.com', 'password123')
        user2 = uf.create_user('full2@x.com', 'password123')
        ff.enroll(user1['id'], training['id'], sess['id'])
        result, err = ff.enroll(user2['id'], training['id'], sess['id'])
        assert result is None
        assert 'full' in err

    def test_unenroll_reverts_full_session_to_upcoming(self, facades):
        tf = facades['training']
        uf = facades['user']
        sf = facades['session']
        ff = facades['formation']
        training = tf.create('Revert Training')
        sess = sf.create(training['id'], _NOW, _END, max_participants=1)
        user = uf.create_user('revert@x.com', 'password123')
        ff.enroll(user['id'], training['id'], sess['id'])
        assert sf.get(sess['id'])['status'] == 'full'
        ff.unenroll(user['id'], sess['id'])
        assert sf.get(sess['id'])['status'] == 'upcoming'

    def test_unenroll_missing_returns_false(self, facades):
        assert facades['formation'].unenroll('u', 't') is False

    def test_revoke_completion(self, facades):
        training, user, sess = self._setup(facades)
        ff = facades['formation']
        sf = facades['session']
        ff.enroll(user['id'], training['id'], sess['id'])
        sf.complete(sess['id'])
        completions = ff.list_completions(user_id=user['id'])
        relation_id = completions[0]['id']
        revoked = ff.revoke_completion(relation_id)
        assert revoked['type'] == 'enrolled'
        assert revoked['completed_at'] is None

    def test_revoke_completion_missing_returns_none(self, facades):
        assert facades['formation'].revoke_completion('missing') is None

    def test_list_completions_all(self, facades):
        tf = facades['training']
        uf = facades['user']
        sf = facades['session']
        ff = facades['formation']
        training = tf.create('ListComp')
        user = uf.create_user('lc@x.com', 'password123')
        sess = sf.create(training['id'], _NOW, _END, 5)
        ff.enroll(user['id'], training['id'], sess['id'])
        sf.complete(sess['id'])
        all_completions = ff.list_completions()
        assert any(c['user_id'] == user['id'] for c in all_completions)

    def test_list_interested(self, facades):
        tf = facades['training']
        uf = facades['user']
        ff = facades['formation']
        training = tf.create('Interest Training')
        user = uf.create_user('int@x.com', 'password123')
        ff.express_interest(user['id'], training['id'])
        interested = ff.list_interested(training_id=training['id'])
        assert any(i['user_id'] == user['id'] for i in interested)


# ---------------------------------------------------------------------------
# MessageFacade
# ---------------------------------------------------------------------------

class TestMessageFacade:
    def test_create_and_list_by_conversation(self, facades):
        f = facades['message']
        f.create('author-1', 'Hello', conversation_id='conv-1')
        f.create('author-1', 'World', conversation_id='conv-1')
        msgs = f.list_by_conversation('conv-1')
        assert len(msgs) == 2
        assert msgs[0]['content'] == 'Hello'

    def test_list_by_author(self, facades):
        f = facades['message']
        f.create('auth-A', 'Msg 1')
        f.create('auth-B', 'Msg 2')
        result = f.list_by_author('auth-A')
        assert all(m['author_id'] == 'auth-A' for m in result)

    def test_delete_message(self, facades):
        f = facades['message']
        msg = f.create('auth-X', 'To delete')
        assert f.delete(msg['id']) is True
        assert f.get(msg['id']) is None

    def test_delete_missing_returns_false(self, facades):
        assert facades['message'].delete('missing') is False


# ---------------------------------------------------------------------------
# NotificationFacade
# ---------------------------------------------------------------------------

class TestNotificationFacade:
    def test_create_and_list_by_recipient(self, facades):
        f = facades['notification']
        f.create('user-1', 'You have a message')
        f.create('user-1', 'Second notification')
        f.create('user-2', 'Other user')
        result = f.list_by_recipient('user-1')
        assert len(result) == 2
        assert all(n['recipient_id'] == 'user-1' for n in result)

    def test_mark_read(self, facades):
        f = facades['notification']
        n = f.create('user-3', 'Read me')
        assert n['is_read'] is False
        assert f.mark_read(n['id']) is True
        updated = f.get(n['id'])
        assert updated['is_read'] is True

    def test_mark_read_missing_returns_false(self, facades):
        assert facades['notification'].mark_read('missing') is False

    def test_delete(self, facades):
        f = facades['notification']
        n = f.create('user-4', 'Delete me')
        assert f.delete(n['id']) is True
        assert f.get(n['id']) is None


# ---------------------------------------------------------------------------
# NewsFacade
# ---------------------------------------------------------------------------

class TestNewsFacade:
    def test_create_and_list(self, facades):
        f = facades['news']
        f.create('Breaking News', source='Reuters')
        f.create('Sports Update')
        rows = f.list()
        assert len(rows) >= 2

    def test_get_by_id(self, facades):
        f = facades['news']
        article = f.create('Specific Article')
        found = f.get(article['id'])
        assert found['title'] == 'Specific Article'

    def test_delete(self, facades):
        f = facades['news']
        article = f.create('To Delete')
        assert f.delete(article['id']) is True
        assert f.get(article['id']) is None

    def test_delete_missing_returns_false(self, facades):
        assert facades['news'].delete('missing') is False
