"""The book names a database shows: English, or the translation's own.

Each book's `common_name` (the name bible-tui shows) is the translation's own name for the book when
the Bible is not in English, and the English name from `bibles/books.py` otherwise. `canonical_name` and
`slug` stay English in every database, so they identify the book whatever the language.

The translation's name for a book is the first of: the bundle's `metadata.xml` short name, the `\\toc2`
or `\\h` line (USFM, USX, USJ), the OSIS book title's `short` attribute, or the RTF title heading. The
language is the first one known of `metadata.xml`, the OSIS `xml:lang`, and the source's name (`[eng]`,
`eng-web_usfm`). Without a language, the translation's names are used when most of them are not English
book names. Documented in `docs/normalization.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from bibles.books import BOOKS
from bibles.identity import source_name_language
from bibles.model import Bible

# Header markers that hold a book's name, best first.
NAME_MARKERS = ("toc2", "h")
_ENGLISH_NAMES = frozenset(
    name.casefold() for book in BOOKS for name in (book.canonical_name, book.common_name)
)


@dataclass(frozen=True)
class BookNames:
    """What `apply_book_names` decided, for the run output."""

    translated: bool
    count: int  # books for which the source gives a name
    language: Optional[str]
    language_origin: Optional[str]

    def describe(self) -> str:
        language = f"language {self.language} {self.language_origin}" if self.language else None
        if self.translated:
            reason = language or "most of the source's book names are not English"
            return f"the translation's own, for {self.count} books ({reason})"
        if language:
            return f"English ({language})"
        return "English" if self.count == 0 else "English (the source's book names are English)"


def is_english(language: str) -> bool:
    return language.strip().lower().replace("_", "-").split("-")[0] in ("en", "eng")


def _is_english_name(name: str) -> bool:
    return " ".join(name.split()).casefold() in _ENGLISH_NAMES


def apply_book_names(bible: Bible, source: Path, parser_origin: str = "from the source",
                     metadata_language: Optional[str] = None, metadata_names: Optional[Dict[str, str]] = None,
                     metadata_origin: str = "from metadata.xml") -> BookNames:
    """Set each book's `name` to the translation's own name when the Bible is not in English.

    `metadata_language` and `metadata_names` come from a bundle's `metadata.xml`; the other names and
    the language come from the parsed `bible` (`parser_origin` says where) and `source`'s name.
    """
    names: Dict[str, str] = {}
    for bible_book in bible.books:
        candidates = [(metadata_names or {}).get(bible_book.code)]
        candidates += [bible_book.headers.get(marker) for marker in NAME_MARKERS]
        name = next((" ".join(c.split()) for c in candidates if c and c.strip()), None)
        if name:
            names[bible_book.code] = name

    language, origin = None, None
    for value, where in ((metadata_language, metadata_origin), (bible.language, parser_origin),
                         (source_name_language(source), "from the source name")):
        if value and value.strip():
            language, origin = value.strip(), where
            break

    if not names:
        translated = False
    elif language is not None:
        translated = not is_english(language)
    else:
        english = sum(1 for name in names.values() if _is_english_name(name))
        translated = english * 2 < len(names)

    if translated:
        for bible_book in bible.books:
            bible_book.name = names.get(bible_book.code)
    return BookNames(translated, len(names), language, origin)
