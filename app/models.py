from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def _now():
    return datetime.now(timezone.utc)


class Title(db.Model):
    """An existing capstone title in the recommendation dataset."""

    __tablename__ = "titles"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False, unique=True)
    abstract = db.Column(db.Text, default="")
    program = db.Column(db.String(10), default="")
    area = db.Column(db.String(40), default="")
    domain = db.Column(db.String(40), default="")
    tags = db.Column(db.Text, default="")
    tech_stack = db.Column(db.Text, default="")
    year = db.Column(db.Integer, nullable=True)
    source = db.Column(db.String(60), default="")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "abstract": self.abstract or "",
            "program": self.program or "",
            "area": self.area or "",
            "domain": self.domain or "",
            "tags": self.tags or "",
            "tech_stack": self.tech_stack or "",
            "year": self.year,
            "source": self.source or "",
        }


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(254), nullable=False, unique=True, index=True)
    program = db.Column(db.String(10), default="BSIT")
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=_now)

    bookmarks = db.relationship("Bookmark", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    outlines = db.relationship("Outline", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    progress = db.relationship("UserProgress", uselist=False, cascade="all, delete-orphan")
    ai_settings = db.relationship("UserAISettings", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "email": self.email, "program": self.program}


class Bookmark(db.Model):
    """A saved title: either generated (template/AI) or from the dataset. Stores a full snapshot."""

    __tablename__ = "bookmarks"
    __table_args__ = (db.UniqueConstraint("user_id", "title", name="uq_bookmark_user_title"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(400), nullable=False)
    source = db.Column(db.String(20), nullable=False)  # template | ai | database
    payload = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=_now)

    def to_dict(self) -> dict:
        return {"id": self.id, "title": self.title, "source": self.source,
                "payload": self.payload, "created_at": self.created_at.isoformat()}


class Outline(db.Model):
    """A Chapter 1 draft developed from one selected title."""

    __tablename__ = "outlines"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(400), nullable=False)
    system_name = db.Column(db.String(120), default="")
    context = db.Column(db.JSON, nullable=False)  # resolved domain/area/problem/technique/... keys
    mode = db.Column(db.String(20), nullable=False, default="template")  # engine used at creation
    created_at = db.Column(db.DateTime(timezone=True), default=_now)
    updated_at = db.Column(db.DateTime(timezone=True), default=_now, onupdate=_now)

    sections = db.relationship("OutlineSection", backref="outline", cascade="all, delete-orphan",
                               order_by="OutlineSection.position")

    def to_dict(self, with_sections: bool = True) -> dict:
        data = {"id": self.id, "title": self.title, "system_name": self.system_name,
                "context": self.context, "mode": self.mode,
                "created_at": self.created_at.isoformat(), "updated_at": self.updated_at.isoformat()}
        if with_sections:
            data["sections"] = [s.to_dict() for s in self.sections]
        return data


class OutlineSection(db.Model):
    __tablename__ = "outline_sections"
    __table_args__ = (db.UniqueConstraint("outline_id", "key", name="uq_section_outline_key"),)

    id = db.Column(db.Integer, primary_key=True)
    outline_id = db.Column(db.Integer, db.ForeignKey("outlines.id"), nullable=False, index=True)
    key = db.Column(db.String(30), nullable=False)
    heading = db.Column(db.String(120), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False, default="")
    source = db.Column(db.String(20), nullable=False, default="template")  # template | ai | user
    is_edited = db.Column(db.Boolean, nullable=False, default=False)
    version = db.Column(db.Integer, nullable=False, default=1)

    def to_dict(self) -> dict:
        return {"id": self.id, "key": self.key, "heading": self.heading, "position": self.position,
                "content": self.content, "source": self.source, "is_edited": self.is_edited,
                "version": self.version}


class UserProgress(db.Model):
    """Onboarding state: whether the welcome tour was seen and which first steps were done.
    (Saving and developing titles are counted from bookmarks/outlines directly.)"""

    __tablename__ = "user_progress"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    tour_seen = db.Column(db.Boolean, nullable=False, default=False)
    checklist_dismissed = db.Column(db.Boolean, nullable=False, default=False)
    generated = db.Column(db.Boolean, nullable=False, default=False)
    exported = db.Column(db.Boolean, nullable=False, default=False)


class UserAISettings(db.Model):
    """A remembered bring-your-own-key AI configuration. The key is stored encrypted."""

    __tablename__ = "user_ai_settings"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    provider = db.Column(db.String(20), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    encrypted_key = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=_now, onupdate=_now)
