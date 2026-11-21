import os

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from .extensions import db, limiter, login_manager

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_path=os.path.join(BASE_DIR, "instance"), static_folder=None)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY") or _dev_secret(app.instance_path),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///" + os.path.join(app.instance_path, "capsense.db")
        ),
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_HTTPONLY=True,
        RATELIMIT_ENABLED=True,
        SEED_TITLES_CSV=os.path.join(BASE_DIR, "data", "seed_titles.csv"),
        KB_DIR=os.path.join(BASE_DIR, "data", "knowledge_base"),
        AUTO_SEED=True,  # import the seed CSV on first run when the titles table is empty
        TITLES_PER_PAGE=8,
        FRONTEND_DIST=FRONTEND_DIST,
    )
    if config:
        app.config.update(config)

    db.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    from .importer import import_titles_from_csv
    from .knowledge_base import KnowledgeBase
    from .models import Title, User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify(error="Please log in first.", code="unauthorized"), 401

    with app.app_context():
        db.create_all()
        if app.config["AUTO_SEED"] and db.session.query(Title.id).first() is None:
            import_titles_from_csv(app.config["SEED_TITLES_CSV"])
        app.extensions["kb"] = KnowledgeBase.load(app.config["KB_DIR"])
        rebuild_recommender(app)

    from .api import api

    app.register_blueprint(api)
    _register_errors(app)
    _register_frontend(app)
    return app


def _dev_secret(instance_path: str) -> str:
    """A random per-install secret when SECRET_KEY isn't set, so sessions survive restarts."""
    path = os.path.join(instance_path, "secret.key")
    if not os.path.exists(path):
        with open(path, "w", encoding="ascii") as fh:
            fh.write(os.urandom(32).hex())
    with open(path, encoding="ascii") as fh:
        return fh.read().strip()


def _register_errors(app: Flask) -> None:
    @app.errorhandler(429)
    def too_many(exc):
        return jsonify(error="Too many requests. Please wait a moment and try again.",
                       code="rate_limited"), 429

    @app.errorhandler(HTTPException)
    def http_error(exc):
        if request.path.startswith("/api/"):
            return jsonify(error=exc.description, code=exc.name.lower().replace(" ", "_")), exc.code
        return exc


def _register_frontend(app: Flask) -> None:
    """Serve the built React app (frontend/dist) for every non-API path."""

    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def frontend(path: str):
        dist = app.config["FRONTEND_DIST"]
        if path.startswith("api/"):
            return jsonify(error="Not found.", code="not_found"), 404
        if path and os.path.isfile(os.path.join(dist, path)):
            return send_from_directory(dist, path)
        index = os.path.join(dist, "index.html")
        if os.path.isfile(index):
            return send_from_directory(dist, "index.html")
        return ("The React frontend hasn't been built yet. Run `npm run build` in the frontend folder, "
                "or use the dev server with `npm run dev`.", 503)


def rebuild_recommender(app: Flask) -> None:
    """(Re)build the TF-IDF index from the titles table. Call after the dataset changes."""
    from .models import Title
    from .recommender import Recommender

    items = [t.to_dict() for t in Title.query.order_by(Title.id).all()]
    app.extensions["recommender"] = Recommender(items)
    app.extensions.pop("template_engine", None)  # engine holds the old recommender
