from flask import current_app, jsonify
from flask_login import current_user

from ..engines import EngineError, Preferences, get_title_engine
from ..extensions import limiter
from ..progress import mark
from . import api
from .common import body, error


@api.post("/titles/generate")
@limiter.limit("30 per minute")
def generate_titles():
    data = body()
    kb = current_app.extensions["kb"]
    prefs, errors = Preferences.from_json(data, kb)
    if errors:
        return error(" ".join(errors), 400, "invalid_preferences", errors=errors)

    seed = data.get("seed")
    seed = seed if isinstance(seed, int) and not isinstance(seed, bool) else prefs.default_seed()
    count = current_app.config["TITLES_PER_PAGE"]

    try:
        engine = get_title_engine(current_app, current_user, data.get("engine"))
        generated = engine.generate_titles(prefs, count=count, seed=seed)
    except EngineError as exc:
        # The frontend offers "use default mode instead" for these.
        return error(str(exc), 502 if exc.code != "no_key" else 400, exc.code, fallback=True)

    mark(current_user, "generated")  # getting-started checklist (logged-in users only)
    recommended = current_app.extensions["recommender"].recommend(
        prefs.query_text(kb), top_n=count, program=prefs.program,
        domain=prefs.domain, areas=prefs.interests,
    )
    return jsonify(
        prefs=prefs.to_dict(),
        seed=seed,
        engine=engine.source,
        generated=[g.to_dict() for g in generated],
        recommended=recommended,
    )
