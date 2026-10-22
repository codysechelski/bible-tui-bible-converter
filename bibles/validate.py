"""Validate a Bible database against the rules of the reference project.

Every check runs and reports `pass`, `warn` or `fail`; a database is valid when no check fails.
Missing verses are warnings, because translations legitimately omit some verses (and verse ranges
leave the later verses absent). The reference totals are a sanity check only.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Sequence

from bibles.books import BOOKS, NEW_TESTAMENT, OLD_TESTAMENT, OLD_TESTAMENT_BOOK_COUNT

PASS, WARN, FAIL = "pass", "warn", "fail"

REQUIRED_TABLES = ("metadata", "books", "chapters", "verses")
REQUIRED_METADATA = (
    "version", "version_name", "source", "created_at_utc", "book_count", "chapter_count", "verse_count",
)
# Totals of the reference ESV database, used only as a sanity check.
REFERENCE_TOTALS = {"chapters": 1189, "verses": 31104}
# How many examples a check lists before summarizing the rest.
MAX_EXAMPLES = 8


def _plural(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str


@dataclass
class ValidationReport:
    path: Path
    checks: List[CheckResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(check.status != FAIL for check in self.checks)

    @property
    def failures(self) -> List[CheckResult]:
        return [check for check in self.checks if check.status == FAIL]

    @property
    def warnings(self) -> List[CheckResult]:
        return [check for check in self.checks if check.status == WARN]

    def lines(self) -> List[str]:
        lines = [f"  {check.status.upper():4}  {check.name}: {check.detail}" for check in self.checks]
        verdict = "passed" if self.ok else "FAILED"
        lines.append(
            f"Validation {verdict}: {_plural(len(self.checks), 'check')}, {len(self.failures)} failed, "
            f"{_plural(len(self.warnings), 'warning')}"
        )
        return lines


class DatabaseValidationError(Exception):
    """A database failed validation. `report` holds every check."""

    def __init__(self, report: ValidationReport) -> None:
        names = ", ".join(check.name for check in report.failures)
        super().__init__(f"database validation failed: {names}")
        self.report = report


def _examples(items: Sequence[str]) -> str:
    shown = ", ".join(items[:MAX_EXAMPLES])
    if len(items) > MAX_EXAMPLES:
        shown += f" and {len(items) - MAX_EXAMPLES} more"
    return shown


def _result(name: str, problems: Sequence[str], ok_detail: str, status: str = FAIL) -> CheckResult:
    if problems:
        return CheckResult(name, status, _examples(problems))
    return CheckResult(name, PASS, ok_detail)


def _integrity(conn: sqlite3.Connection) -> CheckResult:
    rows = [row[0] for row in conn.execute("PRAGMA integrity_check")]
    return _result("SQLite integrity", [] if rows == ["ok"] else rows, "ok")


def _foreign_keys(conn: sqlite3.Connection) -> CheckResult:
    rows = conn.execute("PRAGMA foreign_key_check").fetchall()
    return _result("Foreign keys", [f"{r[0]} row {r[1]} -> {r[2]}" for r in rows], "no violations")


def _metadata(conn: sqlite3.Connection) -> CheckResult:
    values = dict(conn.execute("SELECT key, value FROM metadata"))
    missing = [key for key in REQUIRED_METADATA if not str(values.get(key) or "").strip()]
    return _result("Metadata", [f"missing {key}" for key in missing],
                   f"{len(REQUIRED_METADATA)} required keys present")


def _books(conn: sqlite3.Connection) -> List[CheckResult]:
    rows = conn.execute(
        "SELECT sort_order, canonical_name, common_name, slug, testament FROM books ORDER BY sort_order"
    ).fetchall()
    expected = {book.sort_order: book for book in BOOKS}

    count = CheckResult("Book count", PASS, "66 books") if len(rows) == 66 else CheckResult(
        "Book count", FAIL, f"expected 66 books, found {len(rows)}"
    )

    orders = [row[0] for row in rows]
    order_problems = [] if orders == list(range(1, len(rows) + 1)) and len(rows) == 66 else [
        f"sort orders are {_examples([str(o) for o in orders]) or 'empty'}, expected 1..66"
    ]
    for order, canonical, common, slug, _ in rows:
        book = expected.get(order)
        if book is None:
            order_problems.append(f"unexpected sort order {order}")
        elif (canonical, common, slug) != (book.canonical_name, book.common_name, book.slug):
            order_problems.append(f"{order} is {canonical!r}/{common!r}/{slug!r}, expected {book.canonical_name!r}")
    order = _result("Book order and names", order_problems, "sort order 1..66 matches the canonical books")

    old = sum(1 for row in rows if row[4] == OLD_TESTAMENT)
    new = sum(1 for row in rows if row[4] == NEW_TESTAMENT)
    wrong = [row[1] for row in rows
             if row[4] != (OLD_TESTAMENT if row[0] <= OLD_TESTAMENT_BOOK_COUNT else NEW_TESTAMENT)]
    split_problems = [f"{name} has the wrong testament" for name in wrong]
    if (old, new) != (39, 27):
        split_problems.insert(0, f"{old} old / {new} new, expected 39 / 27")
    split = _result("Testament split", split_problems, "39 old, 27 new")
    return [count, order, split]


def _chapters(conn: sqlite3.Connection) -> List[CheckResult]:
    gaps: List[str] = []
    counts: List[str] = []
    empty: List[str] = []
    rows = conn.execute(
        "SELECT b.id, b.sort_order, b.common_name FROM books b ORDER BY b.sort_order"
    ).fetchall()
    for book_id, sort_order, name in rows:
        numbers = [r[0] for r in conn.execute(
            "SELECT chapter_number FROM chapters WHERE book_id = ? ORDER BY chapter_number", (book_id,))]
        if numbers != list(range(1, len(numbers) + 1)):
            gaps.append(f"{name} has chapters {_examples([str(n) for n in numbers])}")
        book = next((b for b in BOOKS if b.sort_order == sort_order), None)
        if book is not None and len(numbers) != book.chapter_count:
            counts.append(f"{name} has {len(numbers)} chapters, usually {book.chapter_count}")
    for name, number in conn.execute(
        "SELECT b.common_name, c.chapter_number FROM chapters c JOIN books b ON b.id = c.book_id "
        "WHERE NOT EXISTS (SELECT 1 FROM verses v WHERE v.chapter_id = c.id) ORDER BY b.sort_order, c.chapter_number"
    ):
        empty.append(f"{name} {number}")
    return [
        _result("Chapter numbering", gaps, "every book's chapters run from 1 with no gaps"),
        _result("Chapters with verses", empty, "every chapter has at least one verse"),
        # Versification differs between traditions (Joel has 4 chapters in Hebrew order), so a
        # different chapter count is only a warning.
        _result("Chapter counts", counts, "every book has its usual number of chapters", WARN),
    ]


def _verses(conn: sqlite3.Connection) -> List[CheckResult]:
    missing: List[str] = []
    current = None
    expected_next = 1
    for name, chapter, verse in conn.execute(
        "SELECT b.common_name, v.chapter_number, v.verse_number FROM verses v "
        "JOIN books b ON b.id = v.book_id ORDER BY b.sort_order, v.chapter_number, v.verse_number"
    ):
        if (name, chapter) != current:
            current, expected_next = (name, chapter), 1
        if verse > expected_next:
            span = str(expected_next) if verse - 1 == expected_next else f"{expected_next}-{verse - 1}"
            missing.append(f"{name} {chapter}:{span}")
        expected_next = max(expected_next, verse + 1)

    duplicates = [
        f"{name} {chapter}:{verse}" for name, chapter, verse in conn.execute(
            "SELECT b.common_name, v.chapter_number, v.verse_number FROM verses v JOIN books b ON b.id = v.book_id "
            "GROUP BY v.book_id, v.chapter_number, v.verse_number HAVING COUNT(*) > 1"
        )
    ]
    mismatched = [
        f"verse id {row[0]}" for row in conn.execute(
            "SELECT v.id FROM verses v JOIN chapters c ON c.id = v.chapter_id "
            "WHERE c.book_id != v.book_id OR c.chapter_number != v.chapter_number"
        )
    ]
    empty = [
        f"{name} {chapter}:{verse}" for name, chapter, verse in conn.execute(
            "SELECT b.common_name, v.chapter_number, v.verse_number FROM verses v JOIN books b ON b.id = v.book_id "
            "WHERE TRIM(v.text) = '' ORDER BY b.sort_order, v.chapter_number, v.verse_number"
        )
    ]
    return [
        # Translations omit some verses and verse ranges leave later verses absent, so gaps warn.
        _result("Verse numbering", [f"missing {m}" for m in missing],
                "every chapter's verses run from 1 with no gaps", WARN),
        _result("Duplicate references", duplicates, "no book, chapter and verse appears twice"),
        _result("Verse chapter links", mismatched, "every verse matches its chapter row"),
        _result("Empty verse text", empty, "every verse has text"),
    ]


def _totals(conn: sqlite3.Connection) -> CheckResult:
    chapters = conn.execute("SELECT COUNT(*) FROM chapters").fetchone()[0]
    verses = conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
    detail = (f"{chapters} chapters, {verses} verses (reference: {REFERENCE_TOTALS['chapters']} chapters, "
              f"{REFERENCE_TOTALS['verses']} verses)")
    same = (chapters, verses) == (REFERENCE_TOTALS["chapters"], REFERENCE_TOTALS["verses"])
    return CheckResult("Totals against reference", PASS if same else WARN, detail)


def validate_database(path: Path) -> ValidationReport:
    """Run every check on the database at `path` (opened read-only) and return the report."""
    report = ValidationReport(Path(path))
    if not Path(path).is_file():
        report.checks.append(CheckResult("Database file", FAIL, f"not found: {path}"))
        return report
    try:
        conn = sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro", uri=True)
    except sqlite3.Error as error:
        report.checks.append(CheckResult("Database file", FAIL, str(error)))
        return report
    try:
        try:
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        except sqlite3.DatabaseError as error:
            report.checks.append(CheckResult("Database file", FAIL, f"not a SQLite database: {error}"))
            return report
        missing = [name for name in REQUIRED_TABLES if name not in tables]
        report.checks.append(_result("Schema tables", [f"missing {name}" for name in missing],
                                     ", ".join(REQUIRED_TABLES)))
        if missing:
            return report

        steps: List[Callable[[sqlite3.Connection], object]] = [
            _integrity, _foreign_keys, _metadata, _books, _chapters, _verses, _totals,
        ]
        for step in steps:
            try:
                result = step(conn)
            except sqlite3.Error as error:
                result = CheckResult(step.__name__.strip("_").replace("_", " ").capitalize(), FAIL, str(error))
            report.checks.extend(result if isinstance(result, list) else [result])
        return report
    finally:
        conn.close()


def require_valid(path: Path) -> ValidationReport:
    """Validate `path` and raise `DatabaseValidationError` when any check fails."""
    report = validate_database(path)
    if not report.ok:
        raise DatabaseValidationError(report)
    return report

