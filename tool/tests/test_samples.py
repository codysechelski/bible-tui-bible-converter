"""End-to-end tests over the real samples in `samples/`: Ruth, Jonah and 3 John of the KJV in five formats,
and of the ASV as RTF files."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from bibles.cli import main
from tests.test_writer import REFERENCE_DB, schema_description

TOOL_ROOT = Path(__file__).resolve().parents[1]
SAMPLES = TOOL_ROOT / "samples"
RTF_SAMPLES = SAMPLES / "asv-rtf"
REFERENCE_TUI = REFERENCE_DB.parent / "tui" / "bible_tui.py"

SAMPLE_FILES = {
    "usfm": "kjv.usfm",
    "usx": "kjv.usx",
    "osis": "kjv.osis.xml",
    "vpl": "kjv.vpl.txt",
    "usj": "kjv.usj",
}
# Book rows and the verse count of each chapter, for every sample.
EXPECTED_BOOKS = [
    (8, "Ruth", "Ruth", "ruth", "old"),
    (32, "Jonah", "Jonah", "jonah", "old"),
    (64, "III John", "3 John", "3-john", "new"),
]
EXPECTED_CHAPTERS = {
    "ruth": [22, 23, 18, 22],
    "jonah": [17, 10, 10, 11],
    "3-john": [14],
}
# USFM, USX and USJ come from the same source text. The OSIS file is eBible's own export of a
# slightly different KJV edition, and eBible's VPL marks added words with brackets.
RUTH_1_2 = {
    "usfm": "And the name of the man was Elimelech, and the name of his wife Naomi, and the name of his two "
            "sons Mahlon and Chilion, Ephrathites of Beth-lehem-judah. And they came into the country of Moab, "
            "and continued there.",
    "osis": "And the name of the man was Elimelech, and the name of his wife Naomi, and the name of his two "
            "sons Mahlon and Chilion, Ephrathites of Bethlehemjudah. And they came into the country of Moab, "
            "and continued there.",
    "vpl": "And the name of the man [was] Elimelech, and the name of his wife Naomi, and the name of his two "
           "sons Mahlon and Chilion, Ephrathites of Beth-lehem-judah. And they came into the country of Moab, "
           "and continued there.",
}
RUTH_1_2["usx"] = RUTH_1_2["usj"] = RUTH_1_2["usfm"]
JOHN3_14 = {
    "usfm": "But I trust I shall shortly see thee, and we shall speak face to face. Peace be to thee. Our "
            "friends salute thee. Greet the friends by name.",
}
JOHN3_14["usx"] = JOHN3_14["usj"] = JOHN3_14["osis"] = JOHN3_14["usfm"]
JOHN3_14["vpl"] = ("But I trust I shall shortly see thee, and we shall speak face to face. Peace [be] to thee. "
                   "[Our] friends salute thee. Greet the friends by name.")


def run_cli(*argv: str) -> tuple:
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            code = main(list(argv))
        except SystemExit as exit_:
            code = exit_.code
    return code, stdout.getvalue(), stderr.getvalue()


def verse_map(path: Path) -> dict:
    conn = sqlite3.connect(path)
    try:
        return {(slug, c, v): text for slug, c, v, text in conn.execute(
            "SELECT b.slug, v.chapter_number, v.verse_number, v.text FROM verses v JOIN books b ON b.id = v.book_id"
        )}
    finally:
        conn.close()


class SampleConversionTests(unittest.TestCase):
    """Each sample converts through the CLI; the databases are shared by the tests below."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls._tmp.name)
        cls.databases = {}
        cls.outputs = {}
        for fmt, name in SAMPLE_FILES.items():
            database = cls.out / f"{fmt}.sqlite"
            cls.outputs[fmt] = run_cli(str(SAMPLES / name), "--allow-partial", "-o", str(database))
            cls.databases[fmt] = database

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_samples_exist_for_every_format(self) -> None:
        for name in SAMPLE_FILES.values():
            self.assertTrue((SAMPLES / name).is_file(), name)
        self.assertTrue((SAMPLES / "README.md").is_file())

    def test_every_sample_converts_with_its_format_detected(self) -> None:
        for fmt, (code, out, err) in self.outputs.items():
            with self.subTest(format=fmt):
                self.assertEqual(code, 0, err)
                self.assertIn(f"Format: {fmt} (detected from content)", out)
                self.assertIn(f"Parser: bibles.parsers.{fmt}", out)
                self.assertIn("Validation passed", out)
                self.assertIn("Wrote 3 books, 9 chapters and 147 verses", out)
                self.assertNotIn("Warning:", out)

    @unittest.skipUnless(REFERENCE_DB.is_file(), "reference database not found")
    def test_schema_matches_reference(self) -> None:
        expected = schema_description(REFERENCE_DB)
        for fmt, database in self.databases.items():
            with self.subTest(format=fmt):
                self.assertEqual(schema_description(database), expected)

    def test_books_chapters_and_verses_match_the_sample(self) -> None:
        for fmt, database in self.databases.items():
            with self.subTest(format=fmt):
                conn = sqlite3.connect(database)
                try:
                    books = conn.execute("SELECT sort_order, canonical_name, common_name, slug, testament "
                                         "FROM books ORDER BY sort_order").fetchall()
                    chapters = {}
                    for slug, number, count in conn.execute(
                        "SELECT b.slug, c.chapter_number, COUNT(v.id) FROM chapters c JOIN books b ON b.id = c.book_id "
                        "JOIN verses v ON v.chapter_id = c.id GROUP BY c.id ORDER BY b.sort_order, c.chapter_number"
                    ):
                        chapters.setdefault(slug, []).append(count)
                    texts = dict(((slug, c, v), t) for slug, c, v, t in conn.execute(
                        "SELECT b.slug, chapter_number, verse_number, text FROM verses JOIN books b ON b.id = book_id"))
                finally:
                    conn.close()
                self.assertEqual(books, EXPECTED_BOOKS)
                self.assertEqual(chapters, EXPECTED_CHAPTERS)
                self.assertEqual(texts[("ruth", 1, 2)], RUTH_1_2[fmt])
                self.assertEqual(texts[("3-john", 1, 14)], JOHN3_14[fmt])
                for text in texts.values():
                    self.assertEqual(text, " ".join(text.split()))
                    self.assertNotIn("\\", text)
                    self.assertNotIn("strong", text)
                    self.assertNotIn("¶", text)

    def test_formats_from_the_same_source_have_identical_text(self) -> None:
        usfm = verse_map(self.databases["usfm"])
        self.assertEqual(len(usfm), 147)
        self.assertEqual(verse_map(self.databases["usx"]), usfm)
        self.assertEqual(verse_map(self.databases["usj"]), usfm)

    def test_every_format_has_the_same_references(self) -> None:
        references = set(verse_map(self.databases["usfm"]))
        for fmt in ("osis", "vpl"):
            self.assertEqual(set(verse_map(self.databases[fmt])), references, fmt)

    def test_footnotes_do_not_leak(self) -> None:
        # Ruth 1:1 carries the footnote "ruled: Heb. judged" in every format that has notes.
        for fmt, database in self.databases.items():
            with self.subTest(format=fmt):
                self.assertNotIn("Heb. judged", verse_map(database)[("ruth", 1, 1)])

    def test_generated_database_validates(self) -> None:
        for fmt, database in self.databases.items():
            with self.subTest(format=fmt):
                code, out, _ = run_cli("--validate", str(database), "--allow-partial")
                self.assertEqual(code, 0, out)
                code, out, _ = run_cli("--validate", str(database))
                self.assertEqual(code, 1)
                self.assertIn("FAIL  Book count: expected 66 books, found 3", out)


class RtfSampleTests(unittest.TestCase):
    """The ASV RTF sample (the same three books, one file each) as a folder and as a zip archive."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        tmp = Path(cls._tmp.name)
        cls.archive = tmp / "asv-rtf.zip"
        with zipfile.ZipFile(cls.archive, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(RTF_SAMPLES.glob("*.rtf")):
                archive.write(path, f"release/USX_1/{path.name}")
        cls.outputs = {source: run_cli(str(path), "--allow-partial", "-o", str(tmp / f"{source}.sqlite"))
                       for source, path in (("folder", RTF_SAMPLES), ("zip", cls.archive))}
        cls.databases = {source: tmp / f"{source}.sqlite" for source in cls.outputs}
        cls.usfm = tmp / "usfm.sqlite"
        run_cli(str(SAMPLES / SAMPLE_FILES["usfm"]), "--allow-partial", "-o", str(cls.usfm))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_folder_and_zip_convert(self) -> None:
        inputs = {"folder": "Input: folder, 3 rtf files in .",
                  "zip": "Input: zip archive, 3 rtf files in release/USX_1"}
        for source, (code, out, err) in self.outputs.items():
            with self.subTest(source=source):
                self.assertEqual(code, 0, err)
                self.assertIn(inputs[source], out)
                self.assertIn("Format: rtf (detected from content)", out)
                self.assertIn("Wrote 3 books, 9 chapters and 147 verses", out)
                self.assertNotIn("Warning:", out)
        self.assertEqual(verse_map(self.databases["zip"]), verse_map(self.databases["folder"]))

    def test_same_references_as_the_kjv_and_asv_text(self) -> None:
        verses = verse_map(self.databases["folder"])
        self.assertEqual(set(verses), set(verse_map(self.usfm)))
        self.assertEqual(verses[("ruth", 1, 2)], RUTH_1_2["usfm"])
        self.assertEqual(verses[("ruth", 1, 1)][:58],
                         "And it came to pass in the days when the judges judged, th")
        self.assertEqual(verses[("3-john", 1, 14)],
                         "but I hope shortly to see thee, and we shall speak face to face. Peace be unto thee. "
                         "The friends salute thee. Salute the friends by name.")
        for text in verses.values():
            self.assertEqual(text, " ".join(text.split()))
            self.assertNotRegex(text, r"[\\{}]")


class TuiQueryTests(unittest.TestCase):
    """The queries the reference TUI runs work on a generated database."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.database = Path(cls._tmp.name) / "kjv.sqlite"
        code, _, err = run_cli(str(SAMPLES / "kjv.usfm"), "--allow-partial", "-o", str(cls.database))
        assert code == 0, err

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_tui_queries_run(self) -> None:
        # Copied from BibleStore in bible-esv/tui/bible_tui.py.
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        try:
            metadata = {row["key"]: row["value"] for row in conn.execute("SELECT key, value FROM metadata")}
            self.assertEqual(metadata["version"], "kjv")
            for order in ("sort_order", "common_name COLLATE NOCASE"):
                books = conn.execute(f"SELECT id, sort_order, common_name, testament FROM books ORDER BY {order}").fetchall()
                self.assertEqual(len(books), 3)
            ruth = conn.execute("SELECT id FROM books WHERE slug = 'ruth'").fetchone()["id"]
            chapters = [r["chapter_number"] for r in conn.execute(
                "SELECT chapter_number FROM chapters WHERE book_id = ? ORDER BY chapter_number", (ruth,))]
            self.assertEqual(chapters, [1, 2, 3, 4])
            verses = conn.execute("SELECT verse_number, text FROM verses WHERE book_id = ? AND chapter_number = ? "
                                  "ORDER BY verse_number", (ruth, 1)).fetchall()
            self.assertEqual([v["verse_number"] for v in verses], list(range(1, 23)))
            rows = conn.execute(
                "SELECT books.id AS book_id, books.sort_order, books.common_name, verses.chapter_number, "
                "verses.verse_number, verses.text FROM verses JOIN books ON books.id = verses.book_id "
                "ORDER BY books.sort_order, verses.chapter_number, verses.verse_number").fetchall()
            self.assertEqual(len(rows), 147)
            self.assertEqual((rows[-1]["common_name"], rows[-1]["chapter_number"], rows[-1]["verse_number"]),
                             ("3 John", 1, 14))
        finally:
            conn.close()

    @unittest.skipUnless(REFERENCE_TUI.is_file(), "reference TUI not found")
    def test_reference_tui_store_reads_database(self) -> None:
        spec = importlib.util.spec_from_file_location("reference_bible_tui", REFERENCE_TUI)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module  # its dataclasses look the module up while being created
        self.addCleanup(sys.modules.pop, spec.name, None)
        spec.loader.exec_module(module)
        store = module.BibleStore(self.database)
        try:
            self.assertEqual(store.metadata()["book_count"], "3")
            books = store.books(alphabetical=False)
            self.assertEqual([b.name for b in books], ["Ruth", "Jonah", "3 John"])
            self.assertEqual([b.name for b in store.books(alphabetical=True)], ["3 John", "Jonah", "Ruth"])
            jonah = books[1]
            self.assertEqual(store.chapters(jonah.id), [1, 2, 3, 4])
            self.assertEqual(len(store.verses(jonah.id, 2)), 10)
            self.assertEqual(len(store.all_verses()), 147)
        finally:
            store.close()


class CommandLineTests(unittest.TestCase):
    """The wrapper, run as a user would, from another directory.

    It runs from a copy of the repository layout (tool/ beside bibles/), so the default output never lands in
    the real bibles/ directory.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.collection = root / "repo" / "bibles"
        self.wrapper = root / "repo" / "tool" / "bin" / "bibles"
        ignore = shutil.ignore_patterns("__pycache__")
        for part in ("bibles", "bin"):
            shutil.copytree(TOOL_ROOT / part, root / "repo" / "tool" / part, ignore=ignore)
        self.tmp = root / "work"
        self.tmp.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def bibles(self, *argv: str) -> subprocess.CompletedProcess:
        return subprocess.run([str(self.wrapper), *argv], cwd=self.tmp, capture_output=True, text=True)

    def test_default_output_goes_to_bibles_directory(self) -> None:
        result = self.bibles(str(SAMPLES / "kjv.usfm"), "--allow-partial")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.collection / "kjv.sqlite").is_file())
        self.assertEqual(os.listdir(self.tmp), [])
        output_line = next(line for line in result.stdout.splitlines() if line.startswith("Output: "))
        self.assertEqual(Path(output_line[len("Output: "):]).resolve(), (self.collection / "kjv.sqlite").resolve())

    def test_explicit_output_file_name(self) -> None:
        result = self.bibles(str(SAMPLES / "kjv.usj"), "--allow-partial", "-n", "king-james")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.collection / "king-james.sqlite").is_file())

    def test_explicit_output_directory(self) -> None:
        result = self.bibles(str(SAMPLES / "kjv.osis.xml"), "--allow-partial", "-o", "build/")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.tmp / "build" / "kjv.osis.sqlite").is_file())

    def test_explicit_full_output_path(self) -> None:
        result = self.bibles(str(SAMPLES / "kjv.vpl.txt"), "--allow-partial", "-o", "out/bible.db")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.tmp / "out" / "bible.db").is_file())

    def test_missing_input_file(self) -> None:
        result = self.bibles("missing.usfm")
        self.assertEqual(result.returncode, 1)
        self.assertIn("source not found", result.stderr)
        self.assertEqual(os.listdir(self.tmp), [])
        self.assertFalse(self.collection.exists())

    def test_unsupported_format_flag(self) -> None:
        result = self.bibles(str(SAMPLES / "kjv.usfm"), "--format", "docx")
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid choice: 'docx'", result.stderr)

    def test_undetectable_input(self) -> None:
        source = self.tmp / "notes.txt"
        source.write_text("Just some notes.\n", encoding="utf-8")
        result = self.bibles(str(source))
        self.assertEqual(result.returncode, 1)
        self.assertIn("detect failed", result.stderr)
        self.assertEqual(os.listdir(self.tmp), ["notes.txt"])

    def test_full_bible_required_without_allow_partial(self) -> None:
        result = self.bibles(str(SAMPLES / "kjv.usx"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("validate failed", result.stderr)
        self.assertFalse(self.collection.exists())


if __name__ == "__main__":
    unittest.main()
