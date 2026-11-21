"""Small text helpers used to make generated titles read naturally."""
import re

SMALL_WORDS = {
    "a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "into",
    "of", "on", "or", "the", "to", "via", "with", "vs",
}

# Words that start with a vowel letter but a consonant sound ("a unified", "a user").
_CONSONANT_SOUND_PREFIXES = ("uni", "use", "usa", "usu", "uti", "eu", "one", "once")
# Words that start with a consonant letter but a vowel sound ("an hour").
_VOWEL_SOUND_PREFIXES = ("hour", "honest", "honor", "heir")
# Acronyms read letter by letter whose first letter sounds like a vowel ("an SMS", "an RFID").
_ACRONYM_AN_LETTERS = set("AEFHILMNORSX")


def needs_an(word: str) -> bool:
    """Return True if the indefinite article before ``word`` should be "an"."""
    core = re.sub(r"[^A-Za-z0-9]", "", word.split("-")[0])
    if not core:
        return False
    if core[0].isdigit():
        return core[0] == "8"  # "an 8-bit", otherwise "a 2D", "a 3D"
    if core.isupper():  # acronym such as SMS, AI, AR, RFID
        return core[0] in _ACRONYM_AN_LETTERS
    lower = core.lower()
    if lower.startswith(_CONSONANT_SOUND_PREFIXES):
        return False
    if lower.startswith(_VOWEL_SOUND_PREFIXES):
        return True
    return lower[0] in "aeiou"


_ARTICLE_RE = re.compile(r"\b([Aa]n?) ([^\s]+)")


def fix_articles(text: str) -> str:
    """Correct "a"/"an" so they agree with the following word."""

    def repl(match: re.Match) -> str:
        article, word = match.group(1), match.group(2)
        wanted = "an" if needs_an(word) else "a"
        if article[0].isupper():
            wanted = wanted.capitalize()
        return f"{wanted} {word}"

    return _ARTICLE_RE.sub(repl, text)


def _capitalize_part(part: str) -> str:
    """Uppercase the first letter, keeping the rest as written (keeps IoT, SMS, GIS)."""
    for i, ch in enumerate(part):
        if ch.isalpha():
            return part[:i] + ch.upper() + part[i + 1:]
    return part


def smart_title(text: str) -> str:
    """Title-case a sentence, keeping small words lowercase and acronyms intact."""
    out = []
    capitalize_next = True
    for word in text.split(" "):
        if not word:
            out.append(word)
            continue
        if not capitalize_next and word.lower() in SMALL_WORDS:
            out.append(word.lower())
        else:
            out.append("-".join(_capitalize_part(p) for p in word.split("-")))
        capitalize_next = word.endswith(":")
    return " ".join(out)


def normalize(text: str) -> str:
    """Lowercase alphanumeric form, used for de-duplication."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def significant_words(text: str) -> set[str]:
    return {w for w in normalize(text).split() if len(w) > 3}
