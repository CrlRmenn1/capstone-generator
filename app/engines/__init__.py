"""Engine selection: the default (template) engines, or the user's own-key AI engines."""
from .base import (OUTLINE_SECTIONS, SECTION_KEYS, EngineError, GeneratedTitle, OutlineEngine,
                   Preferences, TitleEngine)
from .outline_template import TemplateOutlineEngine
from .template_engine import TemplateEngine


def _ai_config(user):
    from ..security import get_ai_config

    if not (user and user.is_authenticated):
        raise EngineError("Log in and add your own API key in Settings to use AI mode.", "no_key")
    cfg = get_ai_config(user.id)
    if not cfg:
        raise EngineError("Add your own API key in Settings to use AI mode.", "no_key")
    return cfg


def get_title_engine(app, user=None, requested: str | None = None) -> TitleEngine:
    """``requested`` is "ai" or "template" (default)."""
    if requested == "ai":
        from .ai_engine import AITitleEngine

        return AITitleEngine(app.extensions["kb"], app.extensions["recommender"], _ai_config(user), user.id)
    engine = app.extensions.get("template_engine")
    if engine is None:
        engine = TemplateEngine(app.extensions["kb"], app.extensions["recommender"])
        app.extensions["template_engine"] = engine
    return engine


def get_outline_engine(app, user=None, requested: str | None = None) -> OutlineEngine:
    if requested == "ai":
        from .ai_engine import AIOutlineEngine

        return AIOutlineEngine(app.extensions["kb"], _ai_config(user))
    return TemplateOutlineEngine(app.extensions["kb"])


# Backwards-compatible name used by earlier code and tests.
get_engine = get_title_engine

__all__ = ["OUTLINE_SECTIONS", "SECTION_KEYS", "EngineError", "GeneratedTitle", "OutlineEngine",
           "Preferences", "TitleEngine", "TemplateEngine", "TemplateOutlineEngine",
           "get_engine", "get_title_engine", "get_outline_engine"]
