from flask import jsonify
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Bookmark
from . import api
from .common import body, error, text_field

MAX_BOOKMARKS = 200
SOURCES = {"template", "ai", "database"}


@api.get("/bookmarks")
@login_required
def list_bookmarks():
    items = current_user.bookmarks.order_by(Bookmark.created_at.desc()).all()
    return jsonify(bookmarks=[b.to_dict() for b in items])


@api.post("/bookmarks")
@login_required
def add_bookmark():
    data = body()
    title, err = text_field(data, "title", 400)
    if err:
        return error(err)
    source = data.get("source")
    if source not in SOURCES:
        return error("Unknown title source.")
    payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
    existing = current_user.bookmarks.filter_by(title=title).first()
    if existing:
        return jsonify(bookmark=existing.to_dict())
    if current_user.bookmarks.count() >= MAX_BOOKMARKS:
        return error(f"You can save up to {MAX_BOOKMARKS} titles. Remove some first.", 409, "limit")
    bookmark = Bookmark(user_id=current_user.id, title=title, source=source, payload=payload)
    db.session.add(bookmark)
    db.session.commit()
    return jsonify(bookmark=bookmark.to_dict()), 201


@api.delete("/bookmarks/<int:bookmark_id>")
@login_required
def delete_bookmark(bookmark_id: int):
    bookmark = current_user.bookmarks.filter_by(id=bookmark_id).first()
    if not bookmark:
        return error("Bookmark not found.", 404, "not_found")
    db.session.delete(bookmark)
    db.session.commit()
    return jsonify(ok=True)
