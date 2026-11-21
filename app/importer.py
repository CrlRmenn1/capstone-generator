"""Imports capstone titles from CSV into the database."""
import csv

from .extensions import db
from .models import Title

FIELDS = ("title", "abstract", "program", "area", "domain", "tags", "tech_stack", "year", "source")


def import_titles_from_csv(path: str) -> int:
    """Insert titles from ``path``, skipping ones already present. Returns the number added."""
    existing = {t for (t,) in db.session.query(Title.title).all()}
    added = 0
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            title = (row.get("title") or "").strip()
            if not title or title in existing:
                continue
            data = {f: (row.get(f) or "").strip() for f in FIELDS}
            data["year"] = int(data["year"]) if data["year"].isdigit() else None
            db.session.add(Title(**data))
            existing.add(title)
            added += 1
    db.session.commit()
    return added
