"""Shared types for title engines. Routes depend only on these, never on a concrete engine."""
import zlib
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field

from ..knowledge_base import DIFFICULTY_LEVELS, PROGRAMS, KnowledgeBase


def _split_list(raw: str) -> list[str]:
    return [p.strip() for p in (raw or "").replace(";", ",").split(",") if p.strip()]


@dataclass
class Preferences:
    program: str
    interests: list[str]
    domain: str
    difficulty: str
    skills: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: dict, kb: KnowledgeBase) -> tuple["Preferences", list[str]]:
        """Build preferences from a JSON body. Lists may be arrays or comma-separated strings."""
        data = data or {}

        def as_text(value):
            return ", ".join(value) if isinstance(value, list) else str(value or "")

        interests = data.get("interests") or []
        if isinstance(interests, str):
            interests = [interests]
        return cls._build(
            program=str(data.get("program") or "BSIT"),
            interests=[str(i) for i in interests],
            domain=str(data.get("domain") or ""),
            difficulty=str(data.get("difficulty") or "intermediate"),
            skills=as_text(data.get("skills")),
            keywords=as_text(data.get("keywords")),
            kb=kb,
        )

    @classmethod
    def _build(cls, program, interests, domain, difficulty, skills, keywords, kb):
        errors = []
        if program not in PROGRAMS:
            errors.append("Please choose a valid program.")
        interests = [i for i in dict.fromkeys(interests) if i]
        if not interests:
            errors.append("Pick at least one area of interest.")
        elif any(i not in kb.technologies for i in interests):
            errors.append("One of the selected areas of interest is not recognized.")
        if domain not in kb.domains:
            errors.append("Please choose a target domain.")
        if difficulty not in DIFFICULTY_LEVELS:
            errors.append("Please choose a valid difficulty.")
        prefs = cls(
            program=program,
            interests=interests,
            domain=domain,
            difficulty=difficulty,
            skills=_split_list(skills)[:15],
            keywords=_split_list(keywords)[:15],
        )
        return prefs, errors

    def to_dict(self) -> dict:
        return asdict(self)

    def query_text(self, kb: KnowledgeBase) -> str:
        """The preferences as one text query for content-based matching."""
        parts = []
        for key in self.interests:
            tech = kb.technology(key)
            parts += [tech["label"], *tech["keywords"]]
        domain = kb.domain(self.domain)
        # The domain is the anchor of a capstone, so it outweighs the technology keywords.
        parts += [domain["label"], *domain["keywords"]] * 2
        # Free-text keywords are what the student cares about most, so they count twice.
        parts += self.keywords * 2 + self.skills
        return " ".join(parts)

    def default_seed(self) -> int:
        """Stable seed so the same preferences give the same first results."""
        canonical = "|".join([self.program, ",".join(sorted(self.interests)), self.domain,
                              self.difficulty, ",".join(self.skills), ",".join(self.keywords)])
        return zlib.crc32(canonical.lower().encode("utf-8"))


@dataclass
class GeneratedTitle:
    title: str
    system_name: str
    abstract: str
    objectives: list[str]
    stack: list[str]
    skill_matches: list[str]  # team skills found in the stack
    matched_stack: list[str]  # stack items that use one of the team's skills
    difficulty: str
    area: str
    source: str  # "template" or "ai"
    relevance: float = 0.0
    novelty: float = 0.0
    score: float = 0.0
    closest_existing: str = ""
    # Knowledge-base keys behind this title (domain, problem, technique, ...), used to build Chapter 1.
    context: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class EngineError(RuntimeError):
    """Raised when an engine cannot produce a result (e.g. the AI provider rejected the key)."""

    def __init__(self, message: str, code: str = "engine_error"):
        super().__init__(message)
        self.code = code


class TitleEngine(ABC):
    source: str = ""

    @abstractmethod
    def generate_titles(self, prefs: Preferences, count: int = 8, seed: int | None = None) -> list[GeneratedTitle]:
        ...


# Chapter 1 sections in the order they appear in the manuscript.
OUTLINE_SECTIONS = [
    ("background", "Background of the Study"),
    ("problem", "Statement of the Problem"),
    ("objectives", "Objectives of the Study"),
    ("significance", "Significance of the Study"),
    ("scope", "Scope and Limitations"),
    ("terms", "Definition of Terms"),
    ("overview", "Overview of the Proposed System"),
]
SECTION_KEYS = [k for k, _ in OUTLINE_SECTIONS]


class OutlineEngine(ABC):
    """Writes Chapter 1 sections. Content uses a small Markdown subset:
    paragraphs separated by blank lines, "- " bullets, "1. " numbered items, and **bold**."""

    source: str = ""

    @abstractmethod
    def write_section(self, key: str, title: str, ctx: dict, seed: int = 0,
                      current: dict[str, str] | None = None) -> str:
        """Write one section. ``current`` holds the other sections' text, so a regenerated
        section can stay consistent with them (e.g. objectives matching the problems)."""

    def write_all(self, title: str, ctx: dict, seed: int = 0) -> dict[str, str]:
        written: dict[str, str] = {}
        for key in SECTION_KEYS:
            written[key] = self.write_section(key, title, ctx, seed, current=written)
        return written
