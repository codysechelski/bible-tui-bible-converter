"""RTF parser for Bibles exported as formatted text, one book per file.

The layout is the one in the ASV bundle that ships `release/USX_1/RUT.rtf` and so on:

- Heading paragraphs (paragraph style `\\s1` or higher) hold the book title (`Ruth`), the chapter headings
  (`Ruth 1`) and section headings (`BOOK I`). A heading that is the book title followed by a number starts
  that chapter; every other heading is dropped.
- Verse numbers are bold runs that hold only a number (`{\\b 16}`); the text after one belongs to that
  verse. Each paragraph is a line of the verse, as with poetry in the other formats.
- A paragraph that starts with a bold `chapter:verse` reference (`{\\b 7:16 }Many ancient authorities
  insert ...`) is a textual note and is dropped, as is a paragraph holding only a Hebrew letter and its
  name (the Psalm 119 acrostic, `\u05d0 ALEPH.`). Text before the first verse of a chapter (a Psalm
  title) is dropped like any text outside a verse. A verse whose only text is `*` (one the translation
  leaves out) is left out with a warning, like any empty verse.

The book comes from the file name when it is a USFM code (`RUT.rtf`), otherwise from the title heading.
"""

from __future__ import annotations

import codecs
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Optional, Tuple

from bibles.books import UnknownBookError, book_for_code, find_book
from bibles.model import Bible
from bibles.parsers.base import ParseError, VerseCollector, is_segment, parse_number

# Groups whose content is never text: document tables, metadata, pictures, notes and field codes.
_SKIPPED_DESTINATIONS = frozenset(
    {
        "fonttbl", "colortbl", "stylesheet", "info", "pict", "object", "footnote", "fldinst",
        "header", "headerl", "headerr", "headerf", "footer", "footerl", "footerr", "footerf",
        "listtable", "listoverridetable", "rsidtbl", "generator", "latentstyles", "themedata",
        "colorschememapping", "datastore", "xmlnstbl", "filetbl", "revtbl", "pgdsctbl",
    }
)
# Control words that stand for a character.
_CHARACTERS = {
    "tab": " ", "line": " ", "emdash": "\u2014", "endash": "\u2013", "lquote": "\u2018",
    "rquote": "\u2019", "ldblquote": "\u201c", "rdblquote": "\u201d", "bullet": "\u2022",
    "emspace": "\u2003", "enspace": "\u2002", "qmspace": "\u2005",
}
# Control symbols (a backslash and one non-letter) that stand for a character.
_SYMBOLS = {"~": "\u00a0", "_": "\u2011", "-": "", "\\": "\\", "{": "{", "}": "}"}

_TOKEN = re.compile(
    r"\\([a-zA-Z]+)(-?\d+)? ?"  # control word with an optional parameter and delimiting space
    r"|\\'([0-9a-fA-F]{2})"  # hex-encoded byte in the document's code page
    r"|\\([^a-zA-Z'])"  # control symbol
    r"|([{}])"
    r"|[\r\n]+"  # line breaks in the file are not text
    r"|([^\\{}\r\n]+)"
)
_CODE_PAGE = re.compile(rb"\\ansicpg(\d+)")
_VERSE_NUMBER = re.compile(r"\d+[a-z]?(?:-\d+[a-z]?)?")
_NOTE_REFERENCE = re.compile(r"\d+:\d+")
_CHAPTER_HEADING = re.compile(r"(.*\S)\s+(\d+)")
_ACROSTIC = re.compile(r"[\u05d0-\u05ea]\s*[A-Z]+\.?")


@dataclass(frozen=True)
class _State:
    """Formatting that RTF saves at `{` and restores at `}`."""

    bold: bool = False
    style: int = 0
    skip: bool = False
    unicode_skip: int = 1


@dataclass
class _Paragraph:
    style: int
    runs: List[Tuple[str, bool]]  # (text, bold)

    @property
    def text(self) -> str:
        return " ".join("".join(text for text, _ in self.runs).split())


def _code_page(data: bytes) -> str:
    match = _CODE_PAGE.search(data[:4096])
    encoding = f"cp{match.group(1).decode()}" if match else "cp1252"
    try:
        codecs.lookup(encoding)
    except LookupError:
        return "cp1252"
    return encoding


def paragraphs(document: str, encoding: str = "cp1252") -> List[_Paragraph]:
    """Split an RTF document into paragraphs of text runs, dropping everything that is not text."""
    result: List[_Paragraph] = []
    runs: List[Tuple[str, bool]] = []
    stack: List[_State] = []
    state = _State()
    # Characters still to skip after a \u character (its fallback for readers without Unicode).
    pending_skip = 0
    # True right after `{`, where a destination control word may follow.
    group_start = False

    def add(text: str) -> None:
        nonlocal pending_skip
        if pending_skip:
            dropped = min(pending_skip, len(text))
            text, pending_skip = text[dropped:], pending_skip - dropped
        if text and not state.skip:
            # Plain text pieces join up; bold ones stay apart, so `{\b 1}{\b 2}` is two verse numbers.
            if runs and not state.bold and not runs[-1][1]:
                runs[-1] = (runs[-1][0] + text, False)
            else:
                runs.append((text, state.bold))

    def end_paragraph() -> None:
        result.append(_Paragraph(state.style, list(runs)))
        runs.clear()

    for match in _TOKEN.finditer(document):
        word, parameter, hex_byte, symbol, brace, text = match.groups()
        starting = group_start
        group_start = False
        if brace == "{":
            stack.append(state)
            group_start = True
        elif brace == "}":
            if not stack:
                raise ValueError("unbalanced '}'")
            state = stack.pop()
            pending_skip = 0
        elif word is not None:
            value = int(parameter) if parameter is not None else None
            if word in _SKIPPED_DESTINATIONS:
                state = replace(state, skip=True)
            elif word == "u" and value is not None:
                pending_skip = 0
                add(chr(value + 65536 if value < 0 else value))
                pending_skip = state.unicode_skip
            elif word == "uc" and value is not None:
                state = replace(state, unicode_skip=value)
            elif word == "par":
                if not state.skip:
                    end_paragraph()
            elif word == "pard":
                state = replace(state, style=0)
            elif word == "plain":
                state = replace(state, bold=False)
            elif word == "b":
                state = replace(state, bold=value != 0)
            elif word == "s" and value is not None:
                state = replace(state, style=value)
            elif word in _CHARACTERS:
                add(_CHARACTERS[word])
        elif hex_byte is not None:
            add(bytes([int(hex_byte, 16)]).decode(encoding, errors="replace"))
        elif symbol is not None:
            if symbol == "*" and starting:
                state = replace(state, skip=True)  # {\* ...}: an optional destination
            else:
                add(_SYMBOLS.get(symbol, ""))
        elif text is not None:
            # The document is read as Latin-1; bytes above ASCII belong to its code page.
            add(text if text.isascii() else text.encode("latin-1").decode(encoding, errors="replace"))
    if stack:
        raise ValueError("unbalanced '{'")
    if any(text.strip() for text, _ in runs):
        end_paragraph()
    return result


def _is_note(paragraph: _Paragraph) -> bool:
    """A textual note: the first bold text is a `chapter:verse` reference."""
    for text, bold in paragraph.runs:
        if not text.strip():
            continue
        if bold:
            return bool(_NOTE_REFERENCE.fullmatch(text.strip()))
        return False
    return False


class _Reader:
    def __init__(self, path: Path, collector: VerseCollector) -> None:
        self.collector = collector
        self.stem = path.stem
        self.title: Optional[str] = None
        try:
            collector.start_book(book_for_code(self.stem).usfm_code)
            self.has_book = True
        except UnknownBookError:
            self.has_book = False

    def heading(self, paragraph: _Paragraph) -> None:
        text = paragraph.text
        if not text:
            return
        if self.title is None:
            self.title = text
            if not self.has_book:
                try:
                    self.collector.start_book(find_book(text).usfm_code)
                except UnknownBookError:
                    self.collector.skip_book(self.stem)
                self.has_book = True
            self.collector.book_header("h", text)
            return
        match = _CHAPTER_HEADING.fullmatch(text)
        if match and match.group(1).casefold() == self.title.casefold():
            self.collector.start_chapter(int(match.group(2)))

    def verse(self, number: str) -> None:
        collector = self.collector
        if not self.has_book:
            # Neither the file name nor a title heading named the book.
            collector.skip_book(self.stem)
            self.has_book = True
        if collector.skipping:
            return
        if collector.chapter is None:
            collector.start_chapter(1)  # a one-chapter book without a chapter heading
        collector.start_verse(parse_number(number, "verse"), segment=is_segment(number))

    def body(self, paragraph: _Paragraph) -> None:
        if _is_note(paragraph) or _ACROSTIC.fullmatch(paragraph.text):
            return
        collector = self.collector
        collector.line_break()
        for text, bold in paragraph.runs:
            number = text.strip()
            if bold and _VERSE_NUMBER.fullmatch(number):
                self.verse(number)
            elif number == "*" and not bold:
                continue  # the mark of a verse the translation leaves out (`{\\b 16} * {\\b 17}`)
            elif not (bold and not number):
                collector.text(text)


def parse(path: Path) -> Bible:
    data = path.read_bytes()
    if not data.lstrip().startswith(b"{\\rtf"):
        raise ParseError(f"{path}: not an RTF document (it does not start with {{\\rtf)")
    encoding = _code_page(data)
    collector = VerseCollector()
    reader = _Reader(path, collector)
    try:
        for paragraph in paragraphs(data.decode("latin-1"), encoding):
            if paragraph.style:
                reader.heading(paragraph)
            else:
                reader.body(paragraph)
        bible = collector.finish()
    except ValueError as error:
        raise ParseError(f"{path}: {error}") from error
    return bible
