import re

from flask import jsonify
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db, limiter
from ..knowledge_base import PROGRAMS
from ..models import User
from ..progress import mark, progress_dict
from ..security import ai_status, forget_session_key
from . import api
from .common import body, error, text_field

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD = 8


def _me():
    if not current_user.is_authenticated:
        return {"user": None, "ai": None, "progress": None}
    return {"user": current_user.to_dict(), "ai": ai_status(current_user.id),
            "progress": progress_dict(current_user)}


@api.get("/auth/me")
def me():
    return jsonify(_me())


# Onboarding actions the frontend can record. "generated" and "exported" are recorded by
# the server itself when those actions really happen.
PROGRESS_ACTIONS = {
    "tour_seen": ("tour_seen", True),
    "tour_reset": ("tour_seen", False),
    "dismiss_checklist": ("checklist_dismissed", True),
    "restore_checklist": ("checklist_dismissed", False),
}


@api.post("/progress")
@login_required
def update_progress():
    action = body().get("action")
    if action not in PROGRESS_ACTIONS:
        return error("Unknown action.")
    mark(current_user, *PROGRESS_ACTIONS[action])
    return jsonify(progress=progress_dict(current_user))


@api.post("/auth/register")
@limiter.limit("10 per hour")
def register():
    data = body()
    name, err = text_field(data, "name", 120)
    if err:
        return error(err)
    email, err = text_field(data, "email", 254)
    if err:
        return error(err)
    email = email.lower()
    if not _EMAIL.match(email):
        return error("Please enter a valid email address.")
    password = data.get("password") if isinstance(data.get("password"), str) else ""
    if len(password) < MIN_PASSWORD:
        return error(f"Password must be at least {MIN_PASSWORD} characters.")
    program = data.get("program") if data.get("program") in PROGRAMS else "BSIT"
    if User.query.filter_by(email=email).first():
        return error("An account with this email already exists.", 409, "email_taken")

    user = User(name=name, email=email, program=program)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user, remember=True)
    return jsonify(_me()), 201


@api.post("/auth/login")
@limiter.limit("10 per minute")
def login():
    data = body()
    email = str(data.get("email") or "").strip().lower()
    password = data.get("password") if isinstance(data.get("password"), str) else ""
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return error("Incorrect email or password.", 401, "invalid_credentials")
    login_user(user, remember=bool(data.get("remember", True)))
    return jsonify(_me())


@api.post("/auth/logout")
@login_required
def logout():
    forget_session_key(current_user.id)  # session-only API keys end with the session
    logout_user()
    return jsonify(user=None, ai=None, progress=None)
