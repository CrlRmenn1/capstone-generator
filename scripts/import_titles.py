"""Import capstone titles from a CSV into the database.

Usage:  python scripts/import_titles.py [path/to/titles.csv]
CSV columns: title, abstract, program, area, domain, tags, tech_stack, year, source
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app import create_app, rebuild_recommender  # noqa: E402
from app.importer import import_titles_from_csv  # noqa: E402


def main() -> None:
    app = create_app({"AUTO_SEED": False})
    path = sys.argv[1] if len(sys.argv) > 1 else app.config["SEED_TITLES_CSV"]
    with app.app_context():
        added = import_titles_from_csv(path)
        rebuild_recommender(app)
    print(f"Imported {added} new title(s) from {path}")


if __name__ == "__main__":
    main()
