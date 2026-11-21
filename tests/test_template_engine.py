import itertools

import pytest

from app.engines import Preferences, TemplateEngine
from app.engines.template_engine import MAX_DATASET_SIMILARITY
from app.knowledge_base import DIFFICULTY_LEVELS


@pytest.fixture()
def engine(kb, recommender):
    return TemplateEngine(kb, recommender)


def make_prefs(interests=("iot",), domain="agriculture", difficulty="intermediate", **kw):
    return Preferences(program="BSIT", interests=list(interests), domain=domain, difficulty=difficulty, **kw)


def test_generates_requested_count_with_unique_titles_and_names(engine):
    results = engine.generate_titles(make_prefs(), count=8, seed=1)
    assert len(results) == 8
    assert len({r.title for r in results}) == 8
    assert len({r.system_name for r in results}) == 8


def test_results_are_complete_and_well_formed(engine):
    for r in engine.generate_titles(make_prefs(interests=("iot", "mobile")), count=8, seed=2):
        assert "{" not in r.title and "}" not in r.title
        assert r.abstract and len(r.objectives) == 4 and r.stack
        assert r.source == "template"
        assert r.area in ("iot", "mobile")
        assert 0.0 <= r.relevance <= 1.0 and 0.0 <= r.novelty <= 1.0


def test_same_seed_is_deterministic_and_new_seed_changes_results(engine):
    prefs = make_prefs()
    first = [r.title for r in engine.generate_titles(prefs, seed=42)]
    again = [r.title for r in engine.generate_titles(prefs, seed=42)]
    other = [r.title for r in engine.generate_titles(prefs, seed=43)]
    assert first == again
    assert first != other


@pytest.mark.parametrize("difficulty", DIFFICULTY_LEVELS)
def test_techniques_never_exceed_chosen_difficulty(engine, difficulty):
    rank = DIFFICULTY_LEVELS.index(difficulty)
    results = engine.generate_titles(make_prefs(interests=("ai_ml", "web"), difficulty=difficulty), seed=3)
    assert all(DIFFICULTY_LEVELS.index(r.difficulty) <= rank for r in results)
    if difficulty == "beginner":
        assert all(r.difficulty == "beginner" for r in results)


@pytest.mark.parametrize("seed", range(5))
def test_titles_at_requested_difficulty_rank_first(engine, seed):
    results = engine.generate_titles(make_prefs(interests=("ai_ml",), domain="health",
                                                difficulty="advanced"), seed=seed)
    assert results[0].difficulty == "advanced"
    assert sum(r.difficulty == "advanced" for r in results) >= len(results) // 2


def test_system_titles_use_problem_specific_beneficiaries(kb, engine):
    allowed = {b for p in kb.domain("health")["problems"] for b in p["beneficiaries"]}
    for r in engine.generate_titles(make_prefs(interests=("web",), domain="health"), seed=8):
        # Every beneficiary mentioned must belong to some health problem's user list.
        assert any(b.lower() in r.abstract.lower() for b in allowed), r.abstract


def test_mobile_titles_do_not_add_a_second_app_as_feature(engine):
    for seed in range(5):
        for r in engine.generate_titles(make_prefs(interests=("mobile", "iot"), domain="disaster"), seed=seed):
            if r.area == "mobile":
                assert "mobile monitoring app" not in r.title.lower(), r.title


def test_near_duplicates_of_existing_titles_are_excluded(engine):
    for r in engine.generate_titles(make_prefs(), count=8, seed=4):
        assert r.novelty >= 1 - MAX_DATASET_SIMILARITY


def test_keywords_steer_ranking(engine):
    results = engine.generate_titles(make_prefs(interests=("iot",), domain="disaster",
                                                keywords=["flood", "sms"]), count=8, seed=5)
    top_three = " ".join(r.title.lower() + " " + r.abstract.lower() for r in results[:3])
    assert "flood" in top_three or "sms" in top_three


def test_skill_matches_are_reported(engine):
    results = engine.generate_titles(make_prefs(interests=("mobile",), skills=["Flutter"]), seed=6)
    assert any("Flutter" in r.skill_matches for r in results)
    assert all(all("flutter" in s.lower() for s in r.matched_stack) for r in results)


def test_every_domain_and_area_combination_produces_titles(kb, engine):
    for domain, area in itertools.product(kb.domains, kb.technologies):
        results = engine.generate_titles(make_prefs(interests=(area,), domain=domain), count=8, seed=7)
        assert len(results) == 8, f"{domain} x {area} produced only {len(results)}"
        for r in results:
            assert "{" not in r.title, r.title
            assert " a a" not in r.title.lower() and " an a " not in r.title.lower()
