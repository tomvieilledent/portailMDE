import uuid
from datetime import datetime, timezone

import pytest

from backend.models.base import BaseModel
from backend.models.company import Company
from backend.models.conversation import Conversation
from backend.models.conversation_participant import ConversationParticipant
from backend.models.formation_user import FormationUser
from backend.models.message import Message
from backend.models.news import News
from backend.models.notification import Notification
from backend.models.training import Training
from backend.models.training_session import TrainingSession
from backend.models.user import User
from tests.helpers import make_text


def test_base_model_defaults_and_to_dict():
    model = BaseModel(uploaded_at='2026-01-01T00:00:00Z',
                      delete_by='deleter-id')

    payload = model.to_dict()

    assert isinstance(model.id, uuid.UUID)
    assert model.is_active is True
    assert model.uploaded_at == '2026-01-01T00:00:00Z'
    assert model.delete_by == 'deleter-id'
    assert payload['uploaded_at'] == '2026-01-01T00:00:00Z'


def test_user_model_normalizes_email_and_trims_names():
    user = User(
        email='  JOHN.DOE@Example.COM  ',
        password='password123',
        first_name='  John  ',
        last_name='  Doe  ',
        phone=' +33 6 00 00 00 00 ',
        is_super_admin=True,
        company_id='company-id',
    )

    assert user.email == 'john.doe@example.com'
    assert user.first_name == 'John'
    assert user.last_name == 'Doe'
    assert user.is_super_admin is True
    assert user.company_id == 'company-id'


def test_user_model_accepts_boundary_lengths():
    user = User(
        email=f"{make_text(242)}@x.com",
        password=make_text(256),
        first_name=make_text(100),
        last_name=make_text(100),
    )

    assert user.email == f"{make_text(242)}@x.com"
    assert user.password == make_text(256)
    assert user.first_name == make_text(100)
    assert user.last_name == make_text(100)


@pytest.mark.parametrize('email', ['', 'not-an-email', 'a' * 255 + '@example.com'])
def test_user_model_rejects_invalid_email(email):
    with pytest.raises(ValueError):
        User(email=email, password='password123')


@pytest.mark.parametrize('email', [123, None, []])
def test_user_model_rejects_non_string_email(email):
    with pytest.raises(TypeError):
        User(email=email, password='password123')


@pytest.mark.parametrize('password', ['short', 'a' * 257])
def test_user_model_rejects_invalid_password(password):
    with pytest.raises(ValueError):
        User(email='user@example.com', password=password)


@pytest.mark.parametrize('password', [123, None, []])
def test_user_model_rejects_non_string_password(password):
    with pytest.raises(TypeError):
        User(email='user@example.com', password=password)


def test_user_model_rejects_invalid_name_types():
    with pytest.raises(TypeError):
        User(email='user@example.com', password='password123', first_name=123)

    with pytest.raises(ValueError):
        User(email='user@example.com', password='password123', last_name='   ')


@pytest.mark.parametrize('field_name', ['first_name', 'last_name'])
def test_user_model_rejects_overlong_names(field_name):
    kwargs = {
        'email': 'user@example.com',
        'password': 'password123',
        field_name: make_text(101),
    }

    with pytest.raises(ValueError):
        User(**kwargs)


@pytest.mark.parametrize('field_name', ['first_name', 'last_name'])
def test_user_model_rejects_non_string_names(field_name):
    kwargs = {
        'email': 'user@example.com',
        'password': 'password123',
        field_name: 123,
    }

    with pytest.raises(TypeError):
        User(**kwargs)


def test_company_model_validates_email_and_admin_id():
    company = Company(
        name='  Example Company  ',
        admin_email='ADMIN@EXAMPLE.COM',
        admin_id=uuid.uuid4(),
        description='  Some description  ',
        website_link='  https://example.com  ',
    )

    assert company.name == 'Example Company'
    assert company.admin_email == 'admin@example.com'
    assert isinstance(company.admin_id, str)
    assert company.description == 'Some description'
    assert company.website_link == 'https://example.com'


def test_company_model_accepts_boundary_lengths():
    company = Company(
        name=make_text(200),
        admin_email=f"{make_text(242)}@x.com",
        admin_id=str(uuid.uuid4()),
        description=make_text(2000),
        website_link='https://' + make_text(504),  # 512 chars, scheme present
        company_picture=make_text(512),
    )

    assert company.name == make_text(200)
    assert company.admin_email == f"{make_text(242)}@x.com"
    assert company.description == make_text(2000)
    assert company.website_link == 'https://' + make_text(504)
    assert company.company_picture == make_text(512)


@pytest.mark.parametrize('value, expected', [
    ('www.exemple.com', 'https://www.exemple.com'),
    ('  exemple.fr  ', 'https://exemple.fr'),
    ('http://exemple.fr', 'http://exemple.fr'),
    ('https://exemple.fr', 'https://exemple.fr'),
    ('HTTPS://exemple.fr', 'HTTPS://exemple.fr'),
    ('', None),
    ('   ', None),
])
def test_company_website_link_defaults_to_https(value, expected):
    company = Company(name='X', admin_email='a@b.com', website_link=value)
    assert company.website_link == expected


@pytest.mark.parametrize('name', ['', ' ' * 3, 123])
def test_company_model_rejects_invalid_name(name):
    with pytest.raises((TypeError, ValueError)):
        Company(name=name, admin_email='admin@example.com')


@pytest.mark.parametrize(
    'field_name, value, error_type',
    [
        ('name', make_text(201), ValueError),
        ('description', make_text(2001), ValueError),
        ('website_link', make_text(513), ValueError),
        ('company_picture', make_text(513), ValueError),
        ('admin_email', make_text(255) + '@x.com', ValueError),
        ('admin_email', 123, TypeError),
        ('admin_id', 'not-a-uuid', ValueError),
        ('admin_id', 123, TypeError),
    ],
)
def test_company_model_rejects_invalid_field_values(field_name, value, error_type):
    kwargs = {'name': 'Example', 'admin_email': 'admin@example.com'}
    kwargs[field_name] = value

    with pytest.raises(error_type):
        Company(**kwargs)


def test_training_model_validates_title():
    training = Training(title='  Docker Basics  ',
                        company_id='company-id', description='  Intro  ')

    assert training.title == 'Docker Basics'
    assert training.description == 'Intro'
    assert training.company_id == 'company-id'


def test_training_model_accepts_boundary_lengths():
    training = Training(
        title=make_text(200),
        description=make_text(2000),
        picture=make_text(512),
        company_id='company-id',
    )

    assert training.title == make_text(200)
    assert training.description == make_text(2000)
    assert training.picture == make_text(512)


@pytest.mark.parametrize('title', ['', '   ', 123])
def test_training_model_rejects_invalid_title(title):
    with pytest.raises((TypeError, ValueError)):
        Training(title=title)


@pytest.mark.parametrize(
    'field_name, value, error_type',
    [
        ('description', make_text(2001), ValueError),
        ('picture', make_text(513), ValueError),
        ('description', 123, TypeError),
        ('picture', 123, TypeError),
    ],
)
def test_training_model_rejects_invalid_optional_fields(field_name, value, error_type):
    kwargs = {'title': 'Docker Basics'}
    kwargs[field_name] = value

    with pytest.raises(error_type):
        Training(**kwargs)


def test_conversation_model_normalizes_participants():
    conversation = Conversation(participant_ids=('u1', 'u2'))

    assert conversation.participant_ids == ['u1', 'u2']


def test_conversation_model_accepts_empty_participant_list():
    conversation = Conversation()

    assert conversation.participant_ids == []


def test_conversation_model_rejects_invalid_participants():
    with pytest.raises(TypeError):
        Conversation(participant_ids='u1')


def test_message_model_validates_content():
    message = Message()
    message.content = '  Hello world  '

    assert message.content == 'Hello world'


def test_message_model_accepts_boundary_length():
    message = Message()
    message.content = make_text(5000)

    assert message.content == make_text(5000)


@pytest.mark.parametrize('content', [123, '   ', 'a' * 5001])
def test_message_model_rejects_invalid_content(content):
    message = Message()

    with pytest.raises((TypeError, ValueError)):
        message.content = content


def test_notification_model_validates_content():
    notification = Notification()
    notification.content = '  New notification  '

    assert notification.content == 'New notification'


def test_notification_model_accepts_boundary_length():
    notification = Notification()
    notification.content = make_text(1000)

    assert notification.content == make_text(1000)


@pytest.mark.parametrize('content', [123, '   ', 'a' * 1001])
def test_notification_model_rejects_invalid_content(content):
    notification = Notification()

    with pytest.raises((TypeError, ValueError)):
        notification.content = content


def test_news_model_validates_title():
    news = News(title='  Launch update  ')

    assert news.title == 'Launch update'


def test_news_model_accepts_boundary_length():
    news = News(title=make_text(500))

    assert news.title == make_text(500)


@pytest.mark.parametrize('title', [123, '', '   ', 'a' * 501])
def test_news_model_rejects_invalid_title(title):
    with pytest.raises((TypeError, ValueError)):
        News(title=title)


def test_formation_user_validates_required_fields_and_ranges():
    relation = FormationUser(
        user_id='user-id', training_id='training-id', type='interested')

    assert relation.user_id == 'user-id'
    assert relation.training_id == 'training-id'
    assert relation.type == 'interested'


def test_formation_user_accepts_all_valid_types():
    for t in ('interested', 'enrolled', 'completed'):
        fu = FormationUser(user_id='u', training_id='t', type=t)
        assert fu.type == t


@pytest.mark.parametrize(
    'kwargs',
    [
        {'user_id': None, 'training_id': 'training-id'},
        {'user_id': 'user-id', 'training_id': None},
        {'user_id': 'user-id', 'training_id': 'training-id', 'type': 'unknown'},
    ],
)
def test_formation_user_rejects_invalid_values(kwargs):
    with pytest.raises((TypeError, ValueError)):
        FormationUser(**kwargs)


# ---------------------------------------------------------------------------
# TrainingSession model
# ---------------------------------------------------------------------------

_NOW = datetime(2027, 1, 10, 9, 0, tzinfo=timezone.utc)
_END = datetime(2027, 1, 12, 17, 0, tzinfo=timezone.utc)


def test_training_session_validates_required_fields():
    sess = TrainingSession(
        training_id='t-1',
        start_date=_NOW,
        end_date=_END,
        max_participants=20,
    )
    assert sess.training_id == 't-1'
    assert sess.max_participants == 20
    assert sess.status == 'upcoming'


def test_training_session_accepts_all_valid_statuses():
    for status in ('upcoming', 'full', 'completed', 'cancelled'):
        sess = TrainingSession('t', _NOW, _END, 5, status=status)
        assert sess.status == status


def test_training_session_coerces_max_participants_to_int():
    sess = TrainingSession('t', _NOW, _END, '15')
    assert sess.max_participants == 15


def test_training_session_optional_fields_default_to_none():
    sess = TrainingSession('t', _NOW, _END, 10)
    assert sess.location is None
    assert sess.link is None


@pytest.mark.parametrize(
    'kwargs',
    [
        {'training_id': '', 'start_date': _NOW, 'end_date': _END, 'max_participants': 5},
        {'training_id': 't', 'start_date': None, 'end_date': _END, 'max_participants': 5},
        {'training_id': 't', 'start_date': _NOW, 'end_date': None, 'max_participants': 5},
        {'training_id': 't', 'start_date': _NOW, 'end_date': _END, 'max_participants': 0},
        {'training_id': 't', 'start_date': _NOW, 'end_date': _END, 'max_participants': -1},
        {'training_id': 't', 'start_date': _NOW, 'end_date': _END, 'max_participants': 'x'},
        {'training_id': 't', 'start_date': _NOW, 'end_date': _END, 'max_participants': 5,
         'status': 'unknown'},
    ],
)
def test_training_session_rejects_invalid_values(kwargs):
    with pytest.raises((TypeError, ValueError)):
        TrainingSession(**kwargs)


# ---------------------------------------------------------------------------
# ConversationParticipant model
# ---------------------------------------------------------------------------

def test_conversation_participant_stores_ids():
    cp = ConversationParticipant(conversation_id='conv-1', user_id='user-1')
    assert cp.conversation_id == 'conv-1'
    assert cp.user_id == 'user-1'


def test_conversation_participant_strips_whitespace():
    cp = ConversationParticipant(conversation_id='  conv-1  ', user_id='  user-1  ')
    assert cp.conversation_id == 'conv-1'
    assert cp.user_id == 'user-1'


@pytest.mark.parametrize('kwargs', [
    {'conversation_id': '', 'user_id': 'u'},
    {'conversation_id': '  ', 'user_id': 'u'},
    {'conversation_id': 123, 'user_id': 'u'},
    {'conversation_id': 'c', 'user_id': ''},
    {'conversation_id': 'c', 'user_id': 456},
])
def test_conversation_participant_rejects_invalid_ids(kwargs):
    with pytest.raises((TypeError, ValueError)):
        ConversationParticipant(**kwargs)


def test_conversation_participant_validate_static_methods():
    assert ConversationParticipant.validate_conversation_id('  abc  ') == 'abc'
    assert ConversationParticipant.validate_user_id('  xyz  ') == 'xyz'
    with pytest.raises(TypeError):
        ConversationParticipant.validate_conversation_id(99)
    with pytest.raises(ValueError):
        ConversationParticipant.validate_user_id('  ')
