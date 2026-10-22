from __future__ import annotations

import re
import sqlite3
import unittest
from pathlib import Path

from bibles.books import (
    BOOKS,
    NEW_TESTAMENT,
    OLD_TESTAMENT,
    UnknownBookError,
    book_for_code,
    common_name,
    slugify,
)

REFERENCE_DB = Path("/Users/codysechelski/Developer/Projects/bible-esv/bible_esv.sqlite")
ROMAN_PREFIX = re.compile(r"^(I{1,3}) ")


class BookListTests(unittest.TestCase):
    def test_has_66_books_in_sort_order(self) -> None:
        self.assertEqual(len(BOOKS), 66)
        self.assertEqual([book.sort_order for book in BOOKS], list(range(1, 67)))

    def test_testaments_split_at_39(self) -> None:
        for book in BOOKS:
            expected = OLD_TESTAMENT if book.sort_order <= 39 else NEW_TESTAMENT
            self.assertEqual(book.testament, expected, book.canonical_name)
        self.assertEqual(BOOKS[38].canonical_name, "Malachi")
        self.assertEqual(BOOKS[39].canonical_name, "Matthew")

    def test_codes_names_and_slugs_are_unique(self) -> None:
        for field in ("usfm_code", "canonical_name", "common_name", "slug"):
            values = [getattr(book, field) for book in BOOKS]
            self.assertEqual(len(set(values)), 66, field)

    def test_codes_are_three_character_usfm_ids(self) -> None:
        for book in BOOKS:
            self.assertRegex(book.usfm_code, r"^[1-3A-Z][A-Z]{2}$")

    def test_common_name_converts_roman_prefix(self) -> None:
        for book in BOOKS:
            match = ROMAN_PREFIX.match(book.canonical_name)
            if match:
                arabic = str(len(match.group(1)))
                self.assertEqual(book.common_name, arabic + book.canonical_name[match.end() - 1 :])
            elif book.canonical_name == "Revelation of John":
                self.assertEqual(book.common_name, "Revelation")
            else:
                self.assertEqual(book.common_name, book.canonical_name)

    def test_common_name_examples(self) -> None:
        self.assertEqual(common_name("I Samuel"), "1 Samuel")
        self.assertEqual(common_name("II Kings"), "2 Kings")
        self.assertEqual(common_name("III John"), "3 John")
        self.assertEqual(common_name("Isaiah"), "Isaiah")
        self.assertEqual(common_name("Revelation of John"), "Revelation")

    def test_slug_is_lowercase_dashed_common_name(self) -> None:
        for book in BOOKS:
            self.assertEqual(book.slug, book.common_name.lower().replace(" ", "-"))
        self.assertEqual(slugify("1 Samuel"), "1-samuel")
        self.assertEqual(slugify("Song of Solomon"), "song-of-solomon")
        self.assertEqual(book_for_code("3JN").slug, "3-john")

    def test_chapter_counts(self) -> None:
        self.assertEqual(book_for_code("PSA").chapter_count, 150)
        self.assertEqual(book_for_code("REV").chapter_count, 22)
        self.assertEqual(sum(book.chapter_count for book in BOOKS), 1189)


class BookLookupTests(unittest.TestCase):
    def test_lookup_by_code(self) -> None:
        self.assertEqual(book_for_code("GEN").sort_order, 1)
        self.assertEqual(book_for_code("JHN").canonical_name, "John")
        self.assertEqual(book_for_code("SNG").slug, "song-of-solomon")

    def test_lookup_ignores_case_and_whitespace(self) -> None:
        self.assertIs(book_for_code(" jhn\n"), book_for_code("JHN"))

    def test_unknown_code_raises_named_error(self) -> None:
        for code in ("TOB", "XXA", "", "GENESIS"):
            with self.assertRaises(UnknownBookError) as caught:
                book_for_code(code)
            self.assertEqual(caught.exception.code, code)
            self.assertIn(repr(code), str(caught.exception))

    def test_unknown_book_error_is_a_value_error(self) -> None:
        self.assertTrue(issubclass(UnknownBookError, ValueError))


@unittest.skipUnless(REFERENCE_DB.is_file(), f"reference database not found: {REFERENCE_DB}")
class ReferenceDatabaseAgreementTests(unittest.TestCase):
    def test_books_match_reference_database(self) -> None:
        conn = sqlite3.connect(f"file:{REFERENCE_DB}?mode=ro", uri=True)
        try:
            rows = conn.execute(
                """
                SELECT b.sort_order, b.canonical_name, b.common_name, b.slug, b.testament,
                       COUNT(c.id)
                FROM books b LEFT JOIN chapters c ON c.book_id = b.id
                GROUP BY b.id
                ORDER BY b.sort_order
                """
            ).fetchall()
        finally:
            conn.close()
        expected = [
            (b.sort_order, b.canonical_name, b.common_name, b.slug, b.testament, b.chapter_count)
            for b in BOOKS
        ]
        self.assertEqual(rows, expected)


if __name__ == "__main__":
    unittest.main()
