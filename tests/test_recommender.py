from app.recommender import Recommender


def test_iot_agriculture_query_ranks_iot_agri_titles_first(recommender):
    results = recommender.recommend("iot sensors agriculture soil irrigation farm", top_n=3)
    assert results, "expected at least one recommendation"
    top = results[0]
    assert top["domain"] == "agriculture"
    assert top["area"] == "iot"


def test_recommendations_stay_in_the_chosen_domain(kb, recommender):
    from app.engines import Preferences
    prefs = Preferences("BSIT", ["iot", "mobile"], "disaster", "intermediate", keywords=["flood"])
    top = recommender.recommend(prefs.query_text(kb), top_n=4, domain=prefs.domain, areas=prefs.interests)
    assert all(r["domain"] == "disaster" for r in top), [r["title"] for r in top]


def test_scores_are_between_zero_and_one(recommender):
    for r in recommender.recommend("mobile app health appointment", top_n=10):
        assert 0.0 < r["similarity"] <= 1.0


def test_empty_query_and_empty_dataset():
    assert Recommender([]).recommend("anything") == []
    assert Recommender([{"title": "Some Title"}]).recommend("   ") == []


def test_program_boost_breaks_ties():
    items = [
        {"title": "Inventory System for Stores", "program": "BSCS"},
        {"title": "Inventory System for Stores", "program": "BSIT"},
    ]
    rec = Recommender(items)
    assert rec.recommend("inventory system", program="BSIT")[0]["program"] == "BSIT"
    assert rec.recommend("inventory system", program="BSCS")[0]["program"] == "BSCS"


def test_max_similarity_detects_existing_title(recommender):
    existing = recommender.items[0]["title"]
    sims = recommender.max_similarity([existing, "Completely unrelated words zebra xylophone"])
    assert sims[0] > 0.99
    assert sims[1] < 0.2


def test_closest_titles_returns_the_matching_title(recommender):
    existing = recommender.items[5]["title"]
    (title, sim), = recommender.closest_titles([existing])
    assert title == existing and sim > 0.99
