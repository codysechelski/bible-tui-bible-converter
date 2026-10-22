"""The USFM marker model shared by the USFM, USX and USJ parsers.

USX and USJ are serializations of USFM, so all three front ends translate their input into the same
events (book, chapter, verse, paragraph, character open and close, text) and this handler applies the
normalization rules once. That keeps the three formats producing identical verse text.
"""

from __future__ import annotations

from typing import List, Tuple

from bibles.normalize import is_dropped_inline, is_non_verse_block, marker_base
from bibles.parsers.base import VerseCollector, is_segment, parse_number


class MarkerEvents:
    def __init__(self, collector: VerseCollector) -> None:
        self.collector = collector
        # Open character markers as (base marker, dropped) pairs.
        self._chars: List[Tuple[str, bool]] = []
        # True inside a heading, title, introduction or other non verse paragraph.
        self._skip_block = False

    @property
    def in_character(self) -> bool:
        return bool(self._chars)

    @property
    def _dropping(self) -> bool:
        return self._skip_block or any(dropped for _, dropped in self._chars)

    def book(self, code: str) -> None:
        self._chars.clear()
        self.collector.start_book(code)
        # The rest of the \id line is a description, not verse text.
        self._skip_block = True

    def chapter(self, number: str) -> None:
        self._chars.clear()
        self.collector.start_chapter(parse_number(number, "chapter"))

    def chapter_end(self) -> None:
        self._chars.clear()
        self.collector.end_verse()

    def verse(self, number: str) -> None:
        self._chars.clear()
        self.collector.start_verse(parse_number(number, "verse"), segment=is_segment(number))
        # A verse inside a non verse paragraph (a Psalm title numbered as verse 1, say) is still text.
        self._skip_block = False

    def verse_end(self) -> None:
        self.collector.end_verse()

    def para(self, marker: str) -> None:
        """A paragraph-level marker: it closes open character markers and starts a new line."""
        self._chars.clear()
        self._skip_block = is_non_verse_block(marker)
        if not self._skip_block:
            self.collector.line_break()

    def char_open(self, marker: str) -> None:
        self._chars.append((marker_base(marker), is_dropped_inline(marker)))

    def char_close(self, marker: str) -> None:
        base = marker_base(marker)
        for index in range(len(self._chars) - 1, -1, -1):
            if self._chars[index][0] == base:
                # Closing a marker also closes anything opened inside it and left open.
                del self._chars[index:]
                return

    def text(self, value: str) -> None:
        if value and not self._dropping:
            self.collector.text(value)
