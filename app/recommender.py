"""Content-based filtering over the capstone title dataset (TF-IDF + cosine similarity)."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Metadata boosts added to the text similarity when ranking (the displayed % stays the raw similarity).
SAME_DOMAIN_BOOST = 0.15
SAME_AREA_BOOST = 0.05
SAME_PROGRAM_BOOST = 0.03


class Recommender:
    def __init__(self, items: list[dict]):
        """``items`` are dicts with at least ``title``; optional abstract, tags, area, domain, program."""
        self.items = items
        # Full-document index (title + abstract + tags) for matching preferences.
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        self.matrix = self.vectorizer.fit_transform([self._document(i) for i in items]) if items else None
        # Title-only index for duplicate/novelty checks, so a copied title scores ~1.0.
        self.title_vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        self.title_matrix = (self.title_vectorizer.fit_transform([i.get("title", "") for i in items])
                             if items else None)

    @staticmethod
    def _document(item: dict) -> str:
        # The title is repeated so it weighs more than the abstract and tags.
        parts = [item.get("title", "")] * 2 + [
            item.get("abstract", ""),
            item.get("tags", ""),
            item.get("tech_stack", ""),
        ]
        return " ".join(p for p in parts if p)

    def recommend(self, query: str, top_n: int = 10, program: str | None = None,
                  domain: str | None = None, areas: list[str] | None = None,
                  min_score: float = 0.01) -> list[dict]:
        """Return the ``top_n`` most similar dataset titles with their similarity scores.

        Ranking = TF-IDF cosine similarity + small boosts when the title's domain, area,
        or program matches the student's choices.
        """
        if self.matrix is None or not query.strip():
            return []
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix).ravel()
        areas = set(areas or [])
        ranked = []
        for item, score in zip(self.items, scores):
            if score < min_score:
                continue
            rank_score = (score
                          + (SAME_DOMAIN_BOOST if domain and item.get("domain") == domain else 0)
                          + (SAME_AREA_BOOST if item.get("area") in areas else 0)
                          + (SAME_PROGRAM_BOOST if program and item.get("program") == program else 0))
            ranked.append((rank_score, float(score), item))
        ranked.sort(key=lambda r: r[0], reverse=True)
        return [{**item, "similarity": score} for _, score, item in ranked[:top_n]]

    def closest_titles(self, titles: list[str]) -> list[tuple[str, float]]:
        """For each title, the most similar existing title and its title-to-title similarity."""
        if self.title_matrix is None or not titles:
            return [("", 0.0)] * len(titles)
        sims = cosine_similarity(self.title_vectorizer.transform(titles), self.title_matrix)
        return [(self.items[row.argmax()]["title"], float(row.max())) for row in sims]

    def max_similarity(self, titles: list[str]) -> list[float]:
        """For each title, similarity to its closest existing title (used for novelty checks)."""
        return [sim for _, sim in self.closest_titles(titles)]
