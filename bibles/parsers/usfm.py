"""USFM parser: tokenizes backslash markers into the shared marker events."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from bibles.model import Bible
from bibles.normalize import marker_base
from bibles.parsers.base import ParseError, VerseCollector, read_text
from bibles.parsers.markers import MarkerEvents

# Character-level markers (base names). Anything else that is not handled below is paragraph-level.
# Note-internal markers are included so that a `\fp` inside a footnote does not end the note.
CHARACTER_MARKERS = frozenset(
    {
        # notes and their contents
        "f", "fe", "ef", "x", "ex",
        "fr", "fq", "fqa", "fk", "ft", "fl", "fw", "fp", "fv", "fdc", "fm",
        "xo", "xk", "xq", "xt", "xta", "xop", "xot", "xnt", "xdc",
        # special text and formatting
        "add", "bk", "dc", "k", "nd", "ord", "pn", "png", "addpn", "qt", "sig", "sls", "tl", "wj",
        "em", "bd", "it", "bdit", "no", "sc", "sup", "w", "rb", "pro", "wg", "wh", "wa", "ndx",
        "rq", "qs", "qac", "litl", "lik", "liv", "jmp", "fig", "va", "vp", "ca", "cat", "ior", "iqt",
    }
)

# Markers followed by a single word argument: the book code, chapter number, verse number or
# published chapter character.
ARGUMENT_MARKERS = frozenset({"id", "c", "v", "cp"})

_TOKEN = re.compile(r"\\(\*)|\\\+?([A-Za-z][A-Za-z0-9]*(?:-[se])?)(\*?)")
_ARGUMENT = re.compile(r"\s*(\S+)\s?", re.DOTALL)


class _Tokenizer:
    def __init__(self, events: MarkerEvents) -> None:
        self.events = events
        self.pending: Optional[str] = None
        self.after_open = False
        self.in_milestone = False
        self.in_sidebar = False

    def marker(self, name: str, closing: bool) -> None:
        if self.pending is not None:
            raise ValueError(f"\\{self.pending} is missing its value")
        self.in_milestone = False
        base = marker_base(name)
        if self.in_sidebar:
            self.in_sidebar = base != "esbe"
            return
        if name.endswith(("-s", "-e")) or base == "ts":
            self.in_milestone = True
            return
        if closing:
            self.after_open = False
            self.events.char_close(name)
            return
        self.after_open = True
        if base == "esb":
            self.in_sidebar = True
        elif base in ARGUMENT_MARKERS:
            self.pending = base
        elif base in CHARACTER_MARKERS:
            self.events.char_open(name)
        else:
            self.events.para(name)

    def text(self, segment: str) -> None:
        if self.in_milestone or self.in_sidebar or not segment:
            return
        if self.pending is not None:
            match = _ARGUMENT.match(segment)
            if not match:
                return  # only whitespace so far; the value may follow
            marker, self.pending = self.pending, None
            self.after_open = False
            value, segment = match.group(1), segment[match.end():]
            if marker == "id":
                self.events.book(value)
            elif marker == "c":
                self.events.chapter(value)
            elif marker == "v":
                self.events.verse(value)
        elif self.after_open:
            self.after_open = False
            if segment[0].isspace():
                segment = segment[1:]
        if "|" in segment and self.events.in_character:
            # `\w word|lemma="..."\w*`: the attributes after the bar are not text.
            segment = segment[: segment.index("|")]
        self.events.text(segment)

    def finish(self) -> None:
        if self.pending is not None:
            raise ValueError(f"\\{self.pending} is missing its value")


def parse_text(text: str, bible: Optional[Bible] = None, name: str = "<usfm>") -> Bible:
    """Parse USFM text, raising `ParseError` that names `name` and the line on failure."""
    collector = VerseCollector(bible)
    tokenizer = _Tokenizer(MarkerEvents(collector))
    position = 0
    try:
        for match in _TOKEN.finditer(text):
            tokenizer.text(text[position : match.start()])
            position = match.start()
            if match.group(1):
                tokenizer.in_milestone = False
                tokenizer.after_open = False
            else:
                tokenizer.marker(match.group(2), bool(match.group(3)))
            position = match.end()
        tokenizer.text(text[position:])
        tokenizer.finish()
        return collector.finish()
    except ValueError as error:
        line = text.count("\n", 0, position) + 1
        raise ParseError(f"{name}, line {line}: {error}") from error


def parse(path: Path) -> Bible:
    bible = Bible()
    return parse_text(read_text(path, bible), bible, str(path))
