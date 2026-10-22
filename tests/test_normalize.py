from __future__ import annotations

import unittest

from bibles.books import UnknownBookError
from bibles.model import Bible, DuplicateVerseError
from bibles.normalize import (
    EmptyVerseError,
    LINE_SEPARATOR,
    is_dropped_inline,
    is_non_verse_block,
    marker_base,
    normalize_verse_text,
)


class NormalizeVerseTextTests(unittest.TestCase):
    def test_poetry_lines_join_with_single_space(self) -> None:
        # Psalm 23:2 split across two \q lines.
        lines = ["He makes me lie down in green pastures.\n", "\tHe leads me beside still waters."]
        self.assertEqual(
            normalize_verse_text(lines),
            "He makes me lie down in green pastures. He leads me beside still waters.",
        )
        self.assertEqual(LINE_SEPARATOR, " ")

    def test_text_left_after_removing_a_footnote(self) -> None:
        # "\v 1 In the beginning \f + \ft Or When God began\f* God created ..." with the note removed.
        self.assertEqual(
            normalize_verse_text("In the beginning  God created the heavens and the earth. "),
            "In the beginning God created the heavens and the earth.",
        )

    def test_whitespace_is_collapsed_and_trimmed(self) -> None:
        self.assertEqual(normalize_verse_text("  Jesus\r\n  wept.\t "), "Jesus wept.")
        self.assertEqual(normalize_verse_text(["", "Jesus wept.", "  "]), "Jesus wept.")

    def test_no_break_spaces_are_kept_inside_text(self) -> None:
        self.assertEqual(normalize_verse_text("Dieu ; il"), "Dieu ; il")
        self.assertEqual(normalize_verse_text(" amen "), "amen")

    def test_empty_verse_raises_named_error(self) -> None:
        for fragments in ("", "  \n ", [], ["", "\t"]):
            with self.assertRaises(EmptyVerseError):
                normalize_verse_text(fragments)
        with self.assertRaisesRegex(EmptyVerseError, "JHN 11:35"):
            normalize_verse_text(" ", "JHN 11:35")


class MarkerRuleTests(unittest.TestCase):
    def test_marker_base(self) -> None:
        self.assertEqual(marker_base("\\s1"), "s")
        self.assertEqual(marker_base("toc2"), "toc")
        self.assertEqual(marker_base("\\f*"), "f")
        self.assertEqual(marker_base("IMT"), "imt")

    def test_non_verse_blocks(self) -> None:
        for marker in ("id", "h", "toc1", "mt1", "ms", "s", "s2", "r", "sp", "d", "cl", "is1", "ip", "imt2"):
            self.assertTrue(is_non_verse_block(marker), marker)
        for marker in ("p", "m", "q1", "q2", "pi", "li1", "b", "nb", "v", "c"):
            self.assertFalse(is_non_verse_block(marker), marker)

    def test_dropped_inline_markers(self) -> None:
        for marker in ("f", "fe", "x", "fig", "rq", "va", "vp", "ca", "cp"):
            self.assertTrue(is_dropped_inline(marker), marker)
        for marker in ("wj", "add", "nd", "w", "it", "bk", "qs", "tl"):
            self.assertFalse(is_dropped_inline(marker), marker)


class BibleModelTests(unittest.TestCase):
    def test_add_verse_builds_books_chapters_and_verses(self) -> None:
        bible = Bible()
        bible.add_verse("psa", 23, 1, ["The Lord is my shepherd;", "I shall not want."])
        bible.add_verse("PSA", 23, 2, "He makes me lie down in green pastures.")
        bible.add_verse("GEN", 1, 1, "In the beginning, God created the heavens and the earth.")

        self.assertEqual([b.code for b in bible.books], ["PSA", "GEN"])
        psalms = bible.books[0]
        self.assertEqual(psalms.book.sort_order, 19)
        self.assertEqual([c.number for c in psalms.chapters], [23])
        first = psalms.chapters[0].verses[0]
        self.assertEqual(
            (first.book_code, first.chapter_number, first.verse_number, first.text),
            ("PSA", 23, 1, "The Lord is my shepherd; I shall not want."),
        )
        self.assertEqual(first.reference, "PSA 23:1")
        self.assertEqual([v.reference for v in bible.verses()], ["PSA 23:1", "PSA 23:2", "GEN 1:1"])

    def test_add_verse_errors(self) -> None:
        bible = Bible()
        bible.add_verse("JHN", 11, 35, "Jesus wept.")
        with self.assertRaises(DuplicateVerseError):
            bible.add_verse("jhn", 11, 35, "Jesus wept.")
        with self.assertRaises(UnknownBookError):
            bible.add_verse("TOB", 1, 1, "text")
        with self.assertRaisesRegex(EmptyVerseError, "JHN 11:36"):
            bible.add_verse("JHN", 11, 36, "   ")
        self.assertEqual(len(list(bible.verses())), 1)


if __name__ == "__main__":
    unittest.main()
