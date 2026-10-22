"""In-memory Bible representation that every parser produces and the SQLite writer consumes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Union

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
    book: Book
    chapters: List[Chapter] = field(default_factory=list)

    @property
    def code(self) -> str:
        return self.book.usfm_code


@dataclass
class Bible:
    """Books, chapters and verses in the order the parser added them."""

    books: List[BibleBook] = field(default_factory=list)
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

    def verses(self) -> Iterator[Verse]:
        for bible_book in self.books:
            for chapter in bible_book.chapters:
                yield from chapter.verses
