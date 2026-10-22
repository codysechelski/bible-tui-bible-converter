"""USX parser: walks the XML tree and feeds the shared marker events."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from bibles.model import Bible
from bibles.parsers.base import ParseError, VerseCollector
from bibles.parsers.markers import MarkerEvents

# Elements skipped together with their content (their tail text is still read).
_SKIPPED = frozenset({"sidebar", "periph", "optbreak", "ms"})


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _number(element: ET.Element, what: str) -> Optional[str]:
    """The `number` attribute, or the number at the end of `sid` (`GEN 1` or `GEN 1:1`)."""
    number = element.get("number")
    if number is None and element.get("sid"):
        reference = element.get("sid", "").split()[-1]
        number = reference.split(":")[-1] if what == "verse" else reference.split(":")[0]
    return number


class _Walker:
    def __init__(self, events: MarkerEvents) -> None:
        self.events = events

    def walk(self, element: ET.Element) -> None:
        tag = _local(element.tag)
        events = self.events
        style = element.get("style", "")

        if tag == "book":
            events.book(element.get("code") or element.get("id") or "")
        elif tag == "chapter":
            number = _number(element, "chapter")
            if number is None:
                events.chapter_end()  # USX 3 end milestone: <chapter eid="GEN 1"/>
            else:
                events.chapter(number)
        elif tag == "verse":
            number = _number(element, "verse")
            if number is None:
                events.verse_end()  # USX 3 end milestone: <verse eid="GEN 1:1"/>
            else:
                events.verse(number)
        elif tag in _SKIPPED:
            pass
        elif tag in ("para", "row", "cell"):
            events.para(style or {"row": "tr", "cell": "tc"}.get(tag, "p"))
            self.children(element)
        elif tag in ("char", "note"):
            events.char_open(style)
            self.children(element)
            events.char_close(style)
        elif tag == "figure":
            events.char_open("fig")
            self.children(element)
            events.char_close("fig")
        else:
            # usx, table, ref, link and anything unknown: keep the text inside.
            self.children(element)

        if element.tail:
            events.text(element.tail)

    def children(self, element: ET.Element) -> None:
        if element.text:
            self.events.text(element.text)
        for child in element:
            self.walk(child)


def parse(path: Path) -> Bible:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        raise ParseError(f"{path}: not well-formed XML: {error}") from error
    if _local(root.tag) != "usx":
        raise ParseError(f"{path}: not a USX document (root element is <{_local(root.tag)}>, expected <usx>)")

    collector = VerseCollector()
    try:
        _Walker(MarkerEvents(collector)).children(root)
        bible = collector.finish()
    except ValueError as error:
        raise ParseError(f"{path}: {error}") from error
    return bible
