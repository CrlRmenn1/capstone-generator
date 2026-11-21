"""Storage for students' own AI API keys.

- Default: the key lives only in server memory for the current login and is forgotten at logout
  or server restart. It is never put in the browser cookie.
- "Remember my key": stored in the database encrypted with Fernet (AES-128 + HMAC) using a
  server secret (FERNET_KEY in .env, or instance/fernet.key generated on first run).
- Keys are never logged and are only ever shown masked (e.g. "sk-a…b12c").
"""
import os
import threading

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app

from .extensions import db

_session_keys: dict[int, dict] = {}
_lock = threading.Lock()


def _fernet() -> Fernet:
    cached = current_app.extensions.get("fernet")
    if cached:
        return cached
    key = current_app.config.get("FERNET_KEY") or os.environ.get("FERNET_KEY")
    if not key:
        path = os.path.join(current_app.instance_path, "fernet.key")
        if not os.path.exists(path):
            with open(path, "wb") as fh:
                fh.write(Fernet.generate_key())
        with open(path, "rb") as fh:
            key = fh.read().strip()
    fernet = Fernet(key)
    current_app.extensions["fernet"] = fernet
    return fernet


def encrypt(secret: str) -> str:
    return _fernet().encrypt(secret.encode("utf-8")).decode("ascii")


def decrypt(token: str) -> str | None:
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        return None  # e.g. FERNET_KEY changed; the student must re-enter the key


def mask_key(secret: str) -> str:
    if len(secret) <= 10:
        return "•" * len(secret)
    return f"{secret[:4]}…{secret[-4:]}"


def get_ai_config(user_id: int) -> dict | None:
    """The user's active AI config {provider, model, api_key, remember}, or None."""
    with _lock:
        cfg = _session_keys.get(user_id)
    if cfg:
        return dict(cfg)
    from .models import UserAISettings

    saved = db.session.get(UserAISettings, user_id)
    if saved:
        api_key = decrypt(saved.encrypted_key)
        if api_key:
            return {"provider": saved.provider, "model": saved.model, "api_key": api_key, "remember": True}
    return None


def set_ai_config(user_id: int, provider: str, model: str, api_key: str, remember: bool) -> None:
    from .models import UserAISettings

    saved = db.session.get(UserAISettings, user_id)
    if remember:
        if saved is None:
            saved = UserAISettings(user_id=user_id)
            db.session.add(saved)
        saved.provider, saved.model, saved.encrypted_key = provider, model, encrypt(api_key)
        forget_session_key(user_id)
    else:
        if saved is not None:
            db.session.delete(saved)
        with _lock:
            _session_keys[user_id] = {"provider": provider, "model": model, "api_key": api_key,
                                      "remember": False}
    db.session.commit()


def clear_ai_config(user_id: int) -> None:
    from .models import UserAISettings

    forget_session_key(user_id)
    saved = db.session.get(UserAISettings, user_id)
    if saved is not None:
        db.session.delete(saved)
        db.session.commit()


def forget_session_key(user_id: int) -> None:
    with _lock:
        _session_keys.pop(user_id, None)


def ai_status(user_id: int) -> dict | None:
    """Safe-to-display AI settings (no key)."""
    cfg = get_ai_config(user_id)
    if not cfg:
        return None
    return {"provider": cfg["provider"], "model": cfg["model"], "masked_key": mask_key(cfg["api_key"]),
            "remember": cfg["remember"]}
