"""Loads the curated knowledge base used by the default (no-API) engine."""
import json
import os
from dataclasses import dataclass

DIFFICULTY_LEVELS = ["beginner", "intermediate", "advanced"]

PROGRAMS = {
    "BSIT": "Information Technology",
    "BSCS": "Computer Science",
    "BSIS": "Information Systems",
}

_REQUIRED_TECH_KEYS = {"label", "limitation", "keywords", "pattern_group", "platforms", "artifacts",
                       "name_suffixes", "techniques", "features", "stack"}
_REQUIRED_DOMAIN_KEYS = {"label", "keywords", "beneficiaries", "settings", "name_roots",
                         "learning_topics", "problems"}
_REQUIRED_PROBLEM_KEYS = {"subject", "problem", "goal", "module", "module_desc"}


class KnowledgeBaseError(ValueError):
    pass


@dataclass
class KnowledgeBase:
    technologies: dict
    domains: dict
    patterns: dict

    @classmethod
    def load(cls, directory: str) -> "KnowledgeBase":
        def read(name):
            with open(os.path.join(directory, name), encoding="utf-8") as fh:
                return json.load(fh)

        kb = cls(
            technologies=read("technologies.json"),
            domains=read("domains.json"),
            patterns=read("title_patterns.json"),
        )
        kb.validate()
        return kb

    def validate(self) -> None:
        """Fail fast on a malformed knowledge base instead of at generation time."""
        for key, tech in self.technologies.items():
            missing = _REQUIRED_TECH_KEYS - tech.keys()
            if missing:
                raise KnowledgeBaseError(f"technology '{key}' is missing {sorted(missing)}")
            if tech["pattern_group"] not in self.patterns:
                raise KnowledgeBaseError(f"technology '{key}' uses unknown pattern group")
            levels = {t["difficulty"] for t in tech["techniques"]}
            if "beginner" not in levels or not levels <= set(DIFFICULTY_LEVELS):
                raise KnowledgeBaseError(f"technology '{key}' needs valid techniques incl. beginner")
            if set(tech["stack"]) != set(DIFFICULTY_LEVELS):
                raise KnowledgeBaseError(f"technology '{key}' needs a stack for every level")
        for key, domain in self.domains.items():
            missing = _REQUIRED_DOMAIN_KEYS - domain.keys()
            if missing:
                raise KnowledgeBaseError(f"domain '{key}' is missing {sorted(missing)}")
            for problem in domain["problems"]:
                missing = _REQUIRED_PROBLEM_KEYS - problem.keys()
                if missing:
                    raise KnowledgeBaseError(f"a problem in '{key}' is missing {sorted(missing)}")

    def technology(self, key: str) -> dict:
        return self.technologies[key]

    def domain(self, key: str) -> dict:
        return self.domains[key]

    def technology_label(self, key: str) -> str:
        return self.technologies.get(key, {}).get("label", key)

    def domain_label(self, key: str) -> str:
        return self.domains.get(key, {}).get("label", key)
