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

# (USFM code, canonical name, chapter count) in canonical order.
_BOOK_DATA: Tuple[Tuple[str, str, int], ...] = (
    ("GEN", "Genesis", 50),
    ("EXO", "Exodus", 40),
    ("LEV", "Leviticus", 27),
    ("NUM", "Numbers", 36),
    ("DEU", "Deuteronomy", 34),
    ("JOS", "Joshua", 24),
    ("JDG", "Judges", 21),
    ("RUT", "Ruth", 4),
    ("1SA", "I Samuel", 31),
    ("2SA", "II Samuel", 24),
    ("1KI", "I Kings", 22),
    ("2KI", "II Kings", 25),
    ("1CH", "I Chronicles", 29),
    ("2CH", "II Chronicles", 36),
    ("EZR", "Ezra", 10),
    ("NEH", "Nehemiah", 13),
    ("EST", "Esther", 10),
    ("JOB", "Job", 42),
    ("PSA", "Psalms", 150),
    ("PRO", "Proverbs", 31),
    ("ECC", "Ecclesiastes", 12),
    ("SNG", "Song of Solomon", 8),
    ("ISA", "Isaiah", 66),
    ("JER", "Jeremiah", 52),
    ("LAM", "Lamentations", 5),
    ("EZK", "Ezekiel", 48),
    ("DAN", "Daniel", 12),
    ("HOS", "Hosea", 14),
    ("JOL", "Joel", 3),
    ("AMO", "Amos", 9),
    ("OBA", "Obadiah", 1),
    ("JON", "Jonah", 4),
    ("MIC", "Micah", 7),
    ("NAM", "Nahum", 3),
    ("HAB", "Habakkuk", 3),
    ("ZEP", "Zephaniah", 3),
    ("HAG", "Haggai", 2),
    ("ZEC", "Zechariah", 14),
    ("MAL", "Malachi", 4),
    ("MAT", "Matthew", 28),
    ("MRK", "Mark", 16),
    ("LUK", "Luke", 24),
    ("JHN", "John", 21),
    ("ACT", "Acts", 28),
    ("ROM", "Romans", 16),
    ("1CO", "I Corinthians", 16),
    ("2CO", "II Corinthians", 13),
    ("GAL", "Galatians", 6),
    ("EPH", "Ephesians", 6),
    ("PHP", "Philippians", 4),
    ("COL", "Colossians", 4),
    ("1TH", "I Thessalonians", 5),
    ("2TH", "II Thessalonians", 3),
    ("1TI", "I Timothy", 6),
    ("2TI", "II Timothy", 4),
    ("TIT", "Titus", 3),
    ("PHM", "Philemon", 1),
    ("HEB", "Hebrews", 13),
    ("JAS", "James", 5),
    ("1PE", "I Peter", 5),
    ("2PE", "II Peter", 3),
    ("1JN", "I John", 5),
    ("2JN", "II John", 1),
    ("3JN", "III John", 1),
    ("JUD", "Jude", 1),
    ("REV", "Revelation of John", 22),
)


class UnknownBookError(ValueError):
    """A book code that is not one of the 66 canonical books."""

    def __init__(self, code: str) -> None:
        super().__init__(f"unknown book code {code!r}: not one of the 66 canonical books")
        self.code = code


@dataclass(frozen=True)
class Book:
    usfm_code: str
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
    for sort_order, (code, canonical, chapters) in enumerate(_BOOK_DATA, start=1):
        name = common_name(canonical)
        books.append(
            Book(
                usfm_code=code,
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


def book_for_code(code: str) -> Book:
    """Return the book for a USFM code (case and surrounding whitespace are ignored)."""
    book = _BY_CODE.get(code.strip().upper())
    if book is None:
        raise UnknownBookError(code)
    return book
