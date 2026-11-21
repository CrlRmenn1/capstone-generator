import pytest
from cryptography.fernet import Fernet

from app import create_app, normalize_database_url
from app.security import _as_fernet_key, decrypt, encrypt


@pytest.mark.parametrize("given, expected", [
    ("postgres://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
    ("postgresql://u:p@host:5432/db?sslmode=require", "postgresql+psycopg://u:p@host:5432/db?sslmode=require"),
    ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
    ("sqlite:///x.db", "sqlite:///x.db"),
])
def test_database_url_normalization(given, expected):
    assert normalize_database_url(given) == expected


def test_any_secret_becomes_a_valid_fernet_key():
    real = Fernet.generate_key()
    assert _as_fernet_key(real) == real
    derived = _as_fernet_key("aRandomRenderGeneratedValue123")
    Fernet(derived)  # valid
    assert derived == _as_fernet_key("aRandomRenderGeneratedValue123")  # stable


@pytest.fixture()
def production_env(monkeypatch, tmp_path):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("SECRET_KEY", "prod-secret")
    monkeypatch.setenv("FERNET_KEY", "render-generated-not-a-fernet-key")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'prod.db'}")


def test_production_mode_hardens_cookies_and_trusts_proxy(production_env):
    app = create_app({"RATELIMIT_ENABLED": False})
    assert app.config["SESSION_COOKIE_SECURE"] and app.config["REMEMBER_COOKIE_SECURE"]
    assert type(app.wsgi_app).__name__ == "ProxyFix"
    with app.app_context():
        assert decrypt(encrypt("sk-test-123456789")) == "sk-test-123456789"
    # The app works end to end behind the proxy.
    resp = app.test_client().get("/api/meta", headers={"X-Forwarded-Proto": "https"})
    assert resp.status_code == 200


def test_production_requires_secret_key(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app({"RATELIMIT_ENABLED": False})
