"""Working out the version abbreviation and full name (`bibles/identity.py`)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bibles.identity import (
    GIVEN,
    INITIALS,
    SAME_AS_ABBREVIATION,
    SOURCE_NAME,
    VersionError,
    check_given,
    id_line_version,
    initials,
    resolve_version,
    source_name_version,
    split_abbreviation,
)
from bibles.model import Bible
from bibles.parsers import parse_file
from bibles.parsers.osis import work_abbreviation
from tests.test_parsers import SAMPLES, USFM


def bible_with_id_lines(*descriptions: str) -> Bible:
    """A Bible with one verse per book, each book's `\\id` line carrying the given description."""
    bible = Bible()
    for code, description in zip(("GEN", "EXO", "LEV", "NUM", "DEU"), descriptions):
        bible.add_verse(code, 1, 1, "Text.")
        if description:
            bible.book(code).headers["id"] = description
    return bible


class IdLineTests(unittest.TestCase):
    def test_shared_description_is_the_name(self) -> None:
        bible = bible_with_id_lines("- Bíblia Livre Para Todos", "- Bíblia Livre Para Todos", "")
        self.assertEqual(id_line_version(bible), (None, "Bíblia Livre Para Todos"))

    def test_trailing_abbreviation_is_split_off(self) -> None:
        bible = bible_with_id_lines("World English Bible (WEB)", "World English Bible (WEB)")
        self.assertEqual(id_line_version(bible), ("WEB", "World English Bible"))

    def test_book_names_are_ignored(self) -> None:
        # eBible.org's KJV puts the book's name there: `\id RUT Ruth`.
        self.assertEqual(id_line_version(bible_with_id_lines("Genesis", "Exodus", "Leviticus")), (None, None))

    def test_a_description_most_books_lack_is_ignored(self) -> None:
        bible = bible_with_id_lines("Sample", "Sample", "Other", "Other", "Third")
        self.assertEqual(id_line_version(bible), (None, None))
        self.assertEqual(id_line_version(bible_with_id_lines("Sample Bible")), (None, None))

    def test_split_abbreviation_needs_an_abbreviation(self) -> None:
        self.assertEqual(split_abbreviation("Good News (1976 edition)"), ("Good News (1976 edition)", None))
        self.assertEqual(split_abbreviation("Reina-Valera (RV1909)"), ("Reina-Valera", "RV1909"))


class SourceNameTests(unittest.TestCase):
    def version(self, name: str):
        return source_name_version(Path("/downloads") / name)

    def test_name_language_and_abbreviation(self) -> None:
        self.assertEqual(self.version("American Standard Version of 1901 [eng] ASV.zip"),
                         ("ASV", "American Standard Version of 1901", SOURCE_NAME))

    def test_name_language_and_description(self) -> None:
        self.assertEqual(
            self.version("King James Version [eng] without Strong's numbers, 1769 standardized text.zip"),
            ("KJV", "King James Version without Strong's numbers, 1769 standardized text", SOURCE_NAME),
        )

    def test_ebible_names(self) -> None:
        self.assertEqual(self.version("eng-web_usfm.zip")[:2], ("WEB", None))
        self.assertEqual(self.version("porbr2018_usfm.zip")[:2], ("PORBR2018", None))

    def test_plain_names_say_nothing(self) -> None:
        self.assertEqual(self.version("kjv.usfm")[:2], (None, None))

    def test_initials(self) -> None:
        self.assertEqual(initials("American Standard Version of 1901"), "ASV")
        self.assertEqual(initials("Bíblia Livre - Textus Receptus"), "BLTR")
        self.assertIsNone(initials("bible"))


class ResolveVersionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def resolve(self, source: str, bible=None, found=(), **given):
        return resolve_version(bible or Bible(), self.tmp / source, found, **given)

    def test_given_values_win(self) -> None:
        version = self.resolve("eng-web_usfm.zip", found=[("X", "Y", "from the OSIS header")],
                               abbreviation=" WEB ", name="World  English Bible")
        self.assertEqual((version.abbreviation, version.name), ("WEB", "World English Bible"))
        self.assertEqual((version.abbreviation_origin, version.name_origin), (GIVEN, GIVEN))

    def test_given_values_must_be_paired_and_usable(self) -> None:
        with self.assertRaisesRegex(VersionError, "must be given together"):
            check_given("WEB", None)
        with self.assertRaisesRegex(VersionError, "must be given together"):
            check_given(None, "World English Bible")
        with self.assertRaisesRegex(VersionError, "cannot be blank"):
            check_given(" ", "World English Bible")
        with self.assertRaisesRegex(VersionError, "without spaces"):
            check_given("W E B", "World English Bible")
        self.assertIsNone(check_given(None, None))

    def test_what_the_source_says_comes_first(self) -> None:
        bible = bible_with_id_lines("Other Name (OTH)", "Other Name (OTH)")
        version = self.resolve("eng-web_usfm.zip", bible, [("KJV", "King James Version", "from the OSIS header")])
        self.assertEqual((version.abbreviation, version.name), ("KJV", "King James Version"))
        self.assertEqual(version.abbreviation_origin, "from the OSIS header")

    def test_each_value_comes_from_the_first_source_that_has_it(self) -> None:
        bible = bible_with_id_lines("Bíblia Livre - Textus Receptus", "Bíblia Livre - Textus Receptus")
        version = self.resolve("porbr2018_usfm.zip", bible)
        self.assertEqual((version.abbreviation, version.name), ("PORBR2018", "Bíblia Livre - Textus Receptus"))
        self.assertEqual((version.abbreviation_origin, version.name_origin),
                         ("from the eBible.org file name", "from the \\id lines"))

    def test_abbreviation_falls_back_to_the_source_name(self) -> None:
        version = self.resolve("WEB.zip", bible_with_id_lines("World English Bible", "World English Bible"))
        self.assertEqual((version.abbreviation, version.name), ("WEB", "World English Bible"))
        self.assertEqual(version.abbreviation_origin, SOURCE_NAME)
        version = self.resolve("kjv.vpl.txt")
        self.assertEqual((version.abbreviation, version.name), ("kjv", "kjv"))
        self.assertEqual(version.name_origin, SAME_AS_ABBREVIATION)

    def test_abbreviation_from_initials_when_the_source_name_is_not_one(self) -> None:
        version = self.resolve("my download.zip", bible_with_id_lines("World English Bible", "World English Bible"))
        self.assertEqual((version.abbreviation, version.abbreviation_origin), ("WEB", INITIALS))


class FormatTests(unittest.TestCase):
    def test_osis_work_ids(self) -> None:
        self.assertEqual(work_abbreviation("Bible.en.kjv"), "KJV")
        self.assertEqual(work_abbreviation("SAMPLE"), "SAMPLE")
        self.assertIsNone(work_abbreviation(" "))

    def test_id_descriptions_are_read_in_every_marker_format(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            for fmt in ("usfm", "usx", "usj"):
                name, content = SAMPLES[fmt]
                path = Path(folder) / name
                path.write_text(content, encoding="utf-8")
                bible = parse_file(path, fmt)
                with self.subTest(fmt):
                    self.assertEqual(bible.book("PSA").headers["id"], "Sample Bible")
                    # The description is not verse text.
                    self.assertNotIn("Sample", " ".join(v.text for v in bible.verses()))
        self.assertIn(r"\id PSA Sample Bible", USFM)


if __name__ == "__main__":
    unittest.main()
