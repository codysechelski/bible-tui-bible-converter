"""Verse text normalization rules shared by every parser.

The rules are documented in `docs/normalization.md`. In short: parsers drop non verse blocks and
inline content using the marker sets below, collect the remaining text of a verse as one fragment per
line or paragraph, and pass the fragments to `normalize_verse_text`, which joins them with a single
space, removes paragraph marks and cleans up whitespace.
"""

from __future__ import annotations

import re
from typing import Iterable, Union

# USFM marker names (without the backslash or a trailing level number). USX `style` attributes and
# USJ `marker` values use the same names, so these sets serve the USFM, USX and USJ parsers.

# Paragraph-level markers whose whole content is not verse text: identification and headers, book
# titles, section headings, references under headings, speaker labels, Psalm titles and book
# introductions.
NON_VERSE_BLOCK_MARKERS = frozenset(
    {
        # identification and headers
        "id", "ide", "h", "toc", "toca", "rem", "sts", "usfm",
        # book titles
        "mt", "mte",
        # headings and titles
        "ms", "mr", "s", "sr", "r", "sp", "sd", "d", "cl", "cd", "lit", "qa",
        # book introductions
        "imt", "imte", "is", "ip", "ipi", "im", "imi", "ipq", "imq", "ipr", "iq", "ib", "ili", "iot",
        "io", "iex", "ie",
    }
)

# Inline markers whose content is removed from the verse: footnotes, endnotes, cross references,
# study notes, figures, inline quotation references and alternate or published verse and chapter
# numbers.
DROPPED_INLINE_MARKERS = frozenset({"f", "fe", "ef", "x", "ex", "fig", "rq", "va", "vp", "ca", "cp"})

# OSIS equivalents: elements removed together with their content, and `div` types removed whole.
OSIS_DROPPED_ELEMENTS = frozenset({"title", "note", "figure", "speaker"})
OSIS_DROPPED_DIV_TYPES = frozenset({"introduction", "front", "back"})

# The separator placed between the lines or paragraphs that make up one verse.
LINE_SEPARATOR = " "

# Whitespace collapsed to a single space: every Unicode space except the no-break spaces, which
# some translations use deliberately (for example before French punctuation).
_COLLAPSIBLE_WHITESPACE = re.compile(r"[^\S   ]+")
_LEVEL_SUFFIX = re.compile(r"\d+$")

# Characters removed from verse text: the pilcrow `¶` that some editions (eBible.org's KJV) keep as a
# paragraph mark at the start of a verse. It is layout, not verse text, and the OSIS export of the same
# Bible already leaves it out.
_REMOVED_CHARACTERS = re.compile("\u00b6")


class EmptyVerseError(ValueError):
    """A verse whose text is empty after normalization."""


def marker_base(marker: str) -> str:
    """Return a marker name without a leading backslash, closing star or trailing level number."""
    return _LEVEL_SUFFIX.sub("", marker.strip().lstrip("\\").rstrip("*").lower())


def is_non_verse_block(marker: str) -> bool:
    return marker_base(marker) in NON_VERSE_BLOCK_MARKERS


def is_dropped_inline(marker: str) -> bool:
    return marker_base(marker) in DROPPED_INLINE_MARKERS


def normalize_verse_text(fragments: Union[str, Iterable[str]], location: str = "verse") -> str:
    """Join a verse's line or paragraph fragments and normalize its whitespace.

    Raises `EmptyVerseError`, naming `location`, when nothing but whitespace remains.
    """
    if isinstance(fragments, str):
        fragments = [fragments]
    text = LINE_SEPARATOR.join(fragments)
    text = _REMOVED_CHARACTERS.sub("", text)
    text = _COLLAPSIBLE_WHITESPACE.sub(" ", text).strip()
    if not text:
        raise EmptyVerseError(f"{location} has no text after normalization")
    return text
