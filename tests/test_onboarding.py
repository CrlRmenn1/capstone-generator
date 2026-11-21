from conftest import H, PREFS


def progress(client):
    return client.get("/api/auth/me").json["progress"]


def test_new_user_starts_with_empty_progress(user_client):
    assert progress(user_client) == {"tour_seen": False, "checklist_dismissed": False, "generated": False,
                                     "saved": False, "developed": False, "exported": False}


def test_checklist_follows_real_actions(user_client):
    title = user_client.post("/api/titles/generate", json=PREFS, headers=H).json["generated"][0]
    assert progress(user_client)["generated"] is True

    user_client.post("/api/bookmarks", json={"title": title["title"], "source": "template", "payload": title},
                     headers=H)
    assert progress(user_client)["saved"] is True

    oid = user_client.post("/api/outlines", json={"title": title["title"], "context": title["context"]},
                           headers=H).json["outline"]["id"]
    assert progress(user_client)["developed"] is True

    user_client.get(f"/api/outlines/{oid}/export?format=docx")
    assert progress(user_client)["exported"] is True


def test_tour_and_checklist_actions(user_client):
    for action, key, value in [("tour_seen", "tour_seen", True), ("tour_reset", "tour_seen", False),
                               ("dismiss_checklist", "checklist_dismissed", True),
                               ("restore_checklist", "checklist_dismissed", False)]:
        resp = user_client.post("/api/progress", json={"action": action}, headers=H)
        assert resp.status_code == 200 and resp.json["progress"][key] is value
    assert user_client.post("/api/progress", json={"action": "exported"}, headers=H).status_code == 400


def test_progress_requires_login_and_anonymous_generate_still_works(client):
    assert client.post("/api/progress", json={"action": "tour_seen"}, headers=H).status_code == 401
    assert client.post("/api/titles/generate", json=PREFS, headers=H).status_code == 200
    assert client.get("/api/auth/me").json["progress"] is None
