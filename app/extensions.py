from flask import request
from flask_limiter import Limiter
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy


def _rate_limit_key() -> str:
    """Rate-limit per logged-in user, or per IP address for anonymous visitors."""
    if current_user and current_user.is_authenticated:
        return f"user:{current_user.id}"
    return f"ip:{request.remote_addr}"


db = SQLAlchemy()
login_manager = LoginManager()
limiter = Limiter(key_func=_rate_limit_key, storage_uri="memory://")
