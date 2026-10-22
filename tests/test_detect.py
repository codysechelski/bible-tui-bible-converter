from __future__ import annotations

import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path

from bibles.cli import main
from bibles.detect import SUPPORTED_FORMATS, FormatDetectionError, detect_format, sniff_content

USFM = "\\id GEN\n\\h Genesis\n\\mt1 Genesis\n\\c 1\n\\p\n\\v 1 In the beginning God created.\n"
USX = (
    '<?xml version="1.0" encoding="utf-8"?>\n<!-- generated -->\n'
    '<usx version="3.0"><book code="GEN" style="id"/><chapter number="1" style="c"/></usx>\n'
)
OSIS = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">'
    '<osisText osisIDWork="KJV"><div type="book" osisID="Gen"/></osisText></osis>\n'
)
VPL = "Gen 1:1 In the beginning God created.\nGen 1:2 And the earth was without form.\n"
USJ = '{"type": "USJ", "version": "3.1", "content": [{"type": "book", "marker": "id", "code": "GEN"}]}'

POSITIVE = {
    "usfm": [("gen.usfm", USFM), ("gen.txt", "\ufeff" + USFM), ("noext", "\\c 1\n\\v 1 Text\n")],
    "usx": [("gen.usx", USX), ("gen.xml", USX)],
    "osis": [("kjv.xml", OSIS), ("kjv.osis", '<osis:osis xmlns:osis="x"/>')],
    "vpl": [
        ("kjv.txt", VPL),
        ("kjv.vpl", "GEN 1:1 In the beginning.\n1 John 1:1 That which was.\nSong of Solomon 1:1 The song.\n"),
        ("dotted.txt", "GEN.1.1 In the beginning.\nGEN.1.2 And the earth.\n"),
    ],
    "usj": [("gen.json", USJ), ("gen.usj", "\ufeff" + USJ)],
}

NEGATIVE = {
    "usfm": ("notes.txt", "A plain note that mentions C:\\path and a \\ backslash.\n"),
    "usx": ("page.xml", '<?xml version="1.0"?><html><body/></html>'),
    "osis": ("feed.xml", "<rss><channel/></rss>"),
    "vpl": ("prose.txt", "In the beginning God created the heavens.\nGen 1:1 is quoted later.\n"),
    "usj": ("data.json", '{"type": "other", "content": []}'),
}


class DetectTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def make(self, name: str, content: str) -> Path:
        path = self.tmp / name
        path.write_text(content, encoding="utf-8")
        return path


class ContentSniffingTests(DetectTestCase):
    def test_positive_samples(self) -> None:
        for expected, samples in POSITIVE.items():
            for name, content in samples:
                with self.subTest(format=expected, name=name):
                    detection = detect_format(self.make(name, content))
                    self.assertEqual((detection.format, detection.method), (expected, "content"))

    def test_negative_samples_are_not_detected(self) -> None:
        for fmt, (name, content) in NEGATIVE.items():
            with self.subTest(format=fmt):
                self.assertIsNone(sniff_content(self.make(name, content)))
                with self.assertRaises(FormatDetectionError):
                    detect_format(self.make(name, content))

    def test_usx_and_osis_are_told_apart(self) -> None:
        self.assertEqual(sniff_content(self.make("a.xml", USX)), "usx")
        self.assertEqual(sniff_content(self.make("b.xml", OSIS)), "osis")

    def test_invalid_json_is_not_usj(self) -> None:
        self.assertIsNone(sniff_content(self.make("bad.json", '{"type": "USJ", ')))


class ExtensionTests(DetectTestCase):
    def test_content_wins_over_misleading_extension(self) -> None:
        cases = [("osis.usfm", OSIS, "osis"), ("usfm.usx", USFM, "usfm"), ("vpl.usj", VPL, "vpl"),
                 ("usj.vpl", USJ, "usj"), ("usx.osis", USX, "usx")]
        for name, content, expected in cases:
            with self.subTest(name=name):
                detection = detect_format(self.make(name, content))
                self.assertEqual((detection.format, detection.method), (expected, "content"))

    def test_extension_used_when_content_is_inconclusive(self) -> None:
        for name, expected in (("a.usfm", "usfm"), ("b.SFM", "usfm"), ("c.usx", "usx"),
                               ("d.osis", "osis"), ("e.vpl", "vpl"), ("f.usj", "usj")):
            with self.subTest(name=name):
                detection = detect_format(self.make(name, "nothing recognisable\n"))
                self.assertEqual((detection.format, detection.method), (expected, "extension"))

    def test_generic_extension_with_unknown_content_fails(self) -> None:
        for name in ("a.txt", "b.xml", "c.json", "noext"):
            with self.subTest(name=name):
                with self.assertRaisesRegex(FormatDetectionError, "usfm, usx, osis, vpl, usj"):
                    detect_format(self.make(name, "nothing recognisable\n"))

    def test_unreadable_file_fails(self) -> None:
        path = self.make("locked.usfm", USFM)
        path.chmod(0)
        try:
            if os.access(path, os.R_OK):
                self.skipTest("running with permissions that ignore file modes")
            with self.assertRaisesRegex(FormatDetectionError, "cannot read"):
                detect_format(path)
        finally:
            path.chmod(0o644)

    def test_empty_file_fails(self) -> None:
        with self.assertRaises(FormatDetectionError):
            detect_format(self.make("empty.txt", ""))


class ForcedFormatTests(DetectTestCase):
    def test_forced_format_skips_detection(self) -> None:
        path = self.make("unknown.txt", "nothing recognisable\n")
        for fmt in SUPPORTED_FORMATS:
            detection = detect_format(path, fmt)
            self.assertEqual((detection.format, detection.method), (fmt, "forced"))
            self.assertEqual(detection.describe(), f"{fmt} (forced with --format)")

    def test_unsupported_forced_format(self) -> None:
        with self.assertRaisesRegex(FormatDetectionError, "supported formats"):
            detect_format(self.make("a.usfm", USFM), "docx")


class CliDetectionTests(DetectTestCase):
    def run_cli(self, *argv: str) -> tuple:
        stdout, stderr = io.StringIO(), io.StringIO()
        old_cwd = os.getcwd()
        os.chdir(self.tmp)
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = main(list(argv))
        finally:
            os.chdir(old_cwd)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_detected_format_is_reported(self) -> None:
        # The sample has no verses, so the run fails after detection but still reports the format.
        code, out, err = self.run_cli(str(self.make("kjv.xml", OSIS)))
        self.assertEqual(code, 1)
        self.assertIn("Format: osis (detected from content)", out)
        self.assertIn("parse failed", err)

    def test_undetectable_file_exits_non_zero_and_names_formats(self) -> None:
        code, out, err = self.run_cli(str(self.make("notes.txt", "hello\n")), "-o", "out/")
        self.assertEqual(code, 1)
        self.assertNotIn("Format:", out)
        self.assertIn("detect failed: could not detect the format", err)
        self.assertIn("usfm, usx, osis, vpl, usj", err)
        self.assertIn("--format", err)
        self.assertFalse((self.tmp / "out").exists())

    def test_forced_format_overrides_detection(self) -> None:
        code, out, _ = self.run_cli(str(self.make("notes.txt", "GEN 1:1 Text.\n")), "--format", "vpl",
                                    "--allow-partial")
        self.assertEqual(code, 0)
        self.assertIn("Format: vpl (forced with --format)", out)


if __name__ == "__main__":
    unittest.main()
