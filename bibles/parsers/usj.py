"""USJ parser: walks the JSON tree and feeds the shared marker events."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bibles.model import Bible
from bibles.parsers.base import ParseError, VerseCollector
from bibles.parsers.markers import MarkerEvents

# Node types skipped together with their content.
_SKIPPED = frozenset({"sidebar", "periph", "optbreak", "ms"})


def _marker(node: dict) -> str:
    return str(node.get("marker") or node.get("mark") or "")


class _Walker:
    def __init__(self, events: MarkerEvents) -> None:
        self.events = events

    def walk(self, node: Any) -> None:
        events = self.events
        if isinstance(node, str):
            events.text(node)
            return
        if not isinstance(node, dict):
            raise ValueError(f"unexpected USJ content {node!r}")

        kind = str(node.get("type", ""))
        marker = _marker(node)
        if kind == "book" or marker == "id":
            events.book(str(node.get("code", "")))
        elif kind == "chapter" or marker == "c":
            events.chapter(str(node.get("number", "")))
        elif kind == "verse" or marker == "v":
            events.verse(str(node.get("number", "")))
        elif kind in _SKIPPED:
            pass
        elif kind in ("para", "table:row", "table:cell"):
            events.para(marker or {"table:row": "tr", "table:cell": "tc"}.get(kind, "p"))
            self.content(node)
        elif kind in ("char", "note"):
            events.char_open(marker)
            self.content(node)
            events.char_close(marker)
        elif kind == "figure":
            events.char_open("fig")
            self.content(node)
            events.char_close("fig")
        else:
            # table, ref and anything unknown: keep the text inside.
            self.content(node)

    def content(self, node: dict) -> None:
        for child in node.get("content") or []:
            self.walk(child)


def parse(path: Path) -> Bible:
    try:
        with path.open(encoding="utf-8-sig") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise ParseError(
            f"{path}: malformed JSON at line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error
    except UnicodeDecodeError as error:
        raise ParseError(f"{path}: USJ must be UTF-8: {error}") from error
    if not isinstance(data, dict) or str(data.get("type", "")).upper() != "USJ":
        raise ParseError(f'{path}: not a USJ document (expected a JSON object with "type": "USJ")')

    collector = VerseCollector()
    try:
        _Walker(MarkerEvents(collector)).content(data)
        bible = collector.finish()
    except ValueError as error:
        raise ParseError(f"{path}: {error}") from error
    return bible
