"""Canonical 66-book reference data shared by every parser.

The names, slugs, testaments, sort orders and chapter counts match the reference database
(`bible-esv/bible_esv.sqlite`), and the naming rules mirror `common_name` and `slugify` in
`bible-esv/tools/build_sqlite.py`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Tuple

OLD_TESTAMENT = "old"
NEW_TESTAMENT = "new"
OLD_TESTAMENT_BOOK_COUNT = 39

# (USFM code, OSIS code, canonical name, chapter count) in canonical order.
_BOOK_DATA: Tuple[Tuple[str, str, str, int], ...] = (
    ("GEN", "Gen", "Genesis", 50),
    ("EXO", "Exod", "Exodus", 40),
    ("LEV", "Lev", "Leviticus", 27),
    ("NUM", "Num", "Numbers", 36),
    ("DEU", "Deut", "Deuteronomy", 34),
    ("JOS", "Josh", "Joshua", 24),
    ("JDG", "Judg", "Judges", 21),
    ("RUT", "Ruth", "Ruth", 4),
    ("1SA", "1Sam", "I Samuel", 31),
    ("2SA", "2Sam", "II Samuel", 24),
    ("1KI", "1Kgs", "I Kings", 22),
    ("2KI", "2Kgs", "II Kings", 25),
    ("1CH", "1Chr", "I Chronicles", 29),
    ("2CH", "2Chr", "II Chronicles", 36),
    ("EZR", "Ezra", "Ezra", 10),
    ("NEH", "Neh", "Nehemiah", 13),
    ("EST", "Esth", "Esther", 10),
    ("JOB", "Job", "Job", 42),
    ("PSA", "Ps", "Psalms", 150),
    ("PRO", "Prov", "Proverbs", 31),
    ("ECC", "Eccl", "Ecclesiastes", 12),
    ("SNG", "Song", "Song of Solomon", 8),
    ("ISA", "Isa", "Isaiah", 66),
    ("JER", "Jer", "Jeremiah", 52),
    ("LAM", "Lam", "Lamentations", 5),
    ("EZK", "Ezek", "Ezekiel", 48),
    ("DAN", "Dan", "Daniel", 12),
    ("HOS", "Hos", "Hosea", 14),
    ("JOL", "Joel", "Joel", 3),
    ("AMO", "Amos", "Amos", 9),
    ("OBA", "Obad", "Obadiah", 1),
    ("JON", "Jonah", "Jonah", 4),
    ("MIC", "Mic", "Micah", 7),
    ("NAM", "Nah", "Nahum", 3),
    ("HAB", "Hab", "Habakkuk", 3),
    ("ZEP", "Zeph", "Zephaniah", 3),
    ("HAG", "Hag", "Haggai", 2),
    ("ZEC", "Zech", "Zechariah", 14),
    ("MAL", "Mal", "Malachi", 4),
    ("MAT", "Matt", "Matthew", 28),
    ("MRK", "Mark", "Mark", 16),
    ("LUK", "Luke", "Luke", 24),
    ("JHN", "John", "John", 21),
    ("ACT", "Acts", "Acts", 28),
    ("ROM", "Rom", "Romans", 16),
    ("1CO", "1Cor", "I Corinthians", 16),
    ("2CO", "2Cor", "II Corinthians", 13),
    ("GAL", "Gal", "Galatians", 6),
    ("EPH", "Eph", "Ephesians", 6),
    ("PHP", "Phil", "Philippians", 4),
    ("COL", "Col", "Colossians", 4),
    ("1TH", "1Thess", "I Thessalonians", 5),
    ("2TH", "2Thess", "II Thessalonians", 3),
    ("1TI", "1Tim", "I Timothy", 6),
    ("2TI", "2Tim", "II Timothy", 4),
    ("TIT", "Titus", "Titus", 3),
    ("PHM", "Phlm", "Philemon", 1),
    ("HEB", "Heb", "Hebrews", 13),
    ("JAS", "Jas", "James", 5),
    ("1PE", "1Pet", "I Peter", 5),
    ("2PE", "2Pet", "II Peter", 3),
    ("1JN", "1John", "I John", 5),
    ("2JN", "2John", "II John", 1),
    ("3JN", "3John", "III John", 1),
    ("JUD", "Jude", "Jude", 1),
    ("REV", "Rev", "Revelation of John", 22),
)


class UnknownBookError(ValueError):
    """A book code that is not one of the 66 canonical books."""

    def __init__(self, code: str) -> None:
        super().__init__(f"unknown book code {code!r}: not one of the 66 canonical books")
        self.code = code


@dataclass(frozen=True)
class Book:
    usfm_code: str
    osis_code: str
    canonical_name: str
    common_name: str
    slug: str
    testament: str
    sort_order: int
    chapter_count: int


def common_name(canonical_name: str) -> str:
    for roman, arabic in (("III ", "3 "), ("II ", "2 "), ("I ", "1 ")):
        if canonical_name.startswith(roman):
            return arabic + canonical_name[len(roman) :]
    if canonical_name == "Revelation of John":
        return "Revelation"
    return canonical_name


def slugify(value: str) -> str:
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def _build_books() -> Tuple[Book, ...]:
    books = []
    for sort_order, (code, osis_code, canonical, chapters) in enumerate(_BOOK_DATA, start=1):
        name = common_name(canonical)
        books.append(
            Book(
                usfm_code=code,
                osis_code=osis_code,
                canonical_name=canonical,
                common_name=name,
                slug=slugify(name),
                testament=OLD_TESTAMENT if sort_order <= OLD_TESTAMENT_BOOK_COUNT else NEW_TESTAMENT,
                sort_order=sort_order,
                chapter_count=chapters,
            )
        )
    return tuple(books)


BOOKS: Tuple[Book, ...] = _build_books()
_BY_CODE: Dict[str, Book] = {book.usfm_code: book for book in BOOKS}
_BY_OSIS: Dict[str, Book] = {book.osis_code.upper(): book for book in BOOKS}
_BY_NAME: Dict[str, Book] = {
    name.upper(): book for book in BOOKS for name in (book.canonical_name, book.common_name)
}
# Other three letter codes in common use, such as eBible.org's VPL downloads, mapped to USFM codes.
_ALIASES: Dict[str, str] = {
    "SOL": "SNG", "EZE": "EZK", "JOE": "JOL", "MAR": "MRK", "JOH": "JHN", "PHI": "PHP", "JAM": "JAS",
    "1JO": "1JN", "2JO": "2JN", "3JO": "3JN",
}


def book_for_code(code: str) -> Book:
    """Return the book for a USFM code (case and surrounding whitespace are ignored)."""
    book = _BY_CODE.get(code.strip().upper())
    if book is None:
        raise UnknownBookError(code)
    return book


def book_for_osis(code: str) -> Book:
    """Return the book for an OSIS book code such as `Gen` or `1Sam` (case is ignored).

    USFM codes are accepted too, since some OSIS files use them.
    """
    key = code.strip().upper()
    book = _BY_OSIS.get(key) or _BY_CODE.get(key)
    if book is None:
        raise UnknownBookError(code)
    return book


def find_book(token: str) -> Book:
    """Return the book for a USFM code, an OSIS code, a common alias, or a canonical or common name."""
    key = " ".join(token.split()).upper()
    book = (_BY_CODE.get(key) or _BY_OSIS.get(key) or _BY_NAME.get(key)
            or _BY_CODE.get(_ALIASES.get(key, "")))
    if book is None:
        raise UnknownBookError(token)
    return book
