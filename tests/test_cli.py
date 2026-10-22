from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from bibles.cli import CliError, main, resolve_output_path

REPO_ROOT = Path(__file__).resolve().parents[1]


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

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_defaults_to_source_stem_in_cwd(self) -> None:
        self.assertEqual(resolve_output_path(self.source, cwd=self.tmp), self.tmp / "kjv.sqlite")

    def test_default_replaces_only_last_suffix(self) -> None:
        path = resolve_output_path(Path("web.usx.xml"), cwd=self.tmp)
        self.assertEqual(path, self.tmp / "web.usx.sqlite")

    def test_explicit_name_is_used(self) -> None:
        path = resolve_output_path(self.source, name="bible.db", cwd=self.tmp)
        self.assertEqual(path, self.tmp / "bible.db")

    def test_name_without_extension_gets_sqlite_suffix(self) -> None:
        path = resolve_output_path(self.source, name="king-james", cwd=self.tmp)
        self.assertEqual(path, self.tmp / "king-james.sqlite")

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


class MainTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.source = self.tmp / "kjv.usfm"
        self.source.write_text("\\id GEN\n", encoding="utf-8")
        self._old_cwd = os.getcwd()
        os.chdir(self.tmp)

    def tearDown(self) -> None:
        os.chdir(self._old_cwd)
        self._tmp.cleanup()

    def test_no_arguments_prints_usage_and_fails(self) -> None:
        code, _, err = run_main()
        self.assertNotEqual(code, 0)
        self.assertIn("usage:", err)

    def test_help_lists_every_option(self) -> None:
        code, out, _ = run_main("--help")
        self.assertEqual(code, 0)
        for option in ("source", "--output", "--name", "--format", "--version", "--help"):
            self.assertIn(option, out)

    def test_success_exits_zero_and_reports_output_in_cwd(self) -> None:
        code, out, _ = run_main(str(self.source))
        self.assertEqual(code, 0)
        self.assertIn(f"Output: {Path.cwd() / 'kjv.sqlite'}", out)
        self.assertIn("Format: auto-detect", out)

    def test_missing_output_directory_is_created(self) -> None:
        code, out, _ = run_main(str(self.source), "--output", "nested/dir/")
        self.assertEqual(code, 0)
        self.assertTrue((self.tmp / "nested" / "dir").is_dir())
        self.assertIn("kjv.sqlite", out)

    def test_parent_of_full_file_path_is_created(self) -> None:
        code, _, _ = run_main(str(self.source), "-o", "deep/path/bible.db")
        self.assertEqual(code, 0)
        self.assertTrue((self.tmp / "deep" / "path").is_dir())

    def test_forced_format_is_reported(self) -> None:
        code, out, _ = run_main(str(self.source), "--format", "usx")
        self.assertEqual(code, 0)
        self.assertIn("Format: usx", out)

    def test_unknown_format_is_rejected(self) -> None:
        code, _, err = run_main(str(self.source), "--format", "docx")
        self.assertNotEqual(code, 0)
        self.assertIn("invalid choice", err)

    def test_missing_source_fails(self) -> None:
        code, _, err = run_main(str(self.tmp / "missing.usfm"))
        self.assertNotEqual(code, 0)
        self.assertIn("source file not found", err)

    def test_no_database_is_written_yet(self) -> None:
        run_main(str(self.source))
        self.assertFalse((self.tmp / "kjv.sqlite").exists())


class ShellInvocationTests(unittest.TestCase):
    def test_module_runs_from_shell(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "bibles", "--help"], cwd=REPO_ROOT, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage: bibles", result.stdout)

    def test_wrapper_script_runs_from_any_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [str(REPO_ROOT / "bin" / "bibles")], cwd=tmp, capture_output=True, text=True
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage: bibles", result.stderr)


if __name__ == "__main__":
    unittest.main()
