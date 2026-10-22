"""VPL (verse per line) parser.

Each line is `BOOK C:V text` or `BOOK.C.V text`. The book may be a USFM code, an OSIS code or a book
name. A line with no text, or a `<range>` marker, is an absent verse. A line that is not a verse
reference, or a verse of a book outside the 66, is reported as a warning and skipped.
"""

from __future__ import annotations

import re
from pathlib import Path

from bibles.books import UnknownBookError, find_book
from bibles.model import Bible
from bibles.parsers.base import ParseError, VerseCollector, read_text

_REFERENCE = re.compile(
    r"""^\s*
    (?P<book>(?:[1-4]\s?)?[A-Za-z][A-Za-z.]*?(?:\s[A-Za-z][A-Za-z.]*?)*?)
    (?:\s+|\.)
    (?P<chapter>\d+)[:.](?P<verse>\d+)(?:-\d+)?[a-z]?
    (?:\s+(?P<text>.*?))?\s*$""",
    re.VERBOSE,
)
# The marker eBible.org and BibleNLP put on the later verses of a verse range.
RANGE_MARKER = "<range>"


def parse_text(text: str, bible: Bible, name: str = "<vpl>") -> Bible:
    collector = VerseCollector(bible)
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        match = _REFERENCE.match(line)
        if not match:
            bible.warnings.append(
                f"{Path(name).name}, line {line_number}: not a verse reference, skipped: {line.strip()[:60]!r}"
            )
            continue
        try:
            book = find_book(match.group("book"))
        except UnknownBookError as error:
            collector.skip_book(error.code)
            continue
        verse_text = match.group("text") or ""
        if not verse_text or verse_text.lower() == RANGE_MARKER:
            continue  # an absent verse, or a later verse of a range kept on its first verse
        try:
            collector.start_verse(int(match.group("verse")), book.usfm_code, int(match.group("chapter")))
            collector.text(verse_text)
            collector.end_verse()
        except ValueError as error:
            raise ParseError(f"{name}, line {line_number}: {error}") from error
    return collector.finish()


def parse(path: Path) -> Bible:
    bible = Bible()
    return parse_text(read_text(path, bible), bible, str(path))
