"""Pieces shared by every parser: the error type, text decoding and the verse collector."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional, Tuple

from bibles.books import UnknownBookError, book_for_code
from bibles.model import Bible
from bibles.normalize import EmptyVerseError, normalize_verse_text

_LEADING_NUMBER = re.compile(r"\s*(\d+)")
_SEGMENT = re.compile(r"\s*\d+[a-z]\s*$")


class ParseError(Exception):
    """The source file cannot be parsed. The message names the file and, where known, the place."""


def parse_number(value: str, what: str) -> int:
    """Return the leading number of a chapter or verse value such as `3`, `1-2` or `4a`."""
    match = _LEADING_NUMBER.match(value or "")
    if not match or int(match.group(1)) < 1:
        raise ValueError(f"invalid {what} number {value!r}")
    return int(match.group(1))


def is_segment(value: str) -> bool:
    """True for a verse segment value such as `3b` (the letter marks part of a split verse)."""
    return bool(_SEGMENT.match(value or ""))


def read_text(path: Path, bible: Bible) -> str:
    """Read a text source as UTF-8 (a byte order mark is allowed).

    A file that is not valid UTF-8 is decoded as Windows-1252, the usual legacy encoding, or failing
    that as Latin-1, and a warning is recorded.
    """
    data = path.read_bytes()
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        position = error.start
    for encoding in ("cp1252", "latin-1"):
        try:
            text = data.decode(encoding)
        except UnicodeDecodeError:
            continue
        bible.warnings.append(
            f"{path.name} is not valid UTF-8 (first bad byte at offset {position}); read as {encoding}"
        )
        return text
    raise AssertionError("latin-1 decoding cannot fail")


class VerseCollector:
    """Gathers verse text as a parser walks a source and adds finished verses to a `Bible`.

    Text arriving while no verse is open (introductions, text before the first verse) is ignored.
    `line_break` starts a new fragment, so the pieces of a verse that sit on different poetry lines or
    paragraphs are joined with the shared separator.
    """

    def __init__(self, bible: Optional[Bible] = None) -> None:
        self.bible = bible if bible is not None else Bible()
        self.book_code: Optional[str] = None
        self.chapter: Optional[int] = None
        self._verse: Optional[Tuple[str, int, int]] = None
        self._fragments: List[str] = []
        # True while inside a book that is not one of the 66 (Apocrypha, front matter, glossary).
        self.skipping = False
        self._skipped: List[str] = []

    @property
    def in_verse(self) -> bool:
        return self._verse is not None

    def start_book(self, code: str) -> None:
        self.end_verse()
        self.chapter = None
        try:
            self.book_code = book_for_code(code).usfm_code
        except UnknownBookError:
            self.skip_book(code)
            return
        self.skipping = False

    def skip_book(self, code: str) -> None:
        """Ignore everything until the next book, and warn once per skipped book code."""
        self.end_verse()
        self.book_code, self.chapter, self.skipping = None, None, True
        key = code.strip().upper() or "(no code)"
        if key not in self._skipped:
            self._skipped.append(key)
            self.bible.warnings.append(f"skipped book {key}: not one of the 66 canonical books")

    def start_chapter(self, number: int) -> None:
        self.end_verse()
        if self.skipping:
            return
        if self.book_code is None:
            raise ValueError(f"chapter {number} appears before any book")
        self.chapter = number

    def start_verse(self, number: int, book_code: Optional[str] = None,
                    chapter: Optional[int] = None, segment: bool = False) -> None:
        """Open a verse. `segment` marks a later part of a split verse (`3b`), which continues the
        open verse of the same number instead of being a duplicate."""
        if book_code is not None:
            try:
                code = book_for_code(book_code).usfm_code
            except UnknownBookError:
                self.skip_book(book_code)
                return
            if code != self.book_code or self.skipping:
                self.start_book(code)
        if self.skipping:
            return
        if chapter is not None and chapter != self.chapter:
            self.start_chapter(chapter)
        if self.book_code is None or self.chapter is None:
            raise ValueError(f"verse {number} appears before any book and chapter")
        key = (self.book_code, self.chapter, number)
        if key == self._verse and segment:
            self.line_break()
            return
        self.end_verse()
        self._verse = key
        self._fragments = [""]

    def text(self, value: str) -> None:
        if self._verse is not None:
            self._fragments[-1] += value

    def line_break(self) -> None:
        if self._verse is not None and self._fragments[-1].strip():
            self._fragments.append("")

    def end_verse(self) -> None:
        if self._verse is None:
            return
        code, chapter, number = self._verse
        self._verse = None
        fragments, self._fragments = self._fragments, []
        try:
            normalize_verse_text(fragments)
        except EmptyVerseError:
            self.bible.warnings.append(
                f"{code} {chapter}:{number} has no text and was left out"
            )
            return
        self.bible.add_verse(code, chapter, number, fragments)

    def finish(self) -> Bible:
        self.end_verse()
        return self.bible

