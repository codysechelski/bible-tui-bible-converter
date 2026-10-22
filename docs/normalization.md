# Verse text normalization

Every parser must produce the same verse text for the same Bible, whatever the source format. The database
stores one plain text column per verse, so anything that is not verse text is removed and the rest is
flattened to a single line. The rules live in `bibles/normalize.py`; parsers add verses through
`Bible.add_verse` in `bibles/model.py`, which applies them.

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
| Headings and titles | `ms#`, `mr`, `s#`, `sr`, `r`, `sp`, `sd#`, `d`, `cl`, `cd`, `lit` |
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
(`OSIS_DROPPED_ELEMENTS`, `OSIS_DROPPED_DIV_TYPES`). Text inside other elements is kept.

**VPL** has no markup; only the whitespace rules apply.

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

## 3. Normalize whitespace

- Each run of whitespace (spaces, tabs, newlines and other Unicode spaces) becomes one space.
- No-break spaces (U+00A0, U+2007, U+202F) inside the text are kept, because some translations use them
  on purpose, for example before French punctuation.
- Leading and trailing whitespace is removed.
- Punctuation is not changed.

## 4. Errors

- A verse whose text is empty after these rules raises `EmptyVerseError`, naming the verse (for example
  `JHN 11:35`). The tool never writes an empty verse.
- Adding the same book, chapter and verse twice raises `DuplicateVerseError`.
- A book code outside the 66 canonical books raises `UnknownBookError` (see `bibles/books.py`).
