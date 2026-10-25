# Supported formats

| Format | Typical files | What is read |
| --- | --- | --- |
| [USFM](https://ubsicap.github.io/usfm/) | `.usfm`, `.sfm` | `\id` starts a book, `\c` a chapter, `\v` a verse; the verse runs until the next verse, chapter or book. Several books may follow each other in one file. |
| [USX](https://ubsicap.github.io/usx/) | `.usx`, `.xml` | A `<usx>` document: `<book code>`, `<chapter number>` / `sid`, `<verse number>` / `sid`, with `eid` end milestones. USX 2 and 3. |
| [OSIS](https://crosswire.org/osis/) | `.osis`, `.xml` | Verse elements identified by `osisID` (`Gen.1.1`), as containers or `sID`/`eID` milestones, in any namespace. Version name from the header. |
| VPL | `.vpl`, `.txt` | One verse per line: `GEN 1:1 text` or `GEN.1.1 text`. The book may be a USFM code, an OSIS code, a book name or an eBible.org code (`SOL`, `JOH`, ...). |
| [USJ](https://docs.usfm.bible/usfm/latest/usj/) | `.usj`, `.json` | A JSON object with `"type": "USJ"` whose `content` holds book, chapter, verse, para, char and note nodes. |
| RTF | `.rtf` | One book per file, as in the ASV bundle: headings such as `Ruth 1` start chapters, bold numbers start verses. See [RTF book files](sources.md#rtf-book-files). |

## Format detection

The content is checked first and always wins over the extension:

- an XML root of `<usx>` is USX, and `<osis>` (or `<osisText>`, any namespace) is OSIS;
- a JSON object with `"type": "USJ"` is USJ;
- a line starting with a USFM marker such as `\id`, `\c` or `\v` is USFM;
- lines starting with a reference such as `Gen 1:1` or `GEN.1.1` are VPL;
- a document starting with `{\rtf` is RTF.

If the content is inconclusive, a format-specific extension (`.usfm`, `.sfm`, `.usx`, `.osis`, `.vpl`, `.usj`,
`.rtf`) is used; `.xml`, `.json` and `.txt` say nothing on their own. Otherwise the run fails, listing the
supported formats. Use `--format` to force a format when detection guesses wrong; the output then says
`Format: usx (forced with --format)`.

## Verse text

The schema stores one plain text column per verse, so every parser applies the same rules (see
[normalization](normalization.md) for the full list):

- Headings, titles, book introductions, footnotes, endnotes, cross references and figures are removed.
- Character formatting (`\nd LORD\nd*`, `<char style="wj">`, `<w>`) keeps its text and loses its markup; word
  attributes such as Strong's numbers are dropped.
- Poetry lines and paragraphs within a verse are joined with a single space.
- Whitespace is collapsed to single spaces and trimmed; no-break spaces inside the text are kept. Punctuation
  is never changed. No verse is ever empty.

Because USFM, USX and USJ share one marker handler, the same Bible in those formats produces identical text;
the test suite checks this with real files.

## Known limitations

- **All formats.** Only the 66 books of the Protestant canon are written; any other book (Apocrypha,
  front matter, glossary) is skipped with a warning. A verse range is stored on its first verse and the later
  verses are absent. A verse a translation omits is left out with a warning. The whole source is read into
  memory, which is fine for a Bible (a full USJ Bible is about 40 MB).
- **USFM.** Psalm titles (`\d`), speaker labels (`\sp`) and acrostic letters (`\qa`) are dropped as headings. A
  file that is not UTF-8 is read as Windows-1252 (or Latin-1) with a warning; the `\ide` marker is not used.
  Peripheral and sidebar content (`\periph`, `\esb`) is skipped.
- **USX.** The same text rules as USFM. Each file is one document; give a folder or zip to convert one file
  per book. Sidebars, peripherals and milestones are skipped.
- **OSIS.** Only text inside a verse element is kept, so Psalm titles (`<title type="psalm">`), headings and
  introductions are dropped. An `osisID` naming several verses uses the first.
- **VPL.** VPL is already rendered text, so any decoration in the file stays in the verse (eBible.org's KJV
  writes added words as `[was]`). A line that is not a verse reference is skipped with a warning; a line with
  no text, or a `<range>` marker, is an absent verse.
- **USJ.** Must be UTF-8 JSON. Both `marker` (the USJ specification) and `mark` are accepted.
- **RTF.** Only the layout described in [RTF book files](sources.md#rtf-book-files) is understood, one book
  per file. Textual notes, section headings, Psalm titles and the Psalm 119 acrostic letters are dropped, but a
  line after a chapter's last verse (Habakkuk 3's subscription in the ASV) stays in that verse.
