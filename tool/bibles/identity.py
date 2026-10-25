"""Working out a Bible's version: its abbreviation (`version`, such as "KJV") and full name
(`version_name`, such as "King James Version").

Each value is taken from the first of these that supplies it:

1. `--abbreviation` and `--version-name`, which are given together.
2. What the source says about itself: an OSIS header (`osisIDWork`, the work's title), a Digital Bible
   Library `metadata.xml`, or the description after the book code on USFM, USX or USJ `\\id` lines when
   most books carry the same one (`\\id GEN Bíblia Livre - Textus Receptus`).
3. The source's name: a download named `<name> [<language>] <abbreviation>` (`American Standard
   Version of 1901 [eng] ASV.zip`), or an eBible.org name (`eng-web_usfm.zip` is WEB).
4. Fallbacks. The abbreviation is the source's base name when that looks like one (`WEB.zip`), then
   the initials of the name (`Bíblia Livre` is BL), then the base name anyway (`kjv.usfm` is kjv). The
   name falls back to the abbreviation.

Documented in `docs/usage.md`.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Tuple

from bibles.books import BOOKS
from bibles.detect import SUPPORTED_FORMATS
from bibles.model import Bible

# Where a value came from, as printed by the CLI.
GIVEN = "given on the command line"
SOURCE_NAME = "from the source name"
INITIALS = "from the initials of the name"
SAME_AS_ABBREVIATION = "same as the abbreviation"

# A short token such as KJV, WEB, NVI-PT or RV1909.
_ABBREVIATION = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,11}")
# `<name> [<language>] <rest>`, as in "American Standard Version of 1901 [eng] ASV".
_BRACKETED_LANGUAGE = re.compile(r"(?P<name>.+?)\s*\[(?P<language>[A-Za-z]{2,3}(?:-[A-Za-z0-9]+)*)\]\s*(?P<rest>.*)")
# eBible.org download names: `eng-web_usfm`, `porbr2018_usfm`.
_EBIBLE = re.compile(r"(?:(?P<language>[a-z]{3})-)?(?P<id>[a-z0-9]+)_(?:%s|sfm|readaloud|html)" % "|".join(SUPPORTED_FORMATS))
# A description ending in its abbreviation: "World English Bible (WEB)".
_TRAILING_ABBREVIATION = re.compile(r"(?P<name>.*\S)\s*\((?P<abbreviation>[^()]+)\)")
_ENGLISH_BOOK_NAMES = frozenset(
    name.casefold() for book in BOOKS for name in (book.canonical_name, book.common_name)
)


class VersionError(ValueError):
    """The abbreviation or name given on the command line is not usable."""


@dataclass(frozen=True)
class Version:
    abbreviation: str
    name: str
    abbreviation_origin: str
    name_origin: str


def is_abbreviation(value: str) -> bool:
    """True for a short token with at least one capital letter or digit, such as KJV or RV1909."""
    return bool(_ABBREVIATION.fullmatch(value)) and any(c.isupper() or c.isdigit() for c in value)


def _clean(value: Optional[str]) -> Optional[str]:
    value = " ".join((value or "").split())
    return value or None


def split_abbreviation(description: str) -> Tuple[str, Optional[str]]:
    """Split "World English Bible (WEB)" into ("World English Bible", "WEB")."""
    match = _TRAILING_ABBREVIATION.fullmatch(description)
    if match and is_abbreviation(match.group("abbreviation").strip()):
        return match.group("name"), match.group("abbreviation").strip()
    return description, None


def id_line_version(bible: Bible) -> Tuple[Optional[str], Optional[str]]:
    """The (abbreviation, name) in the books' `\\id` descriptions, when most books share one.

    A description that only names the book (`\\id RUT Ruth`) is ignored, and so is one that fewer than
    two books, or only half of the books, carry.
    """
    descriptions = []
    for bible_book in bible.books:
        description = (bible_book.headers.get("id") or "").strip(" -–—:|")
        description = " ".join(description.split())
        if description and description.casefold() not in _ENGLISH_BOOK_NAMES:
            descriptions.append(description)
    if not descriptions:
        return None, None
    description, count = Counter(descriptions).most_common(1)[0]
    if count < 2 or count * 2 <= len(bible.books):
        return None, None
    name, abbreviation = split_abbreviation(description)
    return abbreviation, name


def source_stem(source: Path) -> str:
    """A folder's name, or a file's name without its extension and any format extension before it
    (`kjv.vpl.txt` is kjv)."""
    if source.is_dir():
        return source.name
    stem = Path(source.stem)
    return stem.stem if stem.suffix[1:].lower() in SUPPORTED_FORMATS else stem.name


def source_name_version(source: Path) -> Tuple[Optional[str], Optional[str], str]:
    """The (abbreviation, name, origin) a download's file or folder name gives, if any.

    For `King James Version [eng] without Strong's numbers`, which has no abbreviation after the
    language, the abbreviation is the initials of the part before it (KJV).
    """
    stem = source_stem(source)
    match = _BRACKETED_LANGUAGE.fullmatch(stem)
    if match:
        name, rest = match.group("name").strip(), match.group("rest").strip()
        if is_abbreviation(rest):
            return rest, name, SOURCE_NAME
        return initials(name), _clean(f"{name} {rest}"), SOURCE_NAME
    match = _EBIBLE.fullmatch(stem)
    if match:
        return match.group("id").upper(), None, "from the eBible.org file name"
    return None, None, SOURCE_NAME


def source_name_language(source: Path) -> Optional[str]:
    """The language code in a download's name: `eng` in `American Standard Version [eng] ASV.zip` and
    in eBible.org's `eng-web_usfm.zip`."""
    stem = source_stem(source)
    match = _BRACKETED_LANGUAGE.fullmatch(stem) or _EBIBLE.fullmatch(stem)
    return match.group("language") if match else None


def initials(name: str) -> Optional[str]:
    """The first letters of the capitalized words: "American Standard Version of 1901" is ASV. None
    when that gives fewer than two letters."""
    value = "".join(word[0] for word in re.findall(r"[^\W\d_]+", name) if word[0].isupper())
    return value.upper() if len(value) >= 2 else None


def check_given(abbreviation: Optional[str], name: Optional[str]) -> Optional[Tuple[str, str]]:
    """The cleaned (abbreviation, name) given on the command line, or None when neither was given.

    Raises `VersionError` when only one is given, one is blank, or the abbreviation has spaces.
    """
    if abbreviation is None and name is None:
        return None
    if abbreviation is None or name is None:
        raise VersionError("--abbreviation and --version-name must be given together")
    given_abbreviation, given_name = _clean(abbreviation), _clean(name)
    if given_abbreviation is None or given_name is None:
        raise VersionError("--abbreviation and --version-name cannot be blank")
    if " " in given_abbreviation:
        raise VersionError(f"--abbreviation must be one word, without spaces: {abbreviation!r}")
    return given_abbreviation, given_name


def resolve_version(
    bible: Bible,
    source: Path,
    found: Sequence[Tuple[Optional[str], Optional[str], str]] = (),
    abbreviation: Optional[str] = None,
    name: Optional[str] = None,
) -> Version:
    """Work out the version of `bible`, parsed from `source`.

    `found` holds what the source says about itself, best first, as (abbreviation, name, origin)
    triples: the parser's findings and a bundle's `metadata.xml`. `abbreviation` and `name` are the
    values given on the command line; give both or neither. Raises `VersionError` when only one is
    given, one is blank, or the abbreviation has spaces.
    """
    given = check_given(abbreviation, name)
    if given is not None:
        return Version(given[0], given[1], GIVEN, GIVEN)

    candidates = [(_clean(value), _clean(full), origin) for value, full, origin in found]
    id_abbreviation, id_name = id_line_version(bible)
    candidates.append((id_abbreviation, id_name, "from the \\id lines"))
    candidates.append(source_name_version(source))

    found_abbreviation = next(((value, origin) for value, _, origin in candidates if value), None)
    found_name = next(((value, origin) for _, value, origin in candidates if value), None)

    if found_abbreviation is None:
        stem = source_stem(source)
        guessed = initials(found_name[0]) if found_name else None
        if is_abbreviation(stem) or guessed is None:
            found_abbreviation = (stem, SOURCE_NAME)
        else:
            found_abbreviation = (guessed, INITIALS)
    if found_name is None:
        found_name = (found_abbreviation[0], SAME_AS_ABBREVIATION)
    return Version(found_abbreviation[0], found_name[0], found_abbreviation[1], found_name[1])
