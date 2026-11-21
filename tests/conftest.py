import pytest
from cryptography.fernet import Fernet

from app import create_app

H = {"X-CapSense": "1"}  # CSRF header the API requires on writes

PREFS = {"program": "BSIT", "interests": ["iot", "mobile"], "domain": "agriculture",
         "difficulty": "intermediate", "skills": "Flutter, Arduino", "keywords": "soil"}


@pytest.fixture()
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "RATELIMIT_ENABLED": False,
        "FERNET_KEY": Fernet.generate_key(),
        "SECRET_KEY": "test",
    })


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def kb(app):
    return app.extensions["kb"]


@pytest.fixture()
def recommender(app):
    return app.extensions["recommender"]


def register(client, email="ana@example.com", password="password123", name="Ana"):
    return client.post("/api/auth/register", json={"name": name, "email": email, "password": password,
                                                   "program": "BSIT"}, headers=H)


@pytest.fixture()
def user_client(client):
    assert register(client).status_code == 201
    return client
