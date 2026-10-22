"""OSIS parser.

Verses are either containers (`<verse osisID="Gen.1.1">text</verse>`) or milestone pairs
(`<verse sID="Gen.1.1" osisID="Gen.1.1"/>text<verse eID="Gen.1.1"/>`). Only text inside a verse is
kept. Namespaces are ignored, so any OSIS namespace (or none) works.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Tuple

from bibles.books import UnknownBookError, book_for_osis
from bibles.model import Bible
from bibles.normalize import OSIS_DROPPED_DIV_TYPES, OSIS_DROPPED_ELEMENTS
from bibles.parsers.base import ParseError, VerseCollector, parse_number

# Elements whose start and end separate lines or paragraphs of verse text.
_LINE_ELEMENTS = frozenset({"p", "l", "lg", "lb", "list", "item", "row", "cell"})
# Metadata elements that never hold verse text.
_SKIPPED = frozenset({"header"})


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_osis_id(osis_id: str) -> Tuple[str, int, int]:
    """Return (USFM book code, chapter, verse) for the first reference in an osisID value.

    A range or list such as `Gen.1.1 Gen.1.2` or `Gen.1.1-Gen.1.2` uses its first verse.
    """
    first = osis_id.split()[0].split("-")[0] if osis_id.strip() else ""
    # Strip a work prefix (`KJV:Gen.1.1`) and a sub-verse part (`Gen.1.1!a`).
    first = first.split(":")[-1].split("!")[0]
    parts = first.split(".")
    if len(parts) != 3:
        raise ValueError(f"osisID {osis_id!r} is not a book.chapter.verse reference")
    book = book_for_osis(parts[0])
    return book.usfm_code, parse_number(parts[1], "chapter"), parse_number(parts[2], "verse")


class _Walker:
    def __init__(self, collector: VerseCollector) -> None:
        self.collector = collector
        self.verse_count = 0

    def walk(self, element: ET.Element) -> None:
        tag = _local(element.tag)
        collector = self.collector

        if tag in OSIS_DROPPED_ELEMENTS or tag in _SKIPPED or (
            tag == "div" and element.get("type") in OSIS_DROPPED_DIV_TYPES
        ):
            pass
        elif tag == "verse":
            if element.get("eID") is not None:
                collector.end_verse()
            else:
                osis_id = element.get("osisID") or element.get("sID") or ""
                self.start_verse(osis_id)
                if element.get("sID") is None:
                    # Container form: the text inside is the verse.
                    self.children(element)
                    collector.end_verse()
        else:
            line = tag in _LINE_ELEMENTS
            if line:
                collector.line_break()
            self.children(element)
            if line:
                collector.line_break()

        if element.tail:
            collector.text(element.tail)

    def start_verse(self, osis_id: str) -> None:
        try:
            code, chapter, verse = parse_osis_id(osis_id)
        except UnknownBookError as error:
            self.collector.skip_book(error.code)
            return
        self.collector.start_verse(verse, code, chapter)
        self.verse_count += 1

    def children(self, element: ET.Element) -> None:
        if element.text:
            self.collector.text(element.text)
        for child in element:
            self.walk(child)


def _header_text(root: ET.Element, name: str) -> Optional[str]:
    for element in root.iter():
        if _local(element.tag) == "work":
            for child in element:
                if _local(child.tag) == name and (child.text or "").strip():
                    return " ".join(child.text.split())
            break
    return None


def parse(path: Path) -> Bible:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        raise ParseError(f"{path}: not well-formed XML: {error}") from error
    if _local(root.tag) not in ("osis", "osisText"):
        raise ParseError(f"{path}: not an OSIS document (root element is <{_local(root.tag)}>, expected <osis>)")

    collector = VerseCollector()
    walker = _Walker(collector)
    try:
        walker.children(root)
        bible = collector.finish()
    except ValueError as error:
        raise ParseError(f"{path}: {error}") from error
    if walker.verse_count == 0:
        raise ParseError(f"{path}: the OSIS document contains no verse references")

    for element in root.iter():
        if _local(element.tag) == "osisText":
            bible.version = element.get("osisIDWork") or None
            break
    bible.version_name = _header_text(root, "title")
    return bible
