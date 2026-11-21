"""BYOK tests. No real provider is called: generate_json is replaced with a fake."""
import pytest
from cryptography.fernet import Fernet

from conftest import H, PREFS
from app import create_app
from app.ai.providers import ProviderError
from app.engines import ai_engine
from app.models import UserAISettings
from app.security import decrypt, encrypt, mask_key

FAKE_KEY = "sk-test-abcdefghijklmnop1234"


@pytest.fixture(autouse=True)
def clear_cache():
    ai_engine._CACHE.clear()


def save_key(client, remember=False, provider="claude"):
    return client.put("/api/settings/ai", json={"provider": provider, "api_key": FAKE_KEY,
                                                "remember": remember}, headers=H)


def fake_titles(calls):
    def fake(provider, api_key, model, system, prompt, schema, max_tokens=16000):
        calls.append(prompt)
        if "titles" in schema["properties"]:
            return {"titles": [
                {"title": f"AgriBot {i}: A Smart Farm Helper Number {i} for Farmers", "system_name": f"AgriBot{i}",
                 "abstract": "Helps farmers monitor soil.", "objectives": ["To a", "To b", "To c", "To d"],
                 "stack": ["Flutter", "ESP32"], "difficulty": "intermediate", "area": "iot"}
                for i in range(3)
            ] + [
                # A copy of an existing dataset title must be filtered out.
                {"title": "An IoT-Based Soil Moisture Monitoring and Automated Irrigation System",
                 "system_name": "Copy", "abstract": "x", "objectives": [], "stack": [],
                 "difficulty": "beginner", "area": "iot"},
                {"title": "", "system_name": "", "abstract": "", "objectives": [], "stack": [],
                 "difficulty": "beginner", "area": "iot"},
            ]}
        if "content" in schema["properties"]:
            return {"content": "AI section text [cite source]."}
        return {k: f"AI {k} text." for k in schema["properties"]}
    return fake


def test_encryption_and_masking(app):
    with app.app_context():
        token = encrypt(FAKE_KEY)
        assert FAKE_KEY not in token and decrypt(token) == FAKE_KEY
        assert decrypt("garbage") is None
    assert mask_key(FAKE_KEY) == "sk-t…1234"


def test_session_key_is_not_stored_and_is_forgotten_on_logout(user_client, app):
    resp = save_key(user_client, remember=False)
    assert resp.status_code == 200
    assert resp.json["ai"]["masked_key"] == "sk-t…1234"
    with app.app_context():
        assert UserAISettings.query.count() == 0
    me = user_client.get("/api/auth/me")
    assert FAKE_KEY not in me.get_data(as_text=True)
    assert me.json["ai"]["provider"] == "claude"

    user_client.post("/api/auth/logout", headers=H)
    user_client.post("/api/auth/login", json={"email": "ana@example.com", "password": "password123"}, headers=H)
    assert user_client.get("/api/auth/me").json["ai"] is None


def test_remembered_key_is_encrypted_at_rest(user_client, app):
    assert save_key(user_client, remember=True).status_code == 200
    with app.app_context():
        saved = UserAISettings.query.one()
        assert FAKE_KEY not in saved.encrypted_key
        assert decrypt(saved.encrypted_key) == FAKE_KEY
    # Survives logout, unlike a session-only key.
    user_client.post("/api/auth/logout", headers=H)
    user_client.post("/api/auth/login", json={"email": "ana@example.com", "password": "password123"}, headers=H)
    assert user_client.get("/api/auth/me").json["ai"]["remember"] is True
    assert user_client.delete("/api/settings/ai", headers=H).json["ai"] is None
    with app.app_context():
        assert UserAISettings.query.count() == 0


def test_settings_validation(user_client):
    assert user_client.put("/api/settings/ai", json={"provider": "nope", "api_key": FAKE_KEY},
                           headers=H).status_code == 400
    assert user_client.put("/api/settings/ai", json={"provider": "claude", "api_key": "short"},
                           headers=H).status_code == 400
    assert user_client.put("/api/settings/ai", json={"provider": "claude"}, headers=H).status_code == 400


def test_ai_titles_are_mapped_filtered_and_cached(user_client, monkeypatch):
    calls = []
    monkeypatch.setattr(ai_engine, "generate_json", fake_titles(calls))
    save_key(user_client)
    body = {**PREFS, "engine": "ai", "seed": 5}
    resp = user_client.post("/api/titles/generate", json=body, headers=H)
    assert resp.status_code == 200, resp.json
    data = resp.json
    assert data["engine"] == "ai"
    titles = [g["title"] for g in data["generated"]]
    assert len(titles) == 3 and all(t.startswith("AgriBot") for t in titles)
    assert all(g["source"] == "ai" and g["context"]["domain"] == "agriculture" for g in data["generated"])
    assert data["generated"][0]["matched_stack"] == ["Flutter"]
    # The prompt includes existing titles (RAG) so the model avoids repeating them.
    assert "Existing capstones" in calls[0] and "Soil Moisture" in calls[0]

    user_client.post("/api/titles/generate", json=body, headers=H)
    assert len(calls) == 1  # same request served from cache
    user_client.post("/api/titles/generate", json={**body, "seed": 6}, headers=H)
    assert len(calls) == 2


def test_provider_error_returns_fallback_hint(user_client, monkeypatch):
    def broken(*args, **kwargs):
        raise ProviderError("invalid_key")
    monkeypatch.setattr(ai_engine, "generate_json", broken)
    save_key(user_client)
    resp = user_client.post("/api/titles/generate", json={**PREFS, "engine": "ai"}, headers=H)
    assert resp.status_code == 502
    assert resp.json["code"] == "invalid_key" and resp.json["fallback"] is True
    assert "rejected your API key" in resp.json["error"]
    assert FAKE_KEY not in resp.get_data(as_text=True)


def test_ai_outline_and_section_regenerate(user_client, monkeypatch):
    calls = []
    monkeypatch.setattr(ai_engine, "generate_json", fake_titles(calls))
    save_key(user_client)
    resp = user_client.post("/api/outlines", json={"title": "AgriBot: A Smart Farm Helper",
                                                   "context": {"domain": "agriculture", "area": "iot"},
                                                   "engine": "ai"}, headers=H)
    assert resp.status_code == 201
    outline = resp.json["outline"]
    assert outline["mode"] == "ai" and outline["sections"][0]["content"] == "AI background text."
    assert len(calls) == 1  # whole chapter in one request

    oid = outline["id"]
    regen = user_client.post(f"/api/outlines/{oid}/sections/objectives/regenerate", json={"engine": "ai"},
                             headers=H)
    assert regen.status_code == 200 and regen.json["section"]["source"] == "ai"
    # Regenerating objectives shows the model the current problems so they stay aligned.
    assert "AI problem text." in calls[-1]


def test_rate_limit_returns_json_429():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                      "FERNET_KEY": Fernet.generate_key(), "SECRET_KEY": "t", "RATELIMIT_ENABLED": True})
    client = app.test_client()
    codes = [client.post("/api/titles/generate", json=PREFS, headers=H).status_code for _ in range(31)]
    assert codes[:30] == [200] * 30 and codes[30] == 429
    assert client.post("/api/titles/generate", json=PREFS, headers=H).json["code"] == "rate_limited"
