"""One parser per supported format. Each `parse(path)` returns a normalized `Bible`."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict

from bibles.model import Bible
from bibles.parsers import osis, usfm, usj, usx, vpl
from bibles.parsers.base import ParseError

PARSERS: Dict[str, Callable[[Path], Bible]] = {
    "usfm": usfm.parse,
    "usx": usx.parse,
    "osis": osis.parse,
    "vpl": vpl.parse,
    "usj": usj.parse,
}


def parse_file(path: Path, source_format: str) -> Bible:
    """Parse `path` as `source_format`, raising `ParseError` on failure or when no verse is found."""
    parser = PARSERS.get(source_format)
    if parser is None:
        raise ParseError(f"no parser for format {source_format!r}")
    try:
        bible = parser(path)
    except OSError as error:
        raise ParseError(f"cannot read {path}: {error.strerror or error}") from error
    if not bible.books:
        raise ParseError(f"{path}: no verses found")
    return bible


__all__ = ["PARSERS", "ParseError", "parse_file"]
