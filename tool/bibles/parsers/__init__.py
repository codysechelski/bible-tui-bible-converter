"""One parser per supported format. Each `parse(path)` returns a normalized `Bible`."""

from __future__ import annotations

import posixpath
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple

from bibles.model import Bible, BibleBook
from bibles.parsers import osis, rtf, usfm, usj, usx, vpl
from bibles.parsers.base import ParseError

PARSERS: Dict[str, Callable[[Path], Bible]] = {
    "usfm": usfm.parse,
    "usx": usx.parse,
    "osis": osis.parse,
    "vpl": vpl.parse,
    "usj": usj.parse,
    "rtf": rtf.parse,
}
# How many book codes a warning about repeated books lists before summarizing.
_MAX_LISTED_BOOKS = 5


def _parse(path: Path, source_format: str) -> Bible:
    parser = PARSERS.get(source_format)
    if parser is None:
        raise ParseError(f"no parser for format {source_format!r}")
    try:
        return parser(path)
    except OSError as error:
        raise ParseError(f"cannot read {path}: {error.strerror or error}") from error


def parse_file(path: Path, source_format: str) -> Bible:
    """Parse `path` as `source_format`, raising `ParseError` on failure or when no verse is found."""
    bible = _parse(path, source_format)
    if not bible.books:
        raise ParseError(f"{path}: no verses found")
    return bible


def _verse_texts(bible_book: BibleBook) -> List[Tuple[int, int, str]]:
    return [(chapter.number, verse.verse_number, verse.text)
            for chapter in bible_book.chapters for verse in chapter.verses]


def parse_files(files: Sequence[Tuple[Path, str]], source_format: str) -> Bible:
    """Parse several files, given as (path, display name) pairs, into one `Bible`.

    Books are kept in file order. A file may hold no canonical book (an Apocrypha book, say). A book
    found again in a later file with identical text is skipped with a warning; one whose copies
    differ raises `ParseError`, as does finding no verse in any file. Errors name the file by its
    display name.
    """
    merged = Bible()
    origins: Dict[str, str] = {}
    # (folder kept, folder skipped) -> book codes that the second folder repeats.
    repeats: Dict[Tuple[str, str], List[str]] = {}
    for path, name in files:
        try:
            bible = _parse(path, source_format)
        except ParseError as error:
            raise ParseError(str(error).replace(str(path), name)) from error
        merged.version = merged.version or bible.version
        merged.version_name = merged.version_name or bible.version_name
        merged.language = merged.language or bible.language
        merged.warnings.extend(w for w in bible.warnings if w not in merged.warnings)
        for bible_book in bible.books:
            first = origins.get(bible_book.code)
            if first is None:
                merged.add_book(bible_book)
                origins[bible_book.code] = name
                continue
            existing = merged.book(bible_book.code)
            assert existing is not None
            if _verse_texts(existing) != _verse_texts(bible_book):
                raise ParseError(f"{bible_book.code} is in both {first} and {name}, and the copies differ")
            folders = (posixpath.dirname(first) or ".", posixpath.dirname(name) or ".")
            repeats.setdefault(folders, []).append(bible_book.code)

    for (kept, skipped), codes in repeats.items():
        listed = ", ".join(codes[:_MAX_LISTED_BOOKS]) + (", ..." if len(codes) > _MAX_LISTED_BOOKS else "")
        if len(codes) == 1:
            summary = f"1 book in {skipped} repeats {kept} with identical text and was skipped"
        else:
            summary = f"{len(codes)} books in {skipped} repeat {kept} with identical text and were skipped"
        merged.warnings.append(f"{summary} ({listed})")
    if not merged.books:
        raise ParseError(f"no verses found in any of the {len(files)} {source_format} files")
    return merged


__all__ = ["PARSERS", "ParseError", "parse_file", "parse_files"]
