"""Default Chapter 1 writer: fills section templates from the knowledge base (no API needed).

Statements of the problem and objectives are built from the same four items
(core module, technique, feature, evaluation), so they always correspond one-to-one.
Factual claims get a "[cite source]" placeholder: students must add real references.
"""
import random

from ..knowledge_base import KnowledgeBase
from ..textutils import fix_articles, smart_title
from .base import SECTION_KEYS, OutlineEngine
from .context import expand_context

CITE = "[cite source]"
ISO_CRITERIA = "functional suitability, performance efficiency, usability, reliability, and security"


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def _institution(setting: str) -> str:
    """'the municipality' -> 'the Municipality', 'a community college' -> 'the Community College'."""
    for article in ("the ", "a ", "an "):
        if setting.lower().startswith(article):
            return "the " + smart_title(setting[len(article):])
    return smart_title(setting)


class TemplateOutlineEngine(OutlineEngine):
    source = "template"

    def __init__(self, kb: KnowledgeBase):
        self.kb = kb

    def write_section(self, key, title, ctx, seed=0, current=None) -> str:
        if key not in SECTION_KEYS:
            raise ValueError(f"Unknown section '{key}'")
        c = expand_context(self.kb, ctx)
        rng = random.Random(f"{seed}:{key}")
        writer = getattr(self, f"_{key}")
        return fix_articles(writer(title, c, rng).strip())

    # ---------------------------------------------------------------- shared pieces
    @staticmethod
    def _is_sim(c) -> bool:
        return c["group"] == "simulation"

    def _system_phrase(self, c) -> str:
        if self._is_sim(c):
            return f"a {c['platform']} {c['artifact']} on {c['topic']}"
        return f"a {c['platform']} {c['problem']} {c['artifact']}"

    def _items(self, c) -> list[tuple[str, str]]:
        """(problem question, objective) pairs, kept in the same order."""
        t, b = c["technique_rec"], c["beneficiary"]
        if self._is_sim(c):
            return [
                (f"How can a {c['platform']} {c['artifact']} be designed to teach {c['topic']} to {b}?",
                 f"design and develop a {c['platform']} {c['artifact']} that teaches {c['topic']} to {b}"),
                (f"How can {t['name']} be applied for {t['purpose']}?",
                 f"apply {t['name']} for {t['purpose']}"),
                (f"How can {c['feature']} be used to support learner engagement?",
                 f"include {c['feature']} to support learner engagement"),
                (f"What is the level of usability and learning effectiveness of the {c['artifact']} "
                 f"as evaluated by {b} and IT experts?",
                 f"evaluate the usability and learning effectiveness of the {c['artifact']} "
                 f"with {b} and IT experts"),
            ]
        p = c["problem_rec"]
        return [
            (f"How can a {p['module']} module be designed so that it {p['module_desc']}?",
             f"design and develop a {p['module']} module that {p['module_desc']}"),
            (f"How can {t['name']} be applied for {t['purpose']}?",
             f"apply {t['name']} for {t['purpose']}"),
            (f"How can {c['feature']} be integrated to keep users informed and engaged?",
             f"integrate {c['feature']} to keep users informed and engaged"),
            (f"What is the level of quality of the developed system as evaluated by {b} and IT experts "
             f"in terms of {ISO_CRITERIA}, based on ISO/IEC 25010?",
             f"evaluate the quality of the system using the ISO/IEC 25010 software quality model in "
             f"terms of {ISO_CRITERIA}"),
        ]

    def _modules(self, c) -> list[tuple[str, str]]:
        feature_name = smart_title(c["feature"].removeprefix("a ").removeprefix("an "))
        if self._is_sim(c):
            return [
                ("Lessons and Levels", f"presents the lessons on {c['topic']} in a guided sequence"),
                ("Assessment", "checks learner understanding through quizzes and challenges"),
                (feature_name, f"provides {c['feature']} to keep learners motivated"),
                ("Progress Reports", "lets facilitators review learner progress and scores"),
            ]
        p = c["problem_rec"]
        return [
            ("User Management", "handles account registration, login, and role-based access"),
            (p["module"], p["module_desc"]),
            (feature_name, f"extends the system with {c['feature']} so that users stay informed"),
            ("Reports", f"generates summaries and printable reports for administrators and {c['beneficiary']}"),
        ]

    # --------------------------------------------------------------------- sections
    def _background(self, title, c, rng) -> str:
        d, t, p = c["domain_rec"], c["technique_rec"], c["problem_rec"]
        tech_label = c["tech_rec"]["label"]
        if self._is_sim(c):
            context = rng.choice([
                f"{_cap(c['topic'])} is an important subject for {c['beneficiary']}. However, traditional "
                f"lecture-based instruction can make it difficult for learners to stay engaged and to "
                f"retain key concepts {CITE}.",
                f"Learning {c['topic']} requires more than memorization; learners need to understand and "
                f"apply what they learn. In {c['setting']}, {c['beneficiary']} often have limited access "
                f"to engaging learning materials on this topic {CITE}.",
            ])
        else:
            context = rng.choice([
                f"{d['label']} services play a vital role in the community. In {c['setting']}, "
                f"{c['beneficiary']} rely on processes such as {p['subject']}. However, many of these "
                f"processes are still handled manually, which often results in {p['problem']} {CITE}.",
                f"In {c['setting']}, {p['subject']} remains largely manual. {_cap(c['beneficiary'])} "
                f"frequently experience {p['problem']}, which affects the quality and speed of service "
                f"{CITE}.",
            ])
        technology = rng.choice([
            f"Advances in {tech_label} have made it possible to address such problems more efficiently. "
            f"In particular, {t['name']} has been used for {t['purpose']} in similar settings {CITE}. "
            f"Related studies also show that {c['feature']} can improve how users receive and act on "
            f"information {CITE}.",
            f"The growing availability of {tech_label} tools gives institutions an opportunity to "
            f"modernize their processes. {_cap(t['name'])} is one approach that supports "
            f"{t['purpose']} {CITE}, while {c['feature']} can help users stay informed and responsive {CITE}.",
        ])
        goal = (f"make learning {c['topic']} more interactive and measurable" if self._is_sim(c)
                else p["goal"])
        proposal = (
            f"With these considerations, the researchers propose {c['system_name']}, "
            f"{self._system_phrase(c)} for {c['beneficiary']} in {c['setting']}. The study aims to "
            f"{goal} and to provide a practical tool whose quality can be evaluated against established "
            f"software quality standards."
        )
        return "\n\n".join([context, technology, proposal])

    def _problem(self, title, c, rng) -> str:
        if self._is_sim(c):
            general = (f"This study aims to help {c['beneficiary']} in {c['setting']} learn {c['topic']} "
                       f"more effectively through {self._system_phrase(c)}.")
        else:
            general = rng.choice([
                f"This study aims to address {c['problem_rec']['problem']} among {c['beneficiary']} "
                f"in {c['setting']}.",
                f"This study seeks to solve the problem of {c['problem_rec']['problem']} experienced by "
                f"{c['beneficiary']} in {c['setting']}.",
            ])
        questions = "\n".join(f"{i}. {q}" for i, (q, _) in enumerate(self._items(c), 1))
        return f"{general} Specifically, it seeks to answer the following questions:\n\n{questions}"

    def _objectives(self, title, c, rng) -> str:
        general = (f"The general objective of this study is to design and develop {c['system_name']}, "
                   f"{self._system_phrase(c)} for {c['beneficiary']} in {c['setting']}.")
        items = self._items(c)
        lines = "\n".join(
            f"{i}. {o}{'.' if i == len(items) else ';'}{' and' if i == len(items) - 1 else ''}"
            for i, (_, o) in enumerate(items, 1)
        )
        return f"{general}\n\nSpecifically, the study aims to:\n\n{lines}"

    def _significance(self, title, c, rng) -> str:
        tech_label = c["tech_rec"]["label"]
        if self._is_sim(c):
            primary = (f"The {c['artifact']} gives them an engaging way to learn {c['topic']} and to "
                       f"practice at their own pace.")
            institution = "It provides a supplementary learning resource that supports classroom instruction."
        else:
            primary = f"The system will help them {c['problem_rec']['goal']}, saving time and effort."
            institution = "It will gain accurate, organized records and reports that support decision-making."
        return "\n".join([
            "The results of this study will benefit the following:",
            "",
            f"- **{smart_title(c['beneficiary'])}.** {primary}",
            f"- **{smart_title(c['secondary_beneficiary'])}.** They will have faster access to timely and "
            f"accurate information related to {c['problem'] if not self._is_sim(c) else 'learner progress'}.",
            f"- **The Management of {_institution(c['setting'])}.** {institution}",
            f"- **The Researchers.** The study allows them to apply their knowledge of {tech_label} "
            f"to a real problem and to gain experience in developing a complete system.",
            f"- **Future Researchers.** The study can serve as a reference for related studies on "
            f"{c['problem'] if not self._is_sim(c) else c['topic']} and {c['technique']}.",
        ])

    def _scope(self, title, c, rng) -> str:
        stack = ", ".join(c["tech_rec"]["stack"][c["difficulty"]])
        modules = "\n".join(f"- **{name}** – {desc}." for name, desc in self._modules(c))
        coverage = c["topic"] if self._is_sim(c) else c["problem"]
        evaluation = ("its usability and learning effectiveness will be evaluated by selected users"
                      if self._is_sim(c) else "its quality will be evaluated using ISO/IEC 25010")
        return "\n".join([
            f"This study focuses on the development of {c['system_name']}, {self._system_phrase(c)} "
            f"intended for {c['beneficiary']} in {c['setting']}. It includes the following modules:",
            "",
            modules,
            "",
            f"The system will be developed using {stack}, and {evaluation}.",
            "",
            "The study has the following limitations:",
            "",
            f"- The system covers only {coverage} and does not include other processes of {c['setting']}.",
            f"- {c['tech_rec']['limitation']}",
            f"- The evaluation is limited to selected respondents from {c['setting']} within the study period.",
        ])

    def _terms(self, title, c, rng) -> str:
        t = c["technique_rec"]
        feature_term = smart_title(c["feature"].removeprefix("a ").removeprefix("an "))
        terms = [
            (c["system_name"], f"the proposed {self._system_phrase(c).removeprefix('a ').removeprefix('an ')} "
                               f"developed in this study."),
            (smart_title(t["name"].removeprefix("a ").removeprefix("an ")),
             f"the approach used in the system for {t['purpose']}."),
            (feature_term, f"the component of the system that keeps users informed through {c['feature']}."),
            (smart_title(c["beneficiary"]), f"the primary users of {c['system_name']} in this study."),
        ]
        if not self._is_sim(c):
            p = c["problem_rec"]
            terms.insert(2, (f"{p['module']} Module", f"the part of the system that {p['module_desc']}."))
        terms.append(("ISO/IEC 25010", "an international standard used in this study to evaluate the "
                                       "quality of the developed software."))
        lines = "\n".join(f"- **{term}** – refers to {definition}" for term, definition in terms)
        return f"The following terms are defined operationally as used in this study:\n\n{lines}"

    def _overview(self, title, c, rng) -> str:
        t = c["technique_rec"]
        if self._is_sim(c):
            roles = [("Facilitator", "manages lessons and reviews learner progress"),
                     (smart_title(c["beneficiary"]), f"play through the lessons on {c['topic']}")]
            how = (f"Learners open {c['system_name']} and progress through lessons on {c['topic']}. "
                   f"The {c['artifact']} applies {t['name']} for {t['purpose']}, and {c['feature']} keeps "
                   f"them motivated. Facilitators review scores and progress to see which concepts need "
                   f"more attention.")
        else:
            p = c["problem_rec"]
            roles = [("Administrator", "manages accounts, settings, and records"),
                     (smart_title(c["beneficiary"]), f"use the system to {p['goal']}"),
                     (smart_title(c["secondary_beneficiary"]), "receive updates and information from the system")]
            how = (f"Users log in according to their role. {_cap(c['beneficiary'])} use the {p['module']} "
                   f"module, which {p['module_desc']}. The system applies {t['name']} for {t['purpose']}, "
                   f"and {c['feature']} keeps users informed of important updates. Administrators review "
                   f"records and generate reports to support decision-making.")
        role_lines = "\n".join(f"- **{name}** – {desc}." for name, desc in roles)
        module_lines = "\n".join(f"- **{name}** – {desc}." for name, desc in self._modules(c))
        return (f"**User roles**\n\n{role_lines}\n\n**Main modules**\n\n{module_lines}\n\n"
                f"**How it works**\n\n{how}")
