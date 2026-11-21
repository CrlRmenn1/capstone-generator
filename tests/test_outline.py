import io
import itertools
import re

import pytest
from docx import Document

from conftest import H, PREFS, register
from app.engines import SECTION_KEYS, TemplateOutlineEngine
from app.engines.context import resolve_context


def numbered(text: str) -> list[str]:
    return re.findall(r"^\d+\. .+$", text, flags=re.M)


@pytest.fixture()
def outline_engine(kb):
    return TemplateOutlineEngine(kb)


def test_every_domain_and_area_produces_a_complete_aligned_chapter(kb, outline_engine):
    for domain, area in itertools.product(kb.domains, kb.technologies):
        ctx = resolve_context(kb, "Some Capstone Title", {"domain": domain, "area": area})
        written = outline_engine.write_all("Some Capstone Title", ctx)
        assert set(written) == set(SECTION_KEYS)
        for key, text in written.items():
            assert text.strip(), f"{domain}/{area}/{key} empty"
            assert "{" not in text and "}" not in text, f"{domain}/{area}/{key}: {text[:80]}"
            assert " a a" not in text and " an a " not in text.lower()
            assert not re.search(r"\b(many|of) (the|a|an) \w+ (the|a|an)\b", text.lower())
            assert " of The " not in text and "In many the" not in text and "In many a " not in text
        # Each specific problem has a matching objective.
        assert len(numbered(written["problem"])) == len(numbered(written["objectives"])) == 4
        assert "[cite source]" in written["background"]


def test_context_from_generated_title_is_kept(kb, app):
    with app.test_request_context():
        from app.engines import Preferences, get_title_engine
        prefs, _ = Preferences.from_json(PREFS, kb)
        title = get_title_engine(app).generate_titles(prefs, seed=1)[0]
    ctx = resolve_context(kb, title.title, title.context, title.system_name)
    assert ctx["problem"] == title.context["problem"]
    assert ctx["technique"] == title.context["technique"]
    assert ctx["system_name"] == title.system_name


def test_context_is_inferred_for_a_typed_title(kb):
    ctx = resolve_context(kb, "FloodWatch: An IoT-Based Flood Early Warning System with SMS Alerts",
                          {"domain": "disaster", "area": "iot"})
    assert ctx["problem"] == "flood early warning"
    assert ctx["system_name"] == "FloodWatch"
    with pytest.raises(ValueError):
        resolve_context(kb, "Anything", {"domain": "nowhere", "area": "iot"})


def _create(client, **extra):
    body = {"title": "FloodWatch: An IoT-Based Flood Early Warning System",
            "context": {"domain": "disaster", "area": "iot"}, **extra}
    return client.post("/api/outlines", json=body, headers=H)


def test_outline_api_create_edit_regenerate_delete(user_client):
    resp = _create(user_client)
    assert resp.status_code == 201
    outline = resp.json["outline"]
    assert [s["key"] for s in outline["sections"]] == SECTION_KEYS
    oid = outline["id"]
    assert user_client.get("/api/outlines").json["outlines"][0]["id"] == oid

    edited = user_client.patch(f"/api/outlines/{oid}/sections/background",
                               json={"content": "My own background."}, headers=H)
    assert edited.status_code == 200
    assert edited.json["section"]["is_edited"] and edited.json["section"]["source"] == "user"

    regen = user_client.post(f"/api/outlines/{oid}/sections/background/regenerate", json={}, headers=H)
    assert regen.status_code == 200
    section = regen.json["section"]
    assert section["content"] != "My own background." and not section["is_edited"]
    assert section["version"] == 3

    other = user_client.get(f"/api/outlines/{oid}").json["outline"]["sections"]
    assert other[1]["content"] == outline["sections"][1]["content"]  # untouched

    assert user_client.delete(f"/api/outlines/{oid}", headers=H).status_code == 200
    assert user_client.get(f"/api/outlines/{oid}").status_code == 404


def test_outline_requires_login_and_valid_context(client):
    assert _create(client).status_code == 401
    register(client)
    bad = client.post("/api/outlines", json={"title": "X", "context": {"domain": "nope", "area": "iot"}},
                      headers=H)
    assert bad.status_code == 400


def test_outlines_are_private(client):
    register(client)
    oid = _create(client).json["outline"]["id"]
    client.post("/api/auth/logout", headers=H)
    register(client, email="ben@example.com")
    assert client.get(f"/api/outlines/{oid}").status_code == 404
    assert client.get(f"/api/outlines/{oid}/export?format=docx").status_code == 404


def test_export_docx_has_headings_in_order(user_client):
    oid = _create(user_client).json["outline"]["id"]
    resp = user_client.get(f"/api/outlines/{oid}/export?format=docx")
    assert resp.status_code == 200
    assert "attachment" in resp.headers["Content-Disposition"]
    doc = Document(io.BytesIO(resp.data))
    texts = [p.text for p in doc.paragraphs]
    assert "CHAPTER I" in texts and "INTRODUCTION" in texts
    headings = [t for t in texts if re.match(r"^1\.\d ", t)]
    assert headings == [
        "1.1 Background of the Study", "1.2 Statement of the Problem", "1.3 Objectives of the Study",
        "1.4 Significance of the Study", "1.5 Scope and Limitations", "1.6 Definition of Terms",
        "1.7 Overview of the Proposed System",
    ]
    assert not any("**" in t for t in texts)  # bold markers became real bold runs


def test_export_filename_is_clean():
    from app.exporter import safe_filename
    name = safe_filename("Development of a Web-Based Patient Record Management Portal Using X", "docx")
    assert "__" not in name and name.endswith("_Chapter1.docx")


def test_export_pdf(user_client):
    oid = _create(user_client).json["outline"]["id"]
    resp = user_client.get(f"/api/outlines/{oid}/export?format=pdf")
    assert resp.status_code == 200 and resp.data[:5] == b"%PDF-"
    assert user_client.get(f"/api/outlines/{oid}/export?format=exe").status_code == 400
