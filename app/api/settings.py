from flask import jsonify
from flask_login import current_user, login_required

from ..ai.providers import PROVIDERS, ProviderError, test_connection
from ..extensions import limiter
from ..security import ai_status, clear_ai_config, get_ai_config, set_ai_config
from . import api
from .common import body, error


@api.get("/settings/ai")
@login_required
def get_ai_settings():
    return jsonify(ai=ai_status(current_user.id))


@api.put("/settings/ai")
@login_required
def save_ai_settings():
    data = body()
    provider = data.get("provider")
    if provider not in PROVIDERS:
        return error("Choose an AI provider.")
    model = str(data.get("model") or "").strip() or PROVIDERS[provider].default_model
    if len(model) > 100:
        return error("Model name is too long.")
    api_key = str(data.get("api_key") or "").strip()
    existing = get_ai_config(current_user.id)
    if not api_key:
        # Allow changing provider settings without retyping the key, but only for the same provider.
        if not existing or existing["provider"] != provider:
            return error("Paste your API key.")
        api_key = existing["api_key"]
    if not 10 <= len(api_key) <= 400 or any(c.isspace() for c in api_key):
        return error("That doesn't look like a valid API key.")
    set_ai_config(current_user.id, provider, model, api_key, remember=bool(data.get("remember")))
    return jsonify(ai=ai_status(current_user.id))


@api.delete("/settings/ai")
@login_required
def delete_ai_settings():
    clear_ai_config(current_user.id)
    return jsonify(ai=None)


@api.post("/settings/ai/test")
@login_required
@limiter.limit("10 per minute")
def test_ai_settings():
    cfg = get_ai_config(current_user.id)
    if not cfg:
        return error("Save an API key first.", 400, "no_key")
    try:
        test_connection(cfg["provider"], cfg["api_key"], cfg["model"])
    except ProviderError as exc:
        return error(str(exc), 400, exc.code)
    return jsonify(ok=True, message=f"Connected to {PROVIDERS[cfg['provider']].label} ({cfg['model']}).")
