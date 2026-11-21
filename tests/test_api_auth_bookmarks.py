from conftest import H, PREFS, register


def test_register_login_logout_flow(client):
    resp = register(client)
    assert resp.status_code == 201
    assert resp.json["user"]["email"] == "ana@example.com"
    assert client.get("/api/auth/me").json["user"]["name"] == "Ana"

    assert client.post("/api/auth/logout", headers=H).status_code == 200
    assert client.get("/api/auth/me").json["user"] is None

    bad = client.post("/api/auth/login", json={"email": "ana@example.com", "password": "wrong"}, headers=H)
    assert bad.status_code == 401
    ok = client.post("/api/auth/login", json={"email": "ANA@example.com", "password": "password123"}, headers=H)
    assert ok.status_code == 200 and ok.json["user"]["name"] == "Ana"


def test_register_validation(client):
    assert register(client, email="not-an-email").status_code == 400
    assert register(client, password="short").status_code == 400
    assert register(client).status_code == 201
    client.post("/api/auth/logout", headers=H)
    assert register(client).status_code == 409


def test_writes_require_csrf_header(client):
    resp = client.post("/api/auth/register", json={"name": "A", "email": "a@b.co", "password": "password123"})
    assert resp.status_code == 403


def test_meta_lists_form_options(client):
    data = client.get("/api/meta").json
    assert {t["key"] for t in data["technologies"]} >= {"iot", "web", "ai_ml"}
    assert {p["key"] for p in data["providers"]} == {"claude", "openai", "gemini"}


def test_generate_titles_anonymous(client):
    resp = client.post("/api/titles/generate", json=PREFS, headers=H)
    assert resp.status_code == 200
    data = resp.json
    assert data["engine"] == "template" and len(data["generated"]) == 8
    assert data["generated"][0]["context"]["domain"] == "agriculture"
    assert data["recommended"]
    again = client.post("/api/titles/generate", json={**PREFS, "seed": data["seed"]}, headers=H).json
    assert [g["title"] for g in again["generated"]] == [g["title"] for g in data["generated"]]


def test_generate_titles_validation(client):
    resp = client.post("/api/titles/generate", json={"domain": "nope"}, headers=H)
    assert resp.status_code == 400
    assert "Pick at least one area of interest." in resp.json["errors"]


def test_ai_mode_without_key_offers_fallback(user_client):
    resp = user_client.post("/api/titles/generate", json={**PREFS, "engine": "ai"}, headers=H)
    assert resp.status_code == 400
    assert resp.json["code"] == "no_key" and resp.json["fallback"] is True


def test_bookmarks_crud_and_isolation(client):
    assert client.get("/api/bookmarks").status_code == 401
    register(client)
    title = client.post("/api/titles/generate", json=PREFS, headers=H).json["generated"][0]
    first = client.post("/api/bookmarks", json={"title": title["title"], "source": "template", "payload": title},
                        headers=H)
    assert first.status_code == 201
    dup = client.post("/api/bookmarks", json={"title": title["title"], "source": "template", "payload": title},
                      headers=H)
    assert dup.json["bookmark"]["id"] == first.json["bookmark"]["id"]
    assert len(client.get("/api/bookmarks").json["bookmarks"]) == 1
    bookmark_id = first.json["bookmark"]["id"]

    # Another student can't see or delete it.
    client.post("/api/auth/logout", headers=H)
    register(client, email="ben@example.com", name="Ben")
    assert client.get("/api/bookmarks").json["bookmarks"] == []
    assert client.delete(f"/api/bookmarks/{bookmark_id}", headers=H).status_code == 404

    client.post("/api/auth/logout", headers=H)
    client.post("/api/auth/login", json={"email": "ana@example.com", "password": "password123"}, headers=H)
    assert client.delete(f"/api/bookmarks/{bookmark_id}", headers=H).status_code == 200
    assert client.get("/api/bookmarks").json["bookmarks"] == []


def test_bookmark_rejects_unknown_source(user_client):
    resp = user_client.post("/api/bookmarks", json={"title": "X", "source": "hacked"}, headers=H)
    assert resp.status_code == 400


def test_unknown_api_path_is_json_404(client):
    resp = client.get("/api/does-not-exist")
    assert resp.status_code == 404 and resp.is_json
