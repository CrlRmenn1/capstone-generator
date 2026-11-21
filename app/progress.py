"""Onboarding progress for the getting-started checklist and welcome tour."""
from .extensions import db
from .models import UserProgress

FLAGS = {"tour_seen", "checklist_dismissed", "generated", "exported"}


def _record(user) -> UserProgress:
    if user.progress is None:
        user.progress = UserProgress(user_id=user.id, tour_seen=False, checklist_dismissed=False,
                                     generated=False, exported=False)
    return user.progress


def mark(user, flag: str, value: bool = True) -> None:
    """Set one flag (no-op for anonymous users or if already set)."""
    if flag not in FLAGS or not getattr(user, "is_authenticated", False):
        return
    record = _record(user)
    if getattr(record, flag) != value:
        setattr(record, flag, value)
        db.session.commit()


def progress_dict(user) -> dict:
    record = user.progress
    return {
        "tour_seen": bool(record and record.tour_seen),
        "checklist_dismissed": bool(record and record.checklist_dismissed),
        "generated": bool(record and record.generated),
        "saved": user.bookmarks.count() > 0,
        "developed": user.outlines.count() > 0,
        "exported": bool(record and record.exported),
    }
