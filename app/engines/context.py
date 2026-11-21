"""Resolve any title (generated, from the dataset, or typed by the student) into a full
Chapter 1 context: the knowledge-base entries the outline will be written from."""
from ..knowledge_base import DIFFICULTY_LEVELS, KnowledgeBase
from ..textutils import normalize

_STOP = {"system", "based", "using", "with", "for", "the", "and", "development", "design",
         "implementation", "application", "app", "of", "a", "an", "in", "on", "through", "to"}


def _tokens(text: str) -> set[str]:
    return {w for w in normalize(text).split() if len(w) > 2 and w not in _STOP}


def _best(options: list, text_of, title_tokens: set[str]):
    """Option whose text overlaps most with the title (first option on ties)."""
    best, best_score = options[0], -1
    for opt in options:
        score = len(_tokens(text_of(opt)) & title_tokens)
        if score > best_score:
            best, best_score = opt, score
    return best


def _find(items: list[dict], key: str, value: str) -> dict | None:
    return next((i for i in items if i.get(key) == value), None)


def resolve_context(kb: KnowledgeBase, title: str, context: dict | None = None,
                    system_name: str = "") -> dict:
    """Fill in a complete outline context. Known keys in ``context`` are kept; missing ones
    are inferred from the title text. ``context`` must name at least a domain and an area."""
    ctx = dict(context or {})
    domain_key = ctx.get("domain")
    area_key = ctx.get("area") or (ctx.get("areas") or [None])[0]
    if domain_key not in kb.domains:
        raise ValueError("A valid domain is required to develop this title.")
    if area_key not in kb.technologies:
        raise ValueError("A valid area of interest is required to develop this title.")
    domain, tech = kb.domain(domain_key), kb.technology(area_key)
    words = _tokens(title)

    problem = _find(domain["problems"], "subject", ctx.get("problem")) or _best(
        domain["problems"], lambda p: f"{p['subject']} {p['problem']} {p['module']}", words)

    difficulty = ctx.get("difficulty") if ctx.get("difficulty") in DIFFICULTY_LEVELS else "intermediate"
    technique = _find(tech["techniques"], "name", ctx.get("technique"))
    if technique is None:
        # Prefer a technique named in the title; otherwise one at the chosen difficulty.
        named = [t for t in tech["techniques"] if _tokens(t["name"]) and _tokens(t["name"]) <= words]
        at_level = [t for t in tech["techniques"] if t["difficulty"] == difficulty] or tech["techniques"]
        technique = named[0] if named else _best(at_level, lambda t: t["name"], words)

    feature = ctx.get("feature") or _best(tech["features"], lambda f: f, words)
    beneficiaries = problem.get("beneficiaries") or domain["beneficiaries"]

    if not system_name and ":" in title:
        head = title.split(":", 1)[0].strip()
        if 0 < len(head.split()) <= 3:
            system_name = head
    if not system_name:
        system_name = domain["name_roots"][0] + tech["name_suffixes"][0]

    secondary = [b for b in beneficiaries if b != ctx.get("beneficiary")]
    return {
        "group": ctx.get("group") or tech["pattern_group"],
        "domain": domain_key,
        "area": area_key,
        "difficulty": technique["difficulty"],
        "problem": problem["subject"],
        "technique": technique["name"],
        "feature": feature,
        "platform": ctx.get("platform") or tech["platforms"][0],
        "artifact": ctx.get("artifact") or tech["artifacts"][0],
        "beneficiary": ctx.get("beneficiary") or beneficiaries[0],
        "secondary_beneficiary": ctx.get("secondary_beneficiary") or (secondary[0] if secondary else "administrators"),
        "setting": ctx.get("setting") or domain["settings"][0],
        "topic": ctx.get("topic") or _best(domain["learning_topics"], lambda t: t, words),
        "system_name": system_name,
    }


def expand_context(kb: KnowledgeBase, ctx: dict) -> dict:
    """Look up the full knowledge-base records for a resolved context."""
    domain, tech = kb.domain(ctx["domain"]), kb.technology(ctx["area"])
    return {
        **ctx,
        "domain_rec": domain,
        "tech_rec": tech,
        "problem_rec": _find(domain["problems"], "subject", ctx["problem"]) or domain["problems"][0],
        "technique_rec": _find(tech["techniques"], "name", ctx["technique"]) or tech["techniques"][0],
    }
