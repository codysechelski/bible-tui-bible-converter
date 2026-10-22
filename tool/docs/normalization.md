# Verse text normalization

Every parser must produce the same verse text for the same Bible, whatever the source format. The database
stores one plain text column per verse, so anything that is not verse text is removed and the rest is
flattened to a single line. The rules live in `bibles/normalize.py`. The parsers in `bibles/parsers/` apply
them: USFM, USX and USJ all feed one shared marker handler (`bibles/parsers/markers.py`), so the three produce
identical text, and every parser adds verses through `Bible.add_verse` in `bibles/model.py`.

The output matches the reference ESV database: one line per verse, poetry lines joined with a space, no
newlines, no doubled spaces, no leading or trailing whitespace, and no empty verses.

## 1. Remove non verse content

USFM, USX and USJ share the USFM marker vocabulary (`\s1`, `<para style="s1">`, `"marker": "s1"`), so one set
of marker names covers all three. A trailing level number is ignored, so `s`, `s1` and `s2` are all
headings.

**Blocks dropped whole** (`NON_VERSE_BLOCK_MARKERS`):

| Kind | Markers |
| --- | --- |
| Identification and headers | `id`, `ide`, `h`, `toc#`, `toca#`, `rem`, `sts`, `usfm` |
| Book titles | `mt#`, `mte#` |
| Headings and titles | `ms#`, `mr`, `s#`, `sr`, `r`, `sp`, `sd#`, `d`, `cl`, `cd`, `lit`, `qa` (acrostic letters) |
| Book introductions | `imt#`, `imte#`, `is#`, `ip`, `ipi`, `im`, `imi`, `ipq`, `imq`, `ipr`, `iq#`, `ib`, `ili#`, `iot`, `io#`, `iex`, `ie` |

**Inline content dropped** (`DROPPED_INLINE_MARKERS`), together with everything inside it:

| Kind | Markers |
| --- | --- |
| Footnotes and endnotes | `f`, `fe`, `ef` (USX/USJ `note` elements) |
| Cross references | `x`, `ex` |
| Figures | `fig` (USX/USJ `figure`) |
| Inline quotation references | `rq` |
| Alternate and published numbers | `va`, `vp`, `ca`, `cp` |

**Kept**: the text of every other character marker (`wj`, `add`, `nd`, `qs`, `tl`, `bk` and so on) stays in
the verse; only the markup is removed. For `\w word|lemma="..."\w*` only `word` is kept.

**OSIS**: `title`, `note` (footnotes and cross references), `figure` and `speaker` elements are removed with
their content, as are `div` elements of type `introduction`, `front` and `back`
(`OSIS_DROPPED_ELEMENTS`, `OSIS_DROPPED_DIV_TYPES`) and the `header`. Only text inside a verse is kept, whether
the verse is a container (`<verse osisID="Gen.1.1">...</verse>`) or a milestone pair (`sID` ... `eID`). Word
markup such as `<w>`, `<transChange>` and `<divineName>` keeps its text. The OSIS namespace is ignored, and
books resolve from OSIS codes (`Gen`, `1Sam`, `Ps`) or USFM codes.

**VPL** has no markup; only the whitespace rules apply. Each line is `BOOK C:V text` or `BOOK.C.V text`, where
`BOOK` is a USFM code, an OSIS code, a book name or one of eBible.org's alternative codes (`SOL`, `EZE`, `JOE`,
`MAR`, `JOH`, `PHI`, `JAM`, `1JO`, `2JO`, `3JO`). A line that is not a verse reference is skipped and
reported as a warning.

**RTF** (one book per file, see [RTF book files](sources.md#rtf-book-files)): heading paragraphs are dropped
after they have started a chapter, and so are textual notes (a paragraph starting with a bold `chapter:verse`
reference), Psalm 119 acrostic letters, text before a chapter's first verse (Psalm titles), and the document's
font, style and information tables, pictures, footnotes and fields. Character formatting such as italics keeps
its text. A verse whose only text is `*` is an omitted verse.

A removed note leaves no text behind, so `word\f + \ft note\f*.` becomes `word.`.

## 2. Join lines and paragraphs

A verse can span several poetry lines (`\q1`, `\q2`) or paragraphs (`\p`, `\m`, `\li`). The parser passes
each piece as a separate fragment, and the fragments are joined with a single space (`LINE_SEPARATOR`). No
newline or other marker is kept.

```
\q1 \v 2 He makes me lie down in green pastures.
\q2 He leads me beside still waters.
```

becomes `He makes me lie down in green pastures. He leads me beside still waters.`

## 3. Normalize whitespace and paragraph marks

- Each run of whitespace (spaces, tabs, newlines and other Unicode spaces) becomes one space.
- No-break spaces (U+00A0, U+2007, U+202F) inside the text are kept, because some translations use them
  on purpose, for example before French punctuation.
- Leading and trailing whitespace is removed.
- The pilcrow `¶`, which some editions (eBible.org's KJV) keep as a paragraph mark at the start of a
  verse, is removed. It marks layout, not text.
- Punctuation is not changed.

## 4. Verse numbering

- **Verse ranges** are kept on the first verse. `\v 1-2 text`, `GEN 1:1-2 text` and
  `<verse osisID="Gen.1.1 Gen.1.2">` all store the whole text as verse 1, and verse 2 is absent. In VPL the
  later verses of a range carry a `<range>` marker, which is skipped.
- **Verse segments** (`\v 3a`, `\v 3b`) are joined into one verse, separated like poetry lines.
- **Absent verses**: a verse with no text after these rules (for example a verse a translation omits, leaving
  only a footnote) is left out and reported as a warning such as `ACT 8:37 has no text and was left out`.
  A blank VPL line, or a VPL reference with no text, is an absent verse and is not reported.

## 5. Errors

- `Bible.add_verse` raises `EmptyVerseError` for an empty verse, naming it (for example `JHN 11:35`); the
  parsers avoid this by leaving absent verses out as described above. The tool never writes an empty verse.
- Adding the same book, chapter and verse twice raises `DuplicateVerseError`.
- A book outside the 66 canonical books (Apocrypha, front matter, glossary) is skipped with a warning such as
  `skipped book TOB: not one of the 66 canonical books`; `bibles/books.py` raises `UnknownBookError` and the
  parsers catch it.
- Parsers raise `ParseError` naming the file and, for USFM and VPL, the line.
