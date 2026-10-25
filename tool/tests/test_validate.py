from __future__ import annotations

import contextlib
import io
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bibles.books import BOOKS
from bibles.cli import main
from bibles.model import Bible
from bibles.validate import FAIL, PASS, WARN, DatabaseValidationError, require_valid, validate_database
from bibles.writer import write_database

REFERENCE_DB = Path("/Users/codysechelski/Developer/Projects/bible-esv/bible_esv.sqlite")
SOURCE = Path("full.usfm")


def full_bible() -> Bible:
    """Every chapter of all 66 books, with three verses each."""
    bible = Bible()
    for book in BOOKS:
        for chapter in range(1, book.chapter_count + 1):
            for verse in (1, 2, 3):
                bible.add_verse(book.usfm_code, chapter, verse, f"{book.common_name} {chapter}:{verse}.")
    return bible


class ValidateTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._class_tmp = tempfile.TemporaryDirectory()
        cls.template = Path(cls._class_tmp.name) / "full.sqlite"
        write_database(full_bible(), cls.template, SOURCE, "usfm")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._class_tmp.cleanup()

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.db = self.tmp / "bible.sqlite"
        self.db.write_bytes(self.template.read_bytes())

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def execute(self, *statements: str) -> None:
        conn = sqlite3.connect(self.db)
        try:
            for statement in statements:
                conn.execute(statement)
            conn.commit()
        finally:
            conn.close()

    def status(self, name: str) -> tuple:
        report = validate_database(self.db)
        check = next(c for c in report.checks if c.name == name)
        return check.status, check.detail, report.ok


class ValidDatabaseTests(ValidateTestCase):
    def test_full_bible_passes_and_lists_every_check(self) -> None:
        report = validate_database(self.db)
        self.assertTrue(report.ok)
        self.assertEqual([c.name for c in report.checks], [
            "Schema tables", "SQLite integrity", "Foreign keys", "Metadata", "Book count",
            "Book order and names", "Testament split", "Chapter numbering", "Chapters with verses",
            "Chapter counts", "Verse numbering", "Duplicate references", "Verse chapter links",
            "Empty verse text", "Totals against reference",
        ])
        statuses = {c.name: c.status for c in report.checks}
        self.assertEqual(statuses.pop("Totals against reference"), WARN)  # 3 verses per chapter
        self.assertEqual(set(statuses.values()), {PASS})
        lines = report.lines()
        self.assertEqual(len(lines), 16)
        self.assertTrue(lines[0].startswith("  PASS  Schema tables"))
        self.assertEqual(lines[-1], "Validation passed: 15 checks, 0 failed, 1 warning")

    @unittest.skipUnless(REFERENCE_DB.is_file(), "reference database not found")
    def test_reference_database_passes_without_warnings(self) -> None:
        report = validate_database(REFERENCE_DB)
        self.assertTrue(report.ok)
        self.assertEqual(report.warnings, [])


class WarningTests(ValidateTestCase):
    def test_omitted_verses_are_warnings(self) -> None:
        self.execute("DELETE FROM verses WHERE book_id = 44 AND chapter_number = 8 AND verse_number = 2",
                     "DELETE FROM verses WHERE book_id = 1 AND chapter_number = 1 AND verse_number IN (1, 2)")
        status, detail, ok = self.status("Verse numbering")
        self.assertEqual(status, WARN)
        self.assertEqual(detail, "missing Genesis 1:1-2, missing Acts 8:2")
        self.assertTrue(ok)

    def test_unusual_chapter_count_is_a_warning(self) -> None:
        self.execute("DELETE FROM verses WHERE book_id = 39 AND chapter_number = 4",
                     "DELETE FROM chapters WHERE book_id = 39 AND chapter_number = 4")
        status, detail, ok = self.status("Chapter counts")
        self.assertEqual((status, detail, ok), (WARN, "Malachi has 3 chapters, usually 4", True))

    def test_translated_common_names_pass(self) -> None:
        self.execute("UPDATE books SET common_name = 'Gênesis' WHERE id = 1",
                     "UPDATE books SET common_name = 'Êxodo' WHERE id = 2")
        status, detail, ok = self.status("Book order and names")
        self.assertEqual(status, PASS)
        self.assertIn("2 books use the translation's own names", detail)
        self.assertTrue(ok)

    def test_long_lists_are_summarized(self) -> None:
        self.execute("DELETE FROM verses WHERE verse_number = 2 AND book_id = 19")
        _, detail, _ = self.status("Verse numbering")
        self.assertTrue(detail.endswith("and 142 more"), detail)


class FailureTests(ValidateTestCase):
    def assert_fails(self, name: str, detail_part: str) -> None:
        status, detail, ok = self.status(name)
        self.assertEqual(status, FAIL, detail)
        self.assertIn(detail_part, detail)
        self.assertFalse(ok)

    def test_missing_book(self) -> None:
        self.execute("DELETE FROM books WHERE id = 66")
        self.assert_fails("Book count", "expected 66 books, found 65")
        self.assert_fails("Book order and names", "expected 1..66")

    def test_wrong_testament(self) -> None:
        self.execute("UPDATE books SET testament = 'new' WHERE id = 39")
        self.assert_fails("Testament split", "38 old / 28 new")
        self.assert_fails("Testament split", "Malachi has the wrong testament")

    def test_wrong_book_names(self) -> None:
        self.execute("UPDATE books SET slug = 'gen' WHERE id = 1")
        self.assert_fails("Book order and names", "'gen'")

    def test_blank_common_name(self) -> None:
        self.execute("UPDATE books SET common_name = ' ' WHERE id = 1")
        self.assert_fails("Book order and names", "1 (Genesis) has no common name")

    def test_wrong_canonical_name_with_a_translated_common_name(self) -> None:
        self.execute("UPDATE books SET canonical_name = 'Gênesis', common_name = 'Gênesis' WHERE id = 1")
        self.assert_fails("Book order and names", "'Gênesis'")

    def test_chapter_gap(self) -> None:
        self.execute("DELETE FROM chapters WHERE book_id = 1 AND chapter_number = 2")
        self.assert_fails("Chapter numbering", "Genesis has chapters 1, 3, 4")

    def test_chapter_without_verses(self) -> None:
        self.execute("DELETE FROM verses WHERE book_id = 43 AND chapter_number = 11")
        self.assert_fails("Chapters with verses", "John 11")

    def test_empty_verse_text(self) -> None:
        self.execute("UPDATE verses SET text = '  ' WHERE book_id = 43 AND chapter_number = 11 AND verse_number = 3")
        self.assert_fails("Empty verse text", "John 11:3")

    def test_duplicate_reference(self) -> None:
        # The schema forbids duplicates, so build a copy without the unique constraint.
        self.execute(
            "CREATE TABLE verses2 (id INTEGER PRIMARY KEY, book_id INTEGER NOT NULL REFERENCES books(id), "
            "chapter_id INTEGER NOT NULL REFERENCES chapters(id), chapter_number INTEGER NOT NULL, "
            "verse_number INTEGER NOT NULL, text TEXT NOT NULL)",
            "INSERT INTO verses2 SELECT * FROM verses",
            "INSERT INTO verses2 (book_id, chapter_id, chapter_number, verse_number, text) "
            "SELECT book_id, chapter_id, chapter_number, verse_number, text FROM verses WHERE id = 1",
            "DROP TABLE verses", "ALTER TABLE verses2 RENAME TO verses",
        )
        self.assert_fails("Duplicate references", "Genesis 1:1")

    def test_verse_linked_to_wrong_chapter(self) -> None:
        self.execute("UPDATE verses SET chapter_number = 2, verse_number = 99 WHERE id = 1")
        self.assert_fails("Verse chapter links", "verse id 1")

    def test_foreign_key_violation(self) -> None:
        self.execute("PRAGMA foreign_keys = OFF", "UPDATE verses SET chapter_id = 999999 WHERE id = 1")
        self.assert_fails("Foreign keys", "verses row 1 -> chapters")

    def test_missing_metadata(self) -> None:
        self.execute("DELETE FROM metadata WHERE key = 'version'", "UPDATE metadata SET value = '' WHERE key = 'source'")
        self.assert_fails("Metadata", "missing version, missing source")

    def test_missing_table_stops_early(self) -> None:
        self.execute("DROP TABLE metadata")
        report = validate_database(self.db)
        self.assertEqual([(c.name, c.status) for c in report.checks], [("Schema tables", FAIL)])

    def test_not_a_database_and_missing_file(self) -> None:
        not_db = self.tmp / "notes.sqlite"
        not_db.write_text("hello")
        self.assertEqual(validate_database(not_db).checks[0].status, FAIL)
        self.assertIn("not found", validate_database(self.tmp / "missing.sqlite").checks[0].detail)

    def test_require_valid(self) -> None:
        self.execute("DELETE FROM books WHERE id = 66")
        with self.assertRaisesRegex(DatabaseValidationError, "Book count") as caught:
            require_valid(self.db)
        self.assertFalse(caught.exception.report.ok)


class WriterIntegrationTests(ValidateTestCase):
    def test_conversion_runs_validation(self) -> None:
        output = self.tmp / "out.sqlite"
        result = write_database(full_bible(), output, SOURCE)
        self.assertTrue(result.validation.ok)
        self.assertEqual(result.validation.path, output)

    def test_invalid_conversion_leaves_no_database(self) -> None:
        bible = Bible()
        bible.add_verse("GEN", 1, 1, "In the beginning.")
        output = self.tmp / "partial.sqlite"
        with self.assertRaises(DatabaseValidationError) as caught:
            write_database(bible, output, SOURCE)
        self.assertIn("Book count", str(caught.exception))
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), ["bible.sqlite"])


class ValidateCommandTests(ValidateTestCase):
    def run_cli(self, *argv: str) -> tuple:
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                code = main(list(argv))
            except SystemExit as exit_:
                code = exit_.code
        return code, stdout.getvalue(), stderr.getvalue()

    def test_valid_database_exits_zero_and_lists_checks(self) -> None:
        code, out, _ = self.run_cli("--validate", str(self.db))
        self.assertEqual(code, 0)
        self.assertIn(f"Validating: {self.db}", out)
        self.assertIn("PASS  SQLite integrity: ok", out)
        self.assertIn("Validation passed: 15 checks", out)
        self.assertEqual(out.count("\n"), 17)

    def test_invalid_database_exits_one(self) -> None:
        self.execute("DELETE FROM books WHERE id = 66")
        code, out, _ = self.run_cli("--validate", str(self.db))
        self.assertEqual(code, 1)
        self.assertIn("FAIL  Book count: expected 66 books, found 65", out)
        self.assertIn("Validation FAILED", out)

    def test_validate_does_not_write_anything(self) -> None:
        before = self.db.read_bytes()
        self.run_cli("--validate", str(self.db))
        self.assertEqual(self.db.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), ["bible.sqlite"])

    def test_validate_rejects_conversion_options(self) -> None:
        code, _, err = self.run_cli("--validate", str(self.db), "--format", "usfm")
        self.assertEqual(code, 2)
        self.assertIn("cannot be combined", err)


if __name__ == "__main__":
    unittest.main()
