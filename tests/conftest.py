import pytest

from mindtrack import create_app
from mindtrack.database import db
from mindtrack.models.user import User
from mindtrack.utils.security import hash_password


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "ENV_NAME": "testing",
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SESSION_COOKIE_SECURE": False,
        }
    )

    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.add(
            User(
                name="Test User",
                email="test@example.com",
                password_hash=hash_password("123456"),
            )
        )
        db.session.commit()

    yield app


@pytest.fixture
def client(app):
    return app.test_client()
