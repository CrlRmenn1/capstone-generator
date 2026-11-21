from flask import current_app, jsonify

from ..ai.providers import PROVIDERS
from ..knowledge_base import DIFFICULTY_LEVELS, PROGRAMS
from . import api


@api.get("/meta")
def meta():
    """Options for the preference form."""
    kb = current_app.extensions["kb"]
    return jsonify(
        programs=[{"key": k, "label": v} for k, v in PROGRAMS.items()],
        levels=DIFFICULTY_LEVELS,
        technologies=[{"key": k, "label": t["label"]} for k, t in kb.technologies.items()],
        domains=[{"key": k, "label": d["label"]} for k, d in kb.domains.items()],
        providers=[{"key": k, "label": p.label, "default_model": p.default_model, "key_hint": p.key_hint,
                    "key_url": p.key_url} for k, p in PROVIDERS.items()],
    )
