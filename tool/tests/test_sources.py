"""Folder and zip archive sources: finding the book files, merging them, and leaving nothing behind."""

from __future__ import annotations

import os
import re
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from bibles.detect import FormatDetectionError
from bibles.sources import ARCHIVE, FOLDER, find_book_files, open_source, read_dbl_metadata
from tests.test_samples import SAMPLES, run_cli, verse_map

METADATA = """<?xml version="1.0" encoding="utf-8"?>
<DBLMetadata version="2.2.1" id="0123456789abcdef" revision="1">
  <identification>
    <name>King James Version Sample</name>
    <abbreviation>KJVS</abbreviation>
  </identification>
</DBLMetadata>
"""
STYLES = '<?xml version="1.0" encoding="utf-8"?>\n<stylesheet><property name="font-size">12</property></stylesheet>\n'
VERSIFICATION = "# List of books, chapters, verses\n# One line per book.\nRUT 1:22 2:23 3:18 4:22\nJON 1:17 2:10 3:10 4:11\n"


def sample_books() -> dict:
    """The USFM sample split into one file per book, keyed by book code."""
    text = (SAMPLES / "kjv.usfm").read_text(encoding="utf-8-sig")
    parts = re.split(r"(?=^\\id )", text, flags=re.MULTILINE)
    return {part.split()[1]: part for part in parts if part.startswith("\\id ")}


class BundleTestCase(unittest.TestCase):
    """Builds a folder laid out like a Digital Bible Library bundle, with a temporary directory of its own
    so that tests can check that a run leaves no extracted files behind."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.scratch = self.tmp / "scratch"
        self.scratch.mkdir()
        patcher = mock.patch("tempfile.tempdir", str(self.scratch))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.bundle = self.tmp / "kjv-bundle"
        self.books = sample_books()
        self.write("metadata.xml", METADATA)
        self.write("license.xml", "<license/>\n")
        self.write("release/styles.xml", STYLES)
        self.write("release/versification.vrs", VERSIFICATION)
        self.write(".DS_Store", "\0\0\0\1Bud1")
        for code, text in self.books.items():
            self.write(f"release/USX_1/{code}.usfm", text)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, name: str, content: str) -> Path:
        path = self.bundle / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def zip(self, name: str = "kjv-bundle.zip") -> Path:
        archive = self.tmp / name
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipped:
            for directory, _, files in os.walk(self.bundle):
                for file_name in sorted(files):
                    path = Path(directory) / file_name
                    zipped.write(path, path.relative_to(self.bundle).as_posix())
            zipped.writestr("__MACOSX/release/USX_1/._RUT.usfm", "\\id RUT resource fork")
        return archive

    def find(self, forced=None):
        with open_source(self.bundle) as opened:
            return find_book_files(self.bundle, opened, forced)

    def assert_no_leftovers(self) -> None:
        self.assertEqual(list(self.scratch.iterdir()), [])


class FindBookFilesTests(BundleTestCase):
    def test_book_files_are_found_and_the_rest_ignored(self) -> None:
        files = self.find()
        self.assertEqual(files.kind, FOLDER)
        self.assertEqual([f.name for f in files.files],
                         ["release/USX_1/3JN.usfm", "release/USX_1/JON.usfm", "release/USX_1/RUT.usfm"])
        self.assertEqual(files.ignored, ("license.xml", "metadata.xml", "release/styles.xml",
                                         "release/versification.vrs"))
        self.assertEqual((files.detection.format, files.detection.method), ("usfm", "content"))
        self.assertEqual((files.version, files.version_name), ("KJVS", "King James Version Sample"))
        self.assertEqual(files.describe(), "folder, 3 usfm files in release/USX_1; 4 other files ignored")

    def test_mixed_formats_need_a_forced_format(self) -> None:
        (self.bundle / "kjv.usx").write_bytes((SAMPLES / "kjv.usx").read_bytes())
        with self.assertRaisesRegex(FormatDetectionError, r"more than one format: usfm \(3\), usx \(1\); use --format"):
            self.find()
        files = self.find("usx")
        self.assertEqual([f.name for f in files.files], ["kjv.usx"])
        self.assertEqual(files.detection.method, "forced")
        self.assertIn("release/USX_1/RUT.usfm", files.ignored)

    def test_no_bible_files(self) -> None:
        for path in (self.bundle / "release" / "USX_1").iterdir():
            path.unlink()
        with self.assertRaisesRegex(FormatDetectionError, r"no Bible files \(supported formats: .*\) found in the folder .*4 files looked at"):
            self.find()
        with self.assertRaisesRegex(FormatDetectionError, "no osis files found"):
            self.find("osis")

    def test_metadata_that_is_not_dbl_is_ignored(self) -> None:
        self.write("metadata.xml", "<metadata><abbreviation>NO</abbreviation></metadata>")
        self.assertEqual(read_dbl_metadata(self.bundle / "metadata.xml"), (None, None))
        self.write("metadata.xml", "<DBLMetadata><identification>")
        self.assertEqual((self.find().version, self.find().version_name), (None, None))

    def test_zip_is_extracted_for_the_run_only(self) -> None:
        archive = self.zip()
        with open_source(archive) as opened:
            self.assertEqual(opened.kind, ARCHIVE)
            self.assertTrue(str(opened.root).startswith(str(self.scratch)))
            files = find_book_files(archive, opened)
            self.assertEqual(len(files.files), 3)
            self.assertNotIn("__MACOSX/release/USX_1/._RUT.usfm", files.ignored)
        self.assert_no_leftovers()


class BundleConversionTests(BundleTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.out = self.tmp / "out"
        code, _, err = run_cli(str(SAMPLES / "kjv.usfm"), "--allow-partial", "-o", str(self.out / "single.sqlite"))
        self.assertEqual(code, 0, err)
        self.single = verse_map(self.out / "single.sqlite")

    def convert(self, source: Path, *argv: str) -> tuple:
        return run_cli(str(source), "-o", str(self.out) + os.sep, *argv)

    def test_folder_converts_like_the_single_file(self) -> None:
        code, out, err = self.convert(self.bundle, "--allow-partial")
        self.assertEqual(code, 0, err)
        self.assertIn("Input: folder, 3 usfm files in release/USX_1; 4 other files ignored", out)
        self.assertIn("Format: usfm (detected from content)", out)
        self.assertIn("(version KJVS)", out)
        self.assertNotIn("Warning:", out)
        database = self.out / "kjv-bundle.sqlite"
        self.assertEqual(verse_map(database), self.single)

    def test_zip_converts_like_the_single_file_and_leaves_nothing_behind(self) -> None:
        code, out, err = self.convert(self.zip(), "--allow-partial")
        self.assertEqual(code, 0, err)
        self.assertIn("Input: zip archive, 3 usfm files in release/USX_1; 4 other files ignored", out)
        self.assertEqual(verse_map(self.out / "kjv-bundle.sqlite"), self.single)
        self.assert_no_leftovers()

    def test_failed_zip_run_leaves_nothing_behind(self) -> None:
        archive = self.zip()
        code, out, err = run_cli(str(archive), "-o", str(self.tmp / "new" / "dir") + os.sep)
        self.assertEqual(code, 1)
        self.assertIn("validate failed", err)
        self.assertIn("Input: zip archive, 3 usfm files", out)
        self.assertFalse((self.tmp / "new").exists())
        self.assert_no_leftovers()

    def test_repeated_books_are_kept_once(self) -> None:
        self.write("release/USX_2/RUT.usfm", self.books["RUT"])
        code, out, err = self.convert(self.bundle, "--allow-partial")
        self.assertEqual(code, 0, err)
        self.assertIn("Warning: 1 book in release/USX_2 repeats release/USX_1 with identical text and was "
                      "skipped (RUT)", out)
        self.assertEqual(verse_map(self.out / "kjv-bundle.sqlite"), self.single)

    def test_differing_copies_fail_naming_both_files(self) -> None:
        self.write("release/USX_2/RUT.usfm", self.books["RUT"].replace("Elimelech", "Elimelek"))
        code, _, err = self.convert(self.zip(), "--allow-partial")
        self.assertEqual(code, 1)
        self.assertIn("parse failed: RUT is in both release/USX_1/RUT.usfm and release/USX_2/RUT.usfm, "
                      "and the copies differ", err)
        self.assertFalse((self.out / "kjv-bundle.sqlite").exists())
        self.assert_no_leftovers()

    def test_parse_errors_name_the_file_inside_the_archive(self) -> None:
        self.write("release/USX_1/JON.usfm", "\\id JON\n\\c 1\n\\v")
        code, _, err = self.convert(self.zip(), "--allow-partial")
        self.assertEqual(code, 1)
        self.assertIn("parse failed: release/USX_1/JON.usfm, line 3", err)
        self.assertNotIn(str(self.scratch), err)

    def test_damaged_zip_fails_in_detect_stage(self) -> None:
        archive = self.zip()
        with zipfile.ZipFile(archive) as zipped:
            member = zipped.getinfo("release/USX_1/RUT.usfm")
        data = bytearray(archive.read_bytes())
        # Flip a byte of the member's compressed data (after its 30-byte local header and name).
        offset = member.header_offset + 30 + len(member.filename) + 5
        data[offset] ^= 0xFF
        archive.write_bytes(bytes(data))
        code, _, err = self.convert(archive, "--allow-partial")
        self.assertEqual(code, 1)
        self.assertIn("detect failed: cannot extract the zip archive", err)
        self.assert_no_leftovers()


if __name__ == "__main__":
    unittest.main()
