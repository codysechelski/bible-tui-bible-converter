"""Write a `Bible` to a SQLite database using the reference project's schema."""

from __future__ import annotations

import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from bibles.model import Bible, BibleBook
from bibles.validate import DatabaseValidationError, ValidationReport, validate_database

# Copied from bible-esv/tools/build_sqlite.py. The TUI depends on it, so it must not drift; the
# schema test compares it with the reference database.
SCHEMA = """
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE books (
    id INTEGER PRIMARY KEY,
    sort_order INTEGER NOT NULL UNIQUE,
    canonical_name TEXT NOT NULL UNIQUE,
    common_name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    testament TEXT NOT NULL CHECK (testament IN ('old', 'new'))
);

CREATE TABLE chapters (
    id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    chapter_number INTEGER NOT NULL,
    UNIQUE (book_id, chapter_number)
);

CREATE TABLE verses (
    id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    chapter_id INTEGER NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    chapter_number INTEGER NOT NULL,
    verse_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    UNIQUE (book_id, chapter_number, verse_number)
);

CREATE INDEX idx_books_testament_order ON books(testament, sort_order);
CREATE INDEX idx_chapters_book_number ON chapters(book_id, chapter_number);
CREATE INDEX idx_verses_book_chapter_verse ON verses(book_id, chapter_number, verse_number);
CREATE INDEX idx_verses_chapter_number ON verses(chapter_id, verse_number);
"""


class DatabaseWriteError(Exception):
    """The Bible cannot be written as a valid database."""


@dataclass(frozen=True)
class WriteResult:
    metadata: Dict[str, str]
    validation: Optional[ValidationReport]


def build_metadata(
    bible: Bible,
    source: Path,
    source_format: Optional[str] = None,
    created_at: Optional[datetime] = None,
) -> Dict[str, str]:
    """Return the metadata rows. Missing version values fall back to the source file name."""
    version = (bible.version or "").strip() or source.stem
    version_name = (bible.version_name or "").strip() or version
    source_value = source.name if source_format is None else f"{source.name} ({source_format})"
    created = created_at if created_at is not None else datetime.now(timezone.utc)
    return {
        "version": version,
        "version_name": version_name,
        "source": source_value,
        "created_at_utc": created.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "book_count": str(len(bible.books)),
        "chapter_count": str(sum(len(b.chapters) for b in bible.books)),
        "verse_count": str(sum(1 for _ in bible.verses())),
    }


def _ordered_books(bible: Bible) -> List[BibleBook]:
    if not bible.books:
        raise DatabaseWriteError("the source contains no verses")
    books = sorted(bible.books, key=lambda b: b.book.sort_order)
    for bible_book in books:
        numbers = sorted(chapter.number for chapter in bible_book.chapters)
        if numbers != list(range(1, len(numbers) + 1)):
            missing = sorted(set(range(1, max(numbers) + 1)) - set(numbers))
            raise DatabaseWriteError(
                f"{bible_book.code} chapters must be numbered from 1 with no gaps; missing {missing}"
            )
    return books


def _write_rows(conn: sqlite3.Connection, books: List[BibleBook], metadata: Dict[str, str]) -> None:
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    with conn:
        for bible_book in books:
            book = bible_book.book
            # The book id is its sort order, as in the reference database.
            conn.execute(
                "INSERT INTO books (id, sort_order, canonical_name, common_name, slug, testament) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (book.sort_order, book.sort_order, book.canonical_name, bible_book.common_name, book.slug,
                 book.testament),
            )
            for chapter in sorted(bible_book.chapters, key=lambda c: c.number):
                chapter_id = conn.execute(
                    "INSERT INTO chapters (book_id, chapter_number) VALUES (?, ?)",
                    (book.sort_order, chapter.number),
                ).lastrowid
                rows: List[Tuple[int, int, int, int, str]] = [
                    (book.sort_order, chapter_id, chapter.number, verse.verse_number, verse.text)
                    for verse in sorted(chapter.verses, key=lambda v: v.verse_number)
                ]
                conn.executemany(
                    "INSERT INTO verses (book_id, chapter_id, chapter_number, verse_number, text) "
                    "VALUES (?, ?, ?, ?, ?)",
                    rows,
                )
        conn.executemany("INSERT INTO metadata (key, value) VALUES (?, ?)", metadata.items())

    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        raise DatabaseWriteError(f"foreign key check failed: {violations[:5]}")


def write_database(
    bible: Bible,
    output: Path,
    source: Path,
    source_format: Optional[str] = None,
    created_at: Optional[datetime] = None,
    validate: bool = True,
    allow_partial: bool = False,
) -> WriteResult:
    """Write `bible` to `output`, replacing any existing file.

    The database is built in a temporary file beside `output`, validated (unless `validate` is
    False; `allow_partial` accepts fewer than 66 books), and moved into place only when it is complete and valid, so a failure never leaves a
    partial, empty or invalid database at `output`. A failed validation raises
    `DatabaseValidationError`, whose `report` lists every check.
    """
    books = _ordered_books(bible)
    metadata = build_metadata(bible, source, source_format, created_at)

    output = Path(output)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent)
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        conn = sqlite3.connect(tmp_path)
        try:
            _write_rows(conn, books, metadata)
        except sqlite3.Error as error:
            raise DatabaseWriteError(str(error)) from error
        finally:
            conn.close()
        report = validate_database(tmp_path, allow_partial) if validate else None
        if report is not None:
            report.path = output
            if not report.ok:
                raise DatabaseValidationError(report)
        os.replace(tmp_path, output)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise
    return WriteResult(metadata, report)
