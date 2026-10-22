from __future__ import annotations

import re
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from bibles import writer
from bibles.model import Bible
from bibles.writer import DatabaseWriteError, build_metadata, write_database

REFERENCE_DB = Path("/Users/codysechelski/Developer/Projects/bible-esv/bible_esv.sqlite")
SOURCE = Path("sources/kjv.usfm")
FIXED_TIME = datetime(2026, 10, 22, 14, 30, 5, tzinfo=timezone.utc)
METADATA_KEYS = (
    "version", "version_name", "source", "created_at_utc", "book_count", "chapter_count", "verse_count",
)


def sample_bible() -> Bible:
    bible = Bible()
    # Added out of canonical order on purpose.
    bible.add_verse("JHN", 1, 2, "He was in the beginning with God.")
    bible.add_verse("JHN", 1, 1, "In the beginning was the Word.")
    bible.add_verse("GEN", 2, 1, "Thus the heavens and the earth were finished.")
    bible.add_verse("GEN", 1, 1, "In the beginning, God created the heavens and the earth.")
    bible.add_verse("GEN", 1, 2, "The earth was without form and void.")
    return bible


def schema_description(path: Path) -> dict:
    """Everything about the schema that the TUI could depend on."""
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        objects = conn.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
        ).fetchall()
        description: dict = {
            "objects": [(t, n, tbl, re.sub(r"\s+", " ", sql).strip()) for t, n, tbl, sql in objects],
        }
        for _, name, _, _ in objects:
            if _ == "table":
                description[f"columns:{name}"] = conn.execute(f"PRAGMA table_info({name})").fetchall()
                description[f"fks:{name}"] = conn.execute(f"PRAGMA foreign_key_list({name})").fetchall()
                indexes = conn.execute(f"PRAGMA index_list({name})").fetchall()
                description[f"indexes:{name}"] = [
                    (idx[1:], conn.execute(f"PRAGMA index_info({idx[1]})").fetchall()) for idx in indexes
                ]
        return description
    finally:
        conn.close()


class WriterTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.output = self.tmp / "out.sqlite"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, bible: Bible) -> sqlite3.Connection:
        write_database(bible, self.output, SOURCE, "usfm", FIXED_TIME)
        conn = sqlite3.connect(self.output)
        self.addCleanup(conn.close)
        return conn


@unittest.skipUnless(REFERENCE_DB.is_file(), f"reference database not found: {REFERENCE_DB}")
class ReferenceSchemaTests(WriterTestCase):
    def test_schema_matches_reference_database(self) -> None:
        self.write(sample_bible()).close()
        self.assertEqual(schema_description(self.output), schema_description(REFERENCE_DB))


class WriteDatabaseTests(WriterTestCase):
    def test_schema_has_four_tables_and_four_indexes(self) -> None:
        conn = self.write(sample_bible())
        names = dict(conn.execute(
            "SELECT name, type FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
        ).fetchall())
        self.assertEqual(sorted(n for n, t in names.items() if t == "table"),
                         ["books", "chapters", "metadata", "verses"])
        self.assertEqual(sorted(n for n, t in names.items() if t == "index"), [
            "idx_books_testament_order", "idx_chapters_book_number",
            "idx_verses_book_chapter_verse", "idx_verses_chapter_number",
        ])

    def test_foreign_keys_hold(self) -> None:
        conn = self.write(sample_bible())
        self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_books_written_in_canonical_order_from_reference_data(self) -> None:
        conn = self.write(sample_bible())
        self.assertEqual(
            conn.execute("SELECT id, sort_order, canonical_name, common_name, slug, testament "
                         "FROM books ORDER BY id").fetchall(),
            [(1, 1, "Genesis", "Genesis", "genesis", "old"), (43, 43, "John", "John", "john", "new")],
        )

    def test_chapters_and_verses(self) -> None:
        conn = self.write(sample_bible())
        self.assertEqual(
            conn.execute("SELECT book_id, chapter_number FROM chapters ORDER BY id").fetchall(),
            [(1, 1), (1, 2), (43, 1)],
        )
        rows = conn.execute(
            "SELECT v.book_id, v.chapter_id, c.id, v.chapter_number, c.chapter_number, v.verse_number, v.text "
            "FROM verses v JOIN chapters c ON c.id = v.chapter_id ORDER BY v.id"
        ).fetchall()
        self.assertEqual([(r[0], r[3], r[5]) for r in rows],
                         [(1, 1, 1), (1, 1, 2), (1, 2, 1), (43, 1, 1), (43, 1, 2)])
        for row in rows:
            self.assertEqual(row[1], row[2])
            self.assertEqual(row[3], row[4])
        self.assertEqual(rows[0][6], "In the beginning, God created the heavens and the earth.")

    def test_duplicate_verse_rejected_by_schema(self) -> None:
        conn = self.write(sample_bible())
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO verses (book_id, chapter_id, chapter_number, verse_number, text) "
                         "VALUES (1, 1, 1, 1, 'again')")

    def test_metadata(self) -> None:
        conn = self.write(sample_bible())
        metadata = dict(conn.execute("SELECT key, value FROM metadata").fetchall())
        for key in METADATA_KEYS:
            self.assertTrue(metadata.get(key), key)
        self.assertEqual(metadata["version"], "kjv")
        self.assertEqual(metadata["version_name"], "kjv")
        self.assertEqual(metadata["source"], "kjv.usfm (usfm)")
        self.assertEqual(metadata["created_at_utc"], "2026-10-22T14:30:05+00:00")
        self.assertEqual((metadata["book_count"], metadata["chapter_count"], metadata["verse_count"]),
                         ("2", "3", "5"))

    def test_overwrites_existing_file(self) -> None:
        self.output.write_text("old content")
        conn = self.write(sample_bible())
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM verses").fetchone(), (5,))


class MetadataTests(unittest.TestCase):
    def test_version_from_source_format(self) -> None:
        bible = sample_bible()
        bible.version, bible.version_name = "KJV", "King James Version"
        metadata = build_metadata(bible, SOURCE, None, FIXED_TIME)
        self.assertEqual((metadata["version"], metadata["version_name"], metadata["source"]),
                         ("KJV", "King James Version", "kjv.usfm"))

    def test_version_name_falls_back_to_version(self) -> None:
        bible = sample_bible()
        bible.version, bible.version_name = " WEB ", "  "
        metadata = build_metadata(bible, SOURCE, None, FIXED_TIME)
        self.assertEqual((metadata["version"], metadata["version_name"]), ("WEB", "WEB"))

    def test_created_at_is_converted_to_utc(self) -> None:
        from datetime import timedelta
        local = datetime(2026, 10, 22, 9, 30, 5, tzinfo=timezone(timedelta(hours=-5)))
        self.assertEqual(build_metadata(sample_bible(), SOURCE, None, local)["created_at_utc"],
                         "2026-10-22T14:30:05+00:00")


class FailureTests(WriterTestCase):
    def assert_nothing_left_behind(self) -> None:
        self.assertEqual(list(self.tmp.iterdir()), [])

    def test_empty_bible(self) -> None:
        with self.assertRaisesRegex(DatabaseWriteError, "no verses"):
            write_database(Bible(), self.output, SOURCE)
        self.assert_nothing_left_behind()

    def test_chapter_gap(self) -> None:
        bible = sample_bible()
        bible.add_verse("GEN", 4, 1, "Now Adam knew Eve his wife.")
        with self.assertRaisesRegex(DatabaseWriteError, r"GEN chapters .* missing \[3\]"):
            write_database(bible, self.output, SOURCE)
        self.assert_nothing_left_behind()

    def test_failure_mid_write_removes_temp_file_and_keeps_existing_output(self) -> None:
        self.output.write_text("previous database")
        with mock.patch.object(writer, "SCHEMA", writer.SCHEMA + "\nCREATE TABLE books (x);"):
            with self.assertRaises(DatabaseWriteError):
                write_database(sample_bible(), self.output, SOURCE)
        self.assertEqual(list(self.tmp.iterdir()), [self.output])
        self.assertEqual(self.output.read_text(), "previous database")


if __name__ == "__main__":
    unittest.main()
