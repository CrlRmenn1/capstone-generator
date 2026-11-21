"""Default title engine: works fully offline using the knowledge base and title patterns.

Pipeline: build many candidate titles from patterns -> de-duplicate -> score each one on
relevance (match to the preferences) and novelty (distance from existing dataset titles)
-> drop near-duplicates of existing titles -> pick a diverse top N.
"""
import random
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..knowledge_base import DIFFICULTY_LEVELS, KnowledgeBase
from ..recommender import Recommender
from ..textutils import fix_articles, normalize, smart_title
from .base import GeneratedTitle, Preferences, TitleEngine

RELEVANCE_WEIGHT = 0.6
NOVELTY_WEIGHT = 0.4
# Subtracted per level a technique sits below the requested difficulty.
DIFFICULTY_GAP_PENALTY = 0.15
# Titles this similar (title-to-title) to an existing one are near-duplicates and dropped.
MAX_DATASET_SIMILARITY = 0.75
# Base diversity limit per pattern / subject / technique; raised when the pool of options is small.
MAX_PER_GROUP = 2

_SYNONYMS = {"application": "app", "android": "mobile", "smartphone": "mobile"}
_IGNORED = {"based", "real", "time", "data", "system"}


def _words(text: str) -> set[str]:
    """Meaningful words for overlap checks, with a few synonyms folded together."""
    words = {_SYNONYMS.get(w, w) for w in normalize(text).split() if len(w) >= 3}
    return words - _IGNORED


@dataclass
class _Candidate:
    title: str
    system_name: str
    pattern: str
    group: str
    area_key: str
    technique: dict
    problem: dict
    feature: str
    platform: str
    artifact: str
    beneficiary: str
    setting: str
    topic: str


class TemplateEngine(TitleEngine):
    source = "template"

    def __init__(self, kb: KnowledgeBase, recommender: Recommender,
                 max_dataset_similarity: float = MAX_DATASET_SIMILARITY):
        self.kb = kb
        self.recommender = recommender
        self.max_dataset_similarity = max_dataset_similarity

    # ------------------------------------------------------------------ public API
    def generate_titles(self, prefs: Preferences, count: int = 8, seed: int | None = None) -> list[GeneratedTitle]:
        rng = random.Random(seed)
        domain = self.kb.domain(prefs.domain)
        areas = [(key, self.kb.technology(key)) for key in prefs.interests]

        pool: dict[str, _Candidate] = {}
        target = count * 6
        for _ in range(count * 60):
            if len(pool) >= target:
                break
            cand = self._build_candidate(prefs, domain, areas, rng)
            pool.setdefault(normalize(cand.title), cand)

        candidates = list(pool.values())
        scored = self._score(prefs, candidates)
        selected = self._select(scored, count)
        return [self._to_result(prefs, domain, areas, *item) for item in selected]

    # ------------------------------------------------------------- candidate building
    def _pick_technique(self, tech: dict, difficulty: str, rng: random.Random) -> dict:
        rank = DIFFICULTY_LEVELS.index(difficulty)
        exact = [t for t in tech["techniques"] if t["difficulty"] == difficulty]
        easier = [t for t in tech["techniques"] if DIFFICULTY_LEVELS.index(t["difficulty"]) < rank]
        pool = exact or easier
        # Mostly match the chosen level; sometimes offer an easier option for variety.
        if exact and easier and rng.random() < 0.25:
            pool = easier
        return rng.choice(pool)

    def _build_candidate(self, prefs, domain, areas, rng) -> _Candidate:
        area_key, tech = rng.choice(areas)
        technique = self._pick_technique(tech, prefs.difficulty, rng)

        platform = rng.choice(tech["platforms"])
        artifact = rng.choice(tech["artifacts"])
        # The feature may come from any selected area, giving cross-area titles (e.g. IoT + mobile),
        # but it must not repeat the technique or what the system already is ("an app ... with an app").
        taken = _words(f"{technique['name']} {platform} {artifact}")
        feature = ""
        for _ in range(6):
            feature = rng.choice(rng.choice(areas)[1]["features"])
            if not _words(feature) & taken:
                break

        group = tech["pattern_group"]
        pattern = rng.choice(self.kb.patterns[group])
        problem = rng.choice(domain["problems"])
        system_name = rng.choice(domain["name_roots"]) + rng.choice(tech["name_suffixes"])
        # System titles use the problem's own users; learning titles use the domain's learners.
        beneficiaries = (problem.get("beneficiaries") if group == "system" else None) or domain["beneficiaries"]
        slots = {
            "system": system_name,
            "platform": platform,
            "subject": problem["subject"],
            "artifact": artifact,
            "technique": technique["name"],
            "feature": feature,
            "beneficiary": rng.choice(beneficiaries),
            "setting": rng.choice(domain["settings"]),
            "topic": rng.choice(domain["learning_topics"]),
        }
        title = fix_articles(smart_title(pattern.format(**slots)))
        return _Candidate(title=title, system_name=system_name, pattern=pattern, group=group,
                          area_key=area_key, technique=technique, problem=problem, feature=feature,
                          platform=slots["platform"], artifact=slots["artifact"],
                          beneficiary=slots["beneficiary"], setting=slots["setting"], topic=slots["topic"])

    # ------------------------------------------------------------------- scoring
    @staticmethod
    def _candidate_document(c: _Candidate) -> str:
        return " ".join([c.title, c.technique["name"], c.technique["purpose"], c.feature,
                         c.problem["subject"], c.problem["problem"], c.topic if c.group == "simulation" else ""])

    def _score(self, prefs: Preferences, candidates: list[_Candidate]) -> list[tuple]:
        if not candidates:
            return []
        query = prefs.query_text(self.kb)
        docs = [self._candidate_document(c) for c in candidates]
        # Relevance uses a vectorizer fitted on the candidates + query so any keyword counts,
        # even words that never appear in the dataset.
        local = TfidfVectorizer(stop_words="english", sublinear_tf=True).fit(docs + [query])
        relevance = cosine_similarity(local.transform(docs), local.transform([query])).ravel()
        top_relevance = relevance.max() or 1.0

        closest = self.recommender.closest_titles([c.title for c in candidates])

        wanted_rank = DIFFICULTY_LEVELS.index(prefs.difficulty)
        scored = []
        for cand, rel, (near, sim) in zip(candidates, relevance, closest):
            rel_norm = float(rel / top_relevance)
            novelty = 1.0 - float(sim)
            gap = wanted_rank - DIFFICULTY_LEVELS.index(cand.technique["difficulty"])
            score = RELEVANCE_WEIGHT * rel_norm + NOVELTY_WEIGHT * novelty - DIFFICULTY_GAP_PENALTY * gap
            score = max(score, 0.0)
            scored.append((cand, rel_norm, novelty, score, near, float(sim)))
        scored.sort(key=lambda s: s[3], reverse=True)
        return scored

    # ------------------------------------------------------------------ selection
    @staticmethod
    def _diversity_keys(c: _Candidate) -> tuple[str, str, str]:
        subject = c.topic if c.group == "simulation" else c.problem["subject"]
        return c.pattern, subject, c.technique["name"]

    def _select(self, scored: list[tuple], count: int) -> list[tuple]:
        allowed = [s for s in scored if s[5] <= self.max_dataset_similarity]
        # Limit how often a pattern/subject/technique repeats. When there are only a few
        # distinct options (e.g. 2 beginner game techniques), allow proportionally more.
        limits = []
        for i in range(3):
            distinct = len({self._diversity_keys(s[0])[i] for s in allowed}) or 1
            limits.append(max(MAX_PER_GROUP, -(-count // distinct)))

        selected, names, titles = [], set(), set()
        counts = [{}, {}, {}]
        # Pass 1: diversity limits. Pass 2: only require unique names and titles.
        for strict in (True, False):
            for item in allowed:
                if len(selected) >= count:
                    break
                c = item[0]
                if c.system_name in names or c.title in titles:
                    continue
                keys = self._diversity_keys(c)
                if strict and any(counts[i].get(k, 0) >= limits[i] for i, k in enumerate(keys)):
                    continue
                selected.append(item)
                names.add(c.system_name)
                titles.add(c.title)
                for i, k in enumerate(keys):
                    counts[i][k] = counts[i].get(k, 0) + 1
        selected.sort(key=lambda s: s[3], reverse=True)
        return selected

    # --------------------------------------------------------------------- output
    def _stack_for(self, prefs: Preferences, areas, primary_key: str) -> list[str]:
        ordered = sorted(areas, key=lambda a: a[0] != primary_key)  # primary area's stack first
        stack = []
        for _, tech in ordered:
            for item in tech["stack"][prefs.difficulty]:
                if item not in stack:
                    stack.append(item)
        return stack[:8]

    def _to_result(self, prefs, domain, areas, cand: _Candidate, relevance, novelty, score,
                   closest, _sim) -> GeneratedTitle:
        tech = cand.technique
        p = cand.problem
        if cand.group == "simulation":
            abstract = (
                f"{cand.system_name} is a {cand.platform} {cand.artifact} that helps {cand.beneficiary} "
                f"learn about {cand.topic}. It uses {tech['name']} for {tech['purpose']} and includes "
                f"{cand.feature} to keep learners engaged. The study aims to make learning {cand.topic} "
                f"more interactive and measurable for {cand.beneficiary} in {cand.setting}."
            )
            objectives = [
                f"To design and develop a {cand.platform} {cand.artifact} on {cand.topic}.",
                f"To apply {tech['name']} for {tech['purpose']}.",
                f"To include {cand.feature} to support learner engagement.",
                f"To evaluate the learning effectiveness and usability of the {cand.artifact} with target users.",
            ]
        else:
            abstract = (
                f"{cand.system_name} is a {cand.platform} {p['subject']} {cand.artifact} designed for "
                f"{cand.beneficiary} in {cand.setting}. It addresses {p['problem']} by applying "
                f"{tech['name']} for {tech['purpose']}, and it includes {cand.feature}. "
                f"The study aims to {p['goal']}."
            )
            objectives = [
                f"To design and develop a {p['module']} module that {p['module_desc']}.",
                f"To apply {tech['name']} for {tech['purpose']}.",
                f"To integrate {cand.feature} into the system.",
                "To evaluate the system's quality using the ISO/IEC 25010 software quality model.",
            ]
        stack = self._stack_for(prefs, areas, cand.area_key)
        skills = [s.lower() for s in prefs.skills]
        matched_stack = [item for item in stack if any(s in item.lower() for s in skills)]
        skill_matches = [s for s in prefs.skills if any(s.lower() in item.lower() for item in stack)]
        return GeneratedTitle(
            title=cand.title,
            system_name=cand.system_name,
            abstract=fix_articles(abstract),
            objectives=[fix_articles(o) for o in objectives],
            stack=stack,
            skill_matches=skill_matches,
            matched_stack=matched_stack,
            difficulty=tech["difficulty"],
            area=cand.area_key,
            source=self.source,
            relevance=round(relevance, 3),
            novelty=round(novelty, 3),
            score=round(score, 3),
            closest_existing=closest,
            context={
                "group": cand.group,
                "domain": prefs.domain,
                "area": cand.area_key,
                "areas": list(prefs.interests),
                "difficulty": prefs.difficulty,
                "problem": p["subject"],
                "technique": tech["name"],
                "feature": cand.feature,
                "platform": cand.platform,
                "artifact": cand.artifact,
                "beneficiary": cand.beneficiary,
                "setting": cand.setting,
                "topic": cand.topic,
            },
        )
