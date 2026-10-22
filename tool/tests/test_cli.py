from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bibles.cli import COLLECTION_DIR, CliError, main, resolve_output_path

TOOL_ROOT = Path(__file__).resolve().parents[1]


def run_main(*argv: str) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    code = 0
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            code = main(list(argv))
        except SystemExit as exit_:
            code = exit_.code if isinstance(exit_.code, int) else 1
    return code, stdout.getvalue(), stderr.getvalue()


class ResolveOutputPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.source = Path("sources/kjv.usfm")
        self.collection = self.tmp / "bibles"
        patcher = mock.patch("bibles.cli.COLLECTION_DIR", self.collection)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_collection_dir_is_bibles_at_the_repository_root(self) -> None:
        self.assertEqual(COLLECTION_DIR, TOOL_ROOT.parent / "bibles")

    def test_defaults_to_source_stem_in_collection(self) -> None:
        path = resolve_output_path(self.source, cwd=Path("/nowhere"))
        self.assertEqual(path, self.collection / "kjv.sqlite")

    def test_relative_output_is_taken_from_cwd(self) -> None:
        path = resolve_output_path(self.source, output="out/", cwd=self.tmp)
        self.assertEqual(path, self.tmp / "out" / "kjv.sqlite")

    def test_default_replaces_only_last_suffix(self) -> None:
        path = resolve_output_path(Path("web.usx.xml"), cwd=self.tmp)
        self.assertEqual(path, self.collection / "web.usx.sqlite")

    def test_explicit_name_is_used(self) -> None:
        path = resolve_output_path(self.source, name="bible.db", cwd=self.tmp)
        self.assertEqual(path, self.collection / "bible.db")

    def test_name_without_extension_gets_sqlite_suffix(self) -> None:
        path = resolve_output_path(self.source, name="king-james", cwd=self.tmp)
        self.assertEqual(path, self.collection / "king-james.sqlite")

    def test_name_that_is_a_path_is_rejected(self) -> None:
        with self.assertRaises(CliError):
            resolve_output_path(self.source, name="sub/bible.sqlite", cwd=self.tmp)

    def test_existing_directory_output(self) -> None:
        (self.tmp / "out.d").mkdir()
        path = resolve_output_path(self.source, output="out.d", cwd=self.tmp)
        self.assertEqual(path, self.tmp / "out.d" / "kjv.sqlite")

    def test_trailing_separator_output_is_directory(self) -> None:
        path = resolve_output_path(self.source, output="new.d/", cwd=self.tmp)
        self.assertEqual(path, self.tmp / "new.d" / "kjv.sqlite")

    def test_missing_output_without_extension_is_directory(self) -> None:
        path = resolve_output_path(self.source, output="build", name="x.sqlite", cwd=self.tmp)
        self.assertEqual(path, self.tmp / "build" / "x.sqlite")

    def test_full_file_path_output_is_used_directly(self) -> None:
        path = resolve_output_path(self.source, output="build/bible.db", cwd=self.tmp)
        self.assertEqual(path, self.tmp / "build" / "bible.db")

    def test_absolute_output_ignores_cwd(self) -> None:
        target = self.tmp / "abs" / "bible.sqlite"
        self.assertEqual(resolve_output_path(self.source, output=str(target), cwd=Path("/nowhere")), target)

    def test_name_with_full_file_path_output_is_rejected(self) -> None:
        with self.assertRaises(CliError):
            resolve_output_path(self.source, output="bible.db", name="other.db", cwd=self.tmp)


SAMPLE_USFM = "\\id GEN\n\\c 1\n\\p\n\\v 1 In the beginning.\n\\v 2 And the earth.\n"


class MainTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.source = self.tmp / "kjv.usfm"
        self.source.write_text(SAMPLE_USFM, encoding="utf-8")
        self.collection = self.tmp / "bibles"
        patcher = mock.patch("bibles.cli.COLLECTION_DIR", self.collection)
        patcher.start()
        self.addCleanup(patcher.stop)
        self._old_cwd = os.getcwd()
        os.chdir(self.tmp)

    def tearDown(self) -> None:
        os.chdir(self._old_cwd)
        self._tmp.cleanup()

    def convert(self, *argv: str) -> tuple:
        # One book is a partial Bible, so these runs allow it.
        return run_main(str(self.source), "--allow-partial", *argv)

    def test_no_arguments_prints_usage_and_fails(self) -> None:
        code, _, err = run_main()
        self.assertNotEqual(code, 0)
        self.assertIn("usage:", err)

    def test_help_lists_every_option(self) -> None:
        code, out, _ = run_main("--help")
        self.assertEqual(code, 0)
        for option in ("source", "--output", "--name", "--format", "--allow-partial", "--validate",
                       "--version", "--help"):
            self.assertIn(option, out)

    def test_success_writes_database_in_collection_and_reports_it(self) -> None:
        code, out, _ = self.convert()
        self.assertEqual(code, 0)
        output = self.collection / "kjv.sqlite"
        self.assertFalse((self.tmp / "kjv.sqlite").exists())
        self.assertTrue(output.is_file())
        self.assertIn(f"Output: {output}", out)
        self.assertIn("Format: usfm (detected from content)", out)
        self.assertIn("Parser: bibles.parsers.usfm", out)
        self.assertIn("WARN  Book count: 1 of 66 books (partial Bible allowed)", out)
        self.assertIn("Wrote 1 books, 1 chapters and 2 verses (version kjv)", out)

    def test_missing_output_directory_is_created(self) -> None:
        code, out, _ = self.convert("--output", "nested/dir/")
        self.assertEqual(code, 0)
        self.assertTrue((self.tmp / "nested" / "dir" / "kjv.sqlite").is_file())
        self.assertIn("kjv.sqlite", out)

    def test_parent_of_full_file_path_is_created(self) -> None:
        code, _, _ = self.convert("-o", "deep/path/bible.db")
        self.assertEqual(code, 0)
        self.assertTrue((self.tmp / "deep" / "path" / "bible.db").is_file())

    def test_forced_format_is_reported(self) -> None:
        code, out, _ = self.convert("--format", "usfm")
        self.assertEqual(code, 0)
        self.assertIn("Format: usfm (forced with --format)", out)

    def test_wrong_forced_format_fails_in_parse_stage(self) -> None:
        code, out, err = self.convert("--format", "usx", "-o", "new/dir/")
        self.assertEqual(code, 1)
        self.assertIn("Format: usx (forced with --format)", out)
        self.assertIn("Parser: bibles.parsers.usx", out)
        self.assertIn("error: parse failed:", err)
        self.assertIn("no database was written", err)
        self.assertFalse((self.tmp / "new").exists())

    def test_source_without_verses_fails_and_leaves_nothing(self) -> None:
        self.source.write_text("\\id GEN\n\\h Genesis\n", encoding="utf-8")
        code, _, err = self.convert()
        self.assertEqual(code, 1)
        self.assertIn("parse failed:", err)
        self.assertIn("no verses found", err)
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), ["kjv.usfm"])

    def test_partial_bible_fails_validation_without_allow_partial(self) -> None:
        code, out, err = run_main(str(self.source))
        self.assertEqual(code, 1)
        self.assertIn("FAIL  Book count: expected 66 books, found 1", out)
        self.assertIn("error: validate failed: database validation failed: Book count", err)
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), ["kjv.usfm"])

    def test_existing_output_is_replaced_only_on_success(self) -> None:
        self.collection.mkdir()
        output = self.collection / "kjv.sqlite"
        output.write_text("previous")
        run_main(str(self.source))  # fails validation
        self.assertEqual(output.read_text(), "previous")
        self.assertEqual(self.convert()[0], 0)
        self.assertNotEqual(output.read_bytes(), b"previous")

    def test_output_cannot_be_the_source(self) -> None:
        code, _, err = self.convert("-o", str(self.source))
        self.assertEqual(code, 1)
        self.assertIn("output path is the source file", err)
        self.assertEqual(self.source.read_text(encoding="utf-8"), SAMPLE_USFM)

    def test_unknown_format_is_rejected(self) -> None:
        code, _, err = run_main(str(self.source), "--format", "docx")
        self.assertNotEqual(code, 0)
        self.assertIn("invalid choice", err)

    def test_missing_source_fails(self) -> None:
        code, _, err = run_main(str(self.tmp / "missing.usfm"))
        self.assertNotEqual(code, 0)
        self.assertIn("source file not found", err)


class ShellInvocationTests(unittest.TestCase):
    def test_module_runs_from_shell(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "bibles", "--help"], cwd=TOOL_ROOT, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage: bibles", result.stdout)

    def test_wrapper_script_runs_from_any_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [str(TOOL_ROOT / "bin" / "bibles")], cwd=tmp, capture_output=True, text=True
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage: bibles", result.stderr)


if __name__ == "__main__":
    unittest.main()
