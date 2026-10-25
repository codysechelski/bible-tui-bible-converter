"""The translation's own book names (`bibles/booknames.py`) and where each format keeps them."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from bibles.booknames import apply_book_names, is_english
from bibles.model import Bible
from bibles.parsers import parse_file
from bibles.pipeline import convert
from bibles.sources import read_dbl_books
from tests.test_samples import SAMPLES

PORTUGUESE_USFM = r"""\id GEN Bíblia Livre - Textus Receptus
\h Gênesis
\toc1 O Livro de Gênesis
\toc2 Gênesis
\c 1
\p \v 1 No princípio criou Deus os céus e a terra.
\id EXO Bíblia Livre - Textus Receptus
\h Êxodo
\c 1
\p \v 1 Estes, pois, são os nomes dos filhos de Israel.
\id RUT Bíblia Livre - Textus Receptus
\c 1
\p \v 1 E aconteceu nos dias em que os juízes julgavam.
"""

METADATA = """<?xml version="1.0" encoding="utf-8"?>
<DBLMetadata version="2.2.1" id="0123456789abcdef" revision="1">
  <identification><name>Bíblia Livre</name><abbreviation>BLIVRE</abbreviation></identification>
  <language><iso>por</iso></language>
  <names>
    <name id="book-gen"><abbr>Gn</abbr><short>Gênesis (DBL)</short><long>Gênesis</long></name>
    <name id="book-tob"><short>Tobias</short></name>
    <name id="book-exo"><long>Êxodo</long></name>
  </names>
</DBLMetadata>
"""


def bible_named(*names: str) -> Bible:
    bible = Bible()
    for code, name in zip(("GEN", "EXO", "LEV", "NUM"), names):
        bible.add_verse(code, 1, 1, "Text.")
        bible.book(code).headers["toc2"] = name
    return bible


class ApplyBookNamesTests(unittest.TestCase):
    source = Path("/downloads/bible.usfm")

    def names(self, bible: Bible):
        return [b.common_name for b in bible.books]

    def test_names_that_are_not_english_are_used(self) -> None:
        bible = bible_named("Gênesis", "Êxodo", "Levítico")
        result = apply_book_names(bible, self.source)
        self.assertTrue(result.translated)
        self.assertEqual(self.names(bible), ["Gênesis", "Êxodo", "Levítico"])
        self.assertEqual(result.describe(),
                         "the translation's own, for 3 books (most of the source's book names are not English)")

    def test_english_names_are_kept_from_books_py(self) -> None:
        # "Psalm" and the like differ from books.py, but most names are English, so books.py wins.
        bible = bible_named("GENESIS", "Exodus", "Leviticus", "Numbers in the Desert")
        result = apply_book_names(bible, self.source)
        self.assertFalse(result.translated)
        self.assertEqual(self.names(bible), ["Genesis", "Exodus", "Leviticus", "Numbers"])
        self.assertEqual(result.describe(), "English (the source's book names are English)")

    def test_a_known_language_decides(self) -> None:
        bible = bible_named("Genesis", "Exodus")
        result = apply_book_names(bible, self.source, metadata_language="por")
        self.assertTrue(result.translated)
        self.assertEqual(result.describe(), "the translation's own, for 2 books (language por from metadata.xml)")
        bible = bible_named("Gênesis", "Êxodo")
        bible.language = "en-US"
        result = apply_book_names(bible, self.source, "from the OSIS header")
        self.assertFalse(result.translated)
        self.assertEqual(self.names(bible), ["Genesis", "Exodus"])
        self.assertEqual(result.describe(), "English (language en-US from the OSIS header)")

    def test_language_from_the_source_name(self) -> None:
        bible = bible_named("Gênesis", "Êxodo")
        result = apply_book_names(bible, Path("/downloads/Bíblia Livre [eng] BL.zip"))
        self.assertFalse(result.translated)
        self.assertEqual(result.language_origin, "from the source name")

    def test_metadata_names_come_first_and_books_without_a_name_stay_english(self) -> None:
        bible = bible_named("Gênesis", "Êxodo")
        bible.add_verse("LEV", 1, 1, "Text.")
        apply_book_names(bible, self.source, metadata_names={"GEN": "Gênesis (DBL)"})
        self.assertEqual(self.names(bible), ["Gênesis (DBL)", "Êxodo", "Leviticus"])

    def test_no_names_is_english(self) -> None:
        bible = Bible()
        bible.add_verse("GEN", 1, 1, "Text.")
        result = apply_book_names(bible, self.source, metadata_language="por")
        self.assertFalse(result.translated)
        self.assertEqual(self.names(bible), ["Genesis"])

    def test_is_english(self) -> None:
        for code in ("en", "eng", "EN-gb", "en_US"):
            self.assertTrue(is_english(code), code)
        for code in ("por", "pt-BR", "enm-x"):
            self.assertFalse(is_english(code), code)


class FormatTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_marker_formats_record_toc2_and_h(self) -> None:
        path = self.tmp / "por.usfm"
        path.write_text(PORTUGUESE_USFM, encoding="utf-8")
        bible = parse_file(path, "usfm")
        self.assertEqual(bible.book("GEN").headers, {"id": "Bíblia Livre - Textus Receptus", "h": "Gênesis",
                                                     "toc2": "Gênesis"})
        self.assertEqual(bible.book("EXO").headers["h"], "Êxodo")
        self.assertNotIn("Gênesis", bible.book("GEN").chapters[0].verses[0].text)

    def test_osis_short_titles_and_language(self) -> None:
        bible = parse_file(SAMPLES / "kjv.osis.xml", "osis")
        self.assertEqual(bible.language, "en")
        self.assertEqual([b.headers.get("toc2") for b in bible.books], ["Ruth", "Jonah", "3 John"])

    def test_rtf_title_heading(self) -> None:
        bible = parse_file(SAMPLES / "asv-rtf" / "RUT.rtf", "rtf")
        self.assertEqual(bible.book("RUT").headers["h"], "Ruth")

    def test_dbl_language_and_names(self) -> None:
        path = self.tmp / "metadata.xml"
        path.write_text(METADATA, encoding="utf-8")
        self.assertEqual(read_dbl_books(path), ("por", {"GEN": "Gênesis (DBL)", "EXO": "Êxodo"}))

    def test_conversion_writes_the_translation_names(self) -> None:
        source = self.tmp / "por.usfm"
        source.write_text(PORTUGUESE_USFM, encoding="utf-8")
        output = self.tmp / "por.sqlite"
        result = convert(source, output, allow_partial=True)
        self.assertTrue(result.book_names.translated)
        conn = sqlite3.connect(output)
        try:
            rows = conn.execute("SELECT canonical_name, common_name, slug FROM books ORDER BY sort_order").fetchall()
        finally:
            conn.close()
        self.assertEqual(rows, [("Genesis", "Gênesis", "genesis"), ("Exodus", "Êxodo", "exodus"),
                                ("Ruth", "Ruth", "ruth")])


if __name__ == "__main__":
    unittest.main()
