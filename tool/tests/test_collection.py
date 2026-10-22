"""Checks the converted databases committed in bibles/ (see "Converted Bibles" in the README)."""

from __future__ import annotations

import sqlite3
import unittest
from contextlib import closing
from pathlib import Path

from bibles.validate import validate_database
from tests.test_writer import REFERENCE_DB, schema_description

REPO_ROOT = Path(__file__).resolve().parents[2]
README = REPO_ROOT / "README.md"
COLLECTION_DIR = REPO_ROOT / "bibles"

# Every committed database: its version and verse count, as converted from the source recorded in the README.
COLLECTION = {
    "bible_kjv.sqlite": ("KJV", 31102),
    "bible_asv.sqlite": ("ASV", 31086),
}


class CollectionTests(unittest.TestCase):
    def test_every_database_in_the_collection_is_listed(self) -> None:
        self.assertEqual(sorted(path.name for path in COLLECTION_DIR.glob("*.sqlite")), sorted(COLLECTION))

    def test_every_database_is_recorded_in_the_readme(self) -> None:
        readme = README.read_text(encoding="utf-8")
        for name in COLLECTION:
            with self.subTest(database=name):
                self.assertTrue(f"`bibles/{name}`" in readme, f"{name} is not listed in README.md")

    def test_every_database_validates(self) -> None:
        for name in COLLECTION:
            with self.subTest(database=name):
                report = validate_database(COLLECTION_DIR / name)
                self.assertTrue(report.ok, "\n".join(report.lines()))

    @unittest.skipUnless(REFERENCE_DB.is_file(), "reference database not found")
    def test_schema_matches_reference(self) -> None:
        expected = schema_description(REFERENCE_DB)
        for name in COLLECTION:
            with self.subTest(database=name):
                self.assertEqual(schema_description(COLLECTION_DIR / name), expected)

    def test_version_and_counts(self) -> None:
        for name, (version, verses) in COLLECTION.items():
            with self.subTest(database=name):
                with closing(sqlite3.connect(f"file:{COLLECTION_DIR / name}?mode=ro", uri=True)) as conn:
                    metadata = dict(conn.execute("SELECT key, value FROM metadata"))
                    self.assertEqual(metadata["version"], version)
                    self.assertEqual(conn.execute("SELECT COUNT(*) FROM books").fetchone()[0], 66)
                    self.assertEqual(conn.execute("SELECT COUNT(*) FROM chapters").fetchone()[0], 1189)
                    self.assertEqual(conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0], verses)


if __name__ == "__main__":
    unittest.main()
