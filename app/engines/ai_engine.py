"""AI engines (bring-your-own-key). They return the same shapes as the template engines,
so the rest of the app treats both alike.

Titles use retrieval-augmented generation: the closest existing titles from the dataset are
put in the prompt so the model avoids repeating them and stays grounded in realistic scope.
"""
import json
import threading
from collections import OrderedDict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..ai.providers import ProviderError, generate_json
from ..knowledge_base import DIFFICULTY_LEVELS, PROGRAMS, KnowledgeBase
from ..recommender import Recommender
from ..textutils import normalize
from .base import OUTLINE_SECTIONS, SECTION_KEYS, EngineError, GeneratedTitle, OutlineEngine, Preferences, TitleEngine
from .template_engine import MAX_DATASET_SIMILARITY, NOVELTY_WEIGHT, RELEVANCE_WEIGHT

# Identical requests (same user, preferences, seed, model) reuse the earlier answer
# instead of spending the student's quota again.
_CACHE: "OrderedDict[str, object]" = OrderedDict()
_CACHE_SIZE = 256
_cache_lock = threading.Lock()


def _cached(key: str, produce):
    with _cache_lock:
        if key in _CACHE:
            _CACHE.move_to_end(key)
            return _CACHE[key]
    value = produce()
    with _cache_lock:
        _CACHE[key] = value
        while len(_CACHE) > _CACHE_SIZE:
            _CACHE.popitem(last=False)
    return value


def _call(cfg: dict, system: str, prompt: str, schema: dict) -> dict:
    try:
        return generate_json(cfg["provider"], cfg["api_key"], cfg["model"], system, prompt, schema)
    except ProviderError as exc:
        raise EngineError(str(exc), exc.code) from exc


TITLE_SYSTEM = (
    "You are an experienced capstone adviser for Philippine IT and Computer Science programs. "
    "You propose capstone project titles that are specific, feasible for a student team within "
    "one academic year, and defensible before a panel. Titles follow academic conventions "
    "(e.g. 'SystemName: A Web-Based ... for ...'). Never invent statistics, organizations, or citations."
)


class AITitleEngine(TitleEngine):
    source = "ai"

    def __init__(self, kb: KnowledgeBase, recommender: Recommender, cfg: dict, user_id: int):
        self.kb, self.recommender, self.cfg, self.user_id = kb, recommender, cfg, user_id

    def _schema(self, prefs: Preferences, count: int) -> dict:
        item = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "system_name": {"type": "string"},
                "abstract": {"type": "string"},
                "objectives": {"type": "array", "items": {"type": "string"}},
                "stack": {"type": "array", "items": {"type": "string"}},
                "difficulty": {"type": "string", "enum": DIFFICULTY_LEVELS},
                "area": {"type": "string", "enum": prefs.interests},
            },
            "required": ["title", "system_name", "abstract", "objectives", "stack", "difficulty", "area"],
            "additionalProperties": False,
        }
        return {"type": "object", "properties": {"titles": {"type": "array", "items": item}},
                "required": ["titles"], "additionalProperties": False}

    def _prompt(self, prefs: Preferences, count: int, seed: int, existing: list[dict]) -> str:
        domain = self.kb.domain(prefs.domain)
        areas = "\n".join(f"- {k}: {self.kb.technology_label(k)}" for k in prefs.interests)
        problems = "\n".join(f"- {p['subject']}: {p['problem']}" for p in domain["problems"])
        nearby = "\n".join(f"- {t['title']}" for t in existing) or "- (none)"
        return f"""Propose {count} new capstone titles for this student team.

Program: {prefs.program} ({PROGRAMS[prefs.program]})
Target domain: {domain['label']}
Areas of interest (use these keys for "area"):
{areas}
Preferred difficulty: {prefs.difficulty}
Team skills: {', '.join(prefs.skills) or 'not specified'}
Keywords to consider: {', '.join(prefs.keywords) or 'none'}

Typical problems in this domain (for inspiration, not a limit):
{problems}

Existing capstones that are already done. Do NOT repeat or closely paraphrase these:
{nearby}

Requirements:
- Each title must be clearly different from the others and from the existing capstones.
- Most titles should match the preferred difficulty; at most two may be one level easier.
- "system_name" is a short, memorable name (one or two words) that appears in the title when it fits.
- "abstract" is 2 to 3 sentences: the users and setting, the problem, and how the system solves it.
- "objectives" has exactly 4 items starting with "To ...": the core module, the main technique,
  one supporting feature, and an evaluation item (ISO/IEC 25010 for software systems).
- "stack" lists 3 to 6 realistic tools; prefer the team's skills when they fit.
- Variation number {seed}: if asked again with a different number, give different ideas."""

    def generate_titles(self, prefs: Preferences, count: int = 8, seed: int | None = None) -> list[GeneratedTitle]:
        seed = seed or 0
        query = prefs.query_text(self.kb)
        existing = self.recommender.recommend(query, top_n=8, domain=prefs.domain, areas=prefs.interests)
        cache_key = json.dumps([self.user_id, self.cfg["provider"], self.cfg["model"], prefs.to_dict(),
                                count, seed], sort_keys=True)
        data = _cached(cache_key, lambda: _call(self.cfg, TITLE_SYSTEM,
                                                self._prompt(prefs, count, seed, existing),
                                                self._schema(prefs, count)))
        return self._to_results(prefs, data.get("titles") or [], query, count)

    def _to_results(self, prefs: Preferences, raw: list, query: str, count: int) -> list[GeneratedTitle]:
        items, seen = [], set()
        for r in raw:
            if not isinstance(r, dict) or not str(r.get("title", "")).strip():
                continue
            key = normalize(r["title"])
            if key in seen:
                continue
            seen.add(key)
            items.append(r)
        if not items:
            raise EngineError("The AI returned no usable titles. Try again or use default mode.", "bad_response")

        titles = [str(r["title"]).strip()[:300] for r in items]
        docs = [f"{t} {r.get('abstract', '')}" for t, r in zip(titles, items)]
        local = TfidfVectorizer(stop_words="english", sublinear_tf=True).fit(docs + [query])
        relevance = cosine_similarity(local.transform(docs), local.transform([query])).ravel()
        top = relevance.max() or 1.0
        closest = self.recommender.closest_titles(titles)
        skills = [s.lower() for s in prefs.skills]

        results = []
        for title, r, rel, (near, sim) in zip(titles, items, relevance, closest):
            if sim > MAX_DATASET_SIMILARITY:
                continue  # the model repeated an existing title despite instructions
            area = r.get("area") if r.get("area") in prefs.interests else prefs.interests[0]
            difficulty = r.get("difficulty") if r.get("difficulty") in DIFFICULTY_LEVELS else prefs.difficulty
            stack = [str(s) for s in (r.get("stack") or [])][:8]
            rel_norm, novelty = float(rel / top), 1.0 - sim
            results.append(GeneratedTitle(
                title=title,
                system_name=str(r.get("system_name") or "").strip()[:60],
                abstract=str(r.get("abstract") or "").strip(),
                objectives=[str(o) for o in (r.get("objectives") or [])][:6],
                stack=stack,
                skill_matches=[s for s in prefs.skills if any(s.lower() in x.lower() for x in stack)],
                matched_stack=[x for x in stack if any(s in x.lower() for s in skills)],
                difficulty=difficulty,
                area=area,
                source=self.source,
                relevance=round(rel_norm, 3),
                novelty=round(novelty, 3),
                score=round(RELEVANCE_WEIGHT * rel_norm + NOVELTY_WEIGHT * novelty, 3),
                closest_existing=near,
                context={"domain": prefs.domain, "area": area, "areas": list(prefs.interests),
                         "difficulty": difficulty},
            ))
        results.sort(key=lambda g: g.score, reverse=True)
        return results[:count]


# ------------------------------------------------------------------------- outline
OUTLINE_SYSTEM = (
    "You help Philippine IT/CS capstone students draft Chapter 1 (Introduction) of their proposal "
    "for the outline defense. Write in clear, formal academic English suitable for a student "
    "manuscript. Never invent statistics, studies, organizations, laws, or citations: wherever a "
    "claim needs evidence, write the placeholder [cite source] so the students add a real reference. "
    "Format: plain paragraphs separated by blank lines, '- ' for bullet items, '1. ' for numbered "
    "items, and **bold** for terms. No headings, no other Markdown."
)

SECTION_GUIDE = {
    "background": "3 to 4 paragraphs: the domain context and current situation, the problem and its "
                  "effects, how the chosen technology can help (with [cite source] placeholders), and "
                  "a closing paragraph introducing the proposed system by name.",
    "problem": "One general problem sentence, then 'Specifically, it seeks to answer the following "
               "questions:' and exactly 4 numbered questions: the core module, the main technique, "
               "a supporting feature, and the evaluation (ISO/IEC 25010 for software systems).",
    "objectives": "One general objective sentence ('The general objective of this study is to ...'), then "
                  "'Specifically, the study aims to:' and exactly 4 numbered objectives that correspond "
                  "one-to-one, in order, with the specific problems.",
    "significance": "A short intro sentence, then 4 to 6 bullets of the form '**Beneficiary.** how they "
                    "benefit', ending with the researchers and future researchers.",
    "scope": "A paragraph on what the study covers, bullets for each main module ('**Module** – what it "
             "does'), a sentence on tools and evaluation, then 'The study has the following "
             "limitations:' and 3 to 4 bullets.",
    "terms": "One intro sentence, then 5 to 7 bullets '**Term** – refers to ...' with operational "
             "definitions as used in this study.",
    "overview": "Three parts, each starting with a bold label line: **User roles** (bullets), "
                "**Main modules** (bullets), **How it works** (one paragraph describing the flow).",
}

_SECTION_SCHEMA = {"type": "object", "properties": {"content": {"type": "string"}},
                   "required": ["content"], "additionalProperties": False}
_ALL_SCHEMA = {"type": "object", "properties": {k: {"type": "string"} for k in SECTION_KEYS},
               "required": SECTION_KEYS, "additionalProperties": False}


class AIOutlineEngine(OutlineEngine):
    source = "ai"

    def __init__(self, kb: KnowledgeBase, cfg: dict):
        self.kb, self.cfg = kb, cfg

    def _project(self, title: str, ctx: dict) -> str:
        domain, tech = self.kb.domain(ctx["domain"]), self.kb.technology(ctx["area"])
        return (f"Capstone title: {title}\nSystem name: {ctx.get('system_name', '')}\n"
                f"Domain: {domain['label']}\nTechnology area: {tech['label']}\n"
                f"Main problem: {ctx.get('problem', '')}\nKey technique: {ctx.get('technique', '')}\n"
                f"Supporting feature: {ctx.get('feature', '')}\nPrimary users: {ctx.get('beneficiary', '')}\n"
                f"Secondary users: {ctx.get('secondary_beneficiary', '')}\nSetting: {ctx.get('setting', '')}\n"
                f"Difficulty: {ctx.get('difficulty', '')}\n"
                "(Treat the problem, technique, and feature as suggestions; follow the title if it differs.)")

    def write_section(self, key, title, ctx, seed=0, current=None) -> str:
        if key not in SECTION_KEYS:
            raise ValueError(f"Unknown section '{key}'")
        heading = dict(OUTLINE_SECTIONS)[key]
        related = ""
        current = current or {}
        if key == "objectives" and current.get("problem"):
            related = f"\n\nThe current Statement of the Problem (objectives must match it):\n{current['problem']}"
        elif key == "problem" and current.get("objectives"):
            related = f"\n\nThe current Objectives (problems must match them):\n{current['objectives']}"
        prompt = (f"{self._project(title, ctx)}\n\nWrite the section \"{heading}\".\n"
                  f"{SECTION_GUIDE[key]}{related}\n\nVersion {seed}: vary the wording from earlier versions.")
        data = _call(self.cfg, OUTLINE_SYSTEM, prompt, _SECTION_SCHEMA)
        content = str(data.get("content") or "").strip()
        if not content:
            raise EngineError("The AI returned an empty section. Try again.", "bad_response")
        return content

    def write_all(self, title, ctx, seed=0) -> dict[str, str]:
        guide = "\n".join(f"- {k} ({dict(OUTLINE_SECTIONS)[k]}): {SECTION_GUIDE[k]}" for k in SECTION_KEYS)
        prompt = (f"{self._project(title, ctx)}\n\nWrite all Chapter 1 sections. Return one field per "
                  f"section key:\n{guide}\n\nThe objectives must correspond one-to-one with the specific "
                  f"problems.")
        data = _call(self.cfg, OUTLINE_SYSTEM, prompt, _ALL_SCHEMA)
        written = {k: str(data.get(k) or "").strip() for k in SECTION_KEYS}
        if not all(written.values()):
            raise EngineError("The AI left some sections empty. Try again or use default mode.", "bad_response")
        return written
