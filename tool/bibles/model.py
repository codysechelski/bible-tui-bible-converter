"""In-memory Bible representation that every parser produces and the SQLite writer consumes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional, Union

from bibles.books import Book, book_for_code
from bibles.normalize import normalize_verse_text


class DuplicateVerseError(ValueError):
    """The same book, chapter and verse was added twice."""


@dataclass(frozen=True)
class Verse:
    book_code: str
    chapter_number: int
    verse_number: int
    text: str

    @property
    def reference(self) -> str:
        return f"{self.book_code} {self.chapter_number}:{self.verse_number}"


@dataclass
class Chapter:
    number: int
    verses: List[Verse] = field(default_factory=list)


@dataclass
class BibleBook:
    """A book's chapters, and `headers`: the text of the book's header markers in the source, by
    USFM marker (`id` holds the description after the book code on a `\\id` line, `h` and `toc2` the
    book's name; other formats record their book names under these markers too). `name` is the name
    written as the book's `common_name` when it is not the English one (`bibles/booknames.py`)."""

    book: Book
    chapters: List[Chapter] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    name: Optional[str] = None

    @property
    def common_name(self) -> str:
        return self.name or self.book.common_name

    @property
    def code(self) -> str:
        return self.book.usfm_code


@dataclass
class Bible:
    """Books, chapters and verses in the order the parser added them.

    `version` (a short abbreviation such as "KJV"), `version_name` and `language` (a language code
    such as "en" or "por") are set by parsers whose format supplies them; the writer derives a fallback
    when the version is left as None. `warnings` holds problems a parser worked around (for example a
    skipped line) so the run output can show them.
    """

    books: List[BibleBook] = field(default_factory=list)
    version: Optional[str] = None
    version_name: Optional[str] = None
    language: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    _book_index: Dict[str, BibleBook] = field(default_factory=dict, repr=False, compare=False)
    _chapter_index: Dict[tuple, Chapter] = field(default_factory=dict, repr=False, compare=False)
    _verse_keys: set = field(default_factory=set, repr=False, compare=False)

    def add_verse(
        self,
        book_code: str,
        chapter_number: int,
        verse_number: int,
        fragments: Union[str, Iterable[str]],
    ) -> Verse:
        """Normalize a verse's text fragments and add the verse.

        Raises `UnknownBookError` for a code outside the 66 books, `EmptyVerseError` when the text
        normalizes to nothing, and `DuplicateVerseError` when the verse was already added.
        """
        book = book_for_code(book_code)
        code = book.usfm_code
        location = f"{code} {chapter_number}:{verse_number}"
        key = (code, chapter_number, verse_number)
        if key in self._verse_keys:
            raise DuplicateVerseError(f"{location} appears more than once")
        verse = Verse(code, chapter_number, verse_number, normalize_verse_text(fragments, location))

        bible_book = self._book_index.get(code)
        if bible_book is None:
            bible_book = self._book_index[code] = BibleBook(book)
            self.books.append(bible_book)
        chapter = self._chapter_index.get((code, chapter_number))
        if chapter is None:
            chapter = self._chapter_index[(code, chapter_number)] = Chapter(chapter_number)
            bible_book.chapters.append(chapter)

        chapter.verses.append(verse)
        self._verse_keys.add(key)
        return verse

    def book(self, code: str) -> Optional[BibleBook]:
        return self._book_index.get(code)

    def add_book(self, bible_book: BibleBook) -> None:
        """Add a whole book parsed into another `Bible`; its verse text is already normalized.

        Raises `DuplicateVerseError` when the book was already added.
        """
        code = bible_book.code
        if code in self._book_index:
            raise DuplicateVerseError(f"{code} appears more than once")
        self._book_index[code] = bible_book
        self.books.append(bible_book)
        for chapter in bible_book.chapters:
            self._chapter_index[(code, chapter.number)] = chapter
            self._verse_keys.update((code, chapter.number, verse.verse_number) for verse in chapter.verses)

    def verses(self) -> Iterator[Verse]:
        for bible_book in self.books:
            for chapter in bible_book.chapters:
                yield from chapter.verses
