# bibles

`bibles` converts a text-formatted Bible (USFM, USX, OSIS, VPL, USJ or RTF) into a SQLite database that the
custom Bible terminal UI can read. The source can be a single file, a folder of book files, or the zip archive a
Bible download usually comes as. The database uses exactly the schema of the reference project
(`bible-esv/bible_esv.sqlite`), so the TUI opens it without changes.

It is Python 3.9+ and standard library only, so it runs anywhere the TUI does.

## Repository layout

The repository is both the converter and a collection of the databases it produces, in two top-level
directories:

- [`bibles/`](bibles) holds the converted `.sqlite` Bible databases, ready to open. A conversion without
  `--output` is written here.
- [`tool/`](tool) holds the converter: the `bibles` package, the `tool/bin/bibles` wrapper, the tests, the
  [documentation](tool/docs) and the [samples](tool/samples/README.md).

The commands below are run from the repository root. The wrapper works from any directory, and
`python3 -m bibles` works from inside `tool/`.

## Converted Bibles

These databases are in `bibles/`. Open one with the TUI directly; nothing needs converting first.

| File | Translation | Books, chapters, verses | Licence |
| --- | --- | --- | --- |
| `bibles/bible_kjv.sqlite` | King James Version (1769 standardized text) | 66, 1189, 31102 | Public domain (outside the United Kingdom, where the Crown's letters patent restrict printing) |
| `bibles/bible_asv.sqlite` | American Standard Version (1901) | 66, 1189, 31086 | Public domain |

Where each one came from:

| File | Source | Source files dated | SHA-256 of the downloaded zip |
| --- | --- | --- | --- |
| `bibles/bible_kjv.sqlite` | eBible.org [`eng-kjv_usfm.zip`](https://ebible.org/Scriptures/eng-kjv_usfm.zip) ([details](https://ebible.org/find/details.php?id=eng-kjv)) | 2026-09-26 | `67561758cf58d9e767e89226a99171dba722579157d3894767c2f27538bcb38e` |
| `bibles/bible_asv.sqlite` | eBible.org [`eng-asv_usfm.zip`](https://ebible.org/Scriptures/eng-asv_usfm.zip) ([details](https://ebible.org/find/details.php?id=eng-asv)) | 2026-10-20 | `5e385a1a89887849cb07c88ddf4df37708e0fa901b1f1b7f0b8204c153f0a901` |

Both copyright pages shipped in the zips (`copr.htm`) state the text is public domain and may be copied freely.
Notes on the content:

- The KJV zip also holds the Apocrypha and front matter; those books are skipped, leaving the 66. The `¶`
  paragraph marks that eBible.org keeps in the text are kept.
- The ASV leaves out 16 New Testament verses that later manuscripts add (Matthew 17:21, Acts 8:37 and others).
  They are absent rather than empty, so validation warns about the verse gaps and the totals.

### Adding a Bible

1. Pick a source whose licence allows redistribution, and download it. Convert the downloaded zip as it is
   (or the folder it unzips to). Without a Digital Bible Library `metadata.xml` in the bundle, the source
   name becomes the `version` the TUI shows, so name the copy after the translation's short name:

   ```sh
   cp eng-web_usfm.zip WEB.zip
   tool/bin/bibles WEB.zip -n bible_web        # writes bibles/bible_web.sqlite (version WEB)
   ```

2. Check the run's warnings: skipped books should be only non-canonical ones, and missing verses should be
   ones the translation genuinely omits. The conversion fails if any validation check fails.
3. Add the database to both tables above (source URL, date of the source files, SHA-256 of the download,
   licence) and to `COLLECTION` in `tool/tests/test_collection.py`, which checks that every database in
   `bibles/` is listed, validates and matches the reference schema.
4. Commit the `.sqlite` file in `bibles/`. Re-converting the same download must give the same books, chapters and verses;
   only `created_at_utc` changes.

## Quick start

```sh
tool/bin/bibles kjv.usfm                      # writes bibles/kjv.sqlite
tool/bin/bibles eng-kjv_usfm.zip -n kjv       # a whole download, one file per book, as it came
tool/bin/bibles eng-kjv_usfm/ -n kjv          # the same, unzipped
tool/bin/bibles --validate bibles/kjv.sqlite  # checks an existing database
cd tool && python3 -m bibles ../kjv.usfm      # the same, as a module
```

A run reports each stage:

```
Source: kjv.usfm
Format: usfm (detected from content)
Parser: bibles.parsers.usfm
Warning: skipped book TOB: not one of the 66 canonical books
Validating: /home/me/bibles/bibles/kjv.sqlite
  PASS  Schema tables: metadata, books, chapters, verses
  PASS  SQLite integrity: ok
  ...
Validation passed: 15 checks, 0 failed, 0 warnings
Output: /home/me/bibles/bibles/kjv.sqlite
Wrote 66 books, 1189 chapters and 31102 verses (version kjv)
```

## Usage

```sh
tool/bin/bibles SOURCE [-o OUTPUT] [-n NAME] [-f {usfm,usx,osis,vpl,usj,rtf}] [--allow-partial]
tool/bin/bibles --validate DATABASE [--allow-partial]
```

| Option | Meaning |
| --- | --- |
| `SOURCE` | The source Bible (required): a file, a folder of book files (subfolders included), or a zip archive of one. With `--validate`, the database to check. |
| `-o, --output` | Output directory or full output file path, relative to the current directory. Defaults to `bibles/` at the repository root, wherever the command is run from. |
| `-n, --name` | Output file name inside the output directory. Defaults to the source base name (a file's or zip's name without its extension, a folder's name) with `.sqlite`; `.sqlite` is appended when the name has no extension. |
| `-f, --format` | Force a format instead of detecting it: `usfm`, `usx`, `osis`, `vpl`, `usj` or `rtf`. For a folder or zip, only the files in that format are used. |
| `--allow-partial` | Accept a Bible with fewer than 66 books (a New Testament, or a sample). Missing books become a warning. |
| `--validate` | Validate an existing database instead of converting. Cannot be combined with `-o`, `-n` or `-f`. |
| `--version`, `-h` | Print the version or the help. |

How `--output` is interpreted:

- Without `--output`, the database goes into the repository's `bibles/` directory (created if missing), so
  every conversion joins the collection unless you send it elsewhere. `--name` alone only changes the file name.

- An existing directory, a path ending in `/`, or a path without a file extension is a **directory**; the file
  name is placed inside it. Missing directories are created (and removed again if the run fails).
- Anything else (for example `build/kjv.db`) is a **full file path** and is used directly. `--name` cannot be
  combined with a full file path.
- An existing output file is replaced, but only once the new database has been written and validated.

```sh
tool/bin/bibles kjv.usfm                      # bibles/kjv.sqlite
tool/bin/bibles kjv.usfm -n king-james        # bibles/king-james.sqlite
tool/bin/bibles kjv.usfm -o build/            # ./build/kjv.sqlite
tool/bin/bibles kjv.usfm -o build/bible.db    # ./build/bible.db
```

Exit status: 0 on success (warnings allowed), 1 when the conversion or validation fails, 2 for a usage error
or no arguments. A failure names its stage (`detect`, `parse`, `write` or `validate`), and no database is left
at the output path.

## Examples for each format

The [`tool/samples/`](tool/samples/README.md) directory has the same three KJV books in every format, and
the same books of the ASV as RTF files in a folder. They hold 3 books rather than 66, hence `--allow-partial`;
a whole Bible needs no flag.

```sh
tool/bin/bibles tool/samples/kjv.usfm     --allow-partial -o build/kjv-usfm.sqlite   # USFM
tool/bin/bibles tool/samples/kjv.usx      --allow-partial -o build/kjv-usx.sqlite    # USX
tool/bin/bibles tool/samples/kjv.osis.xml --allow-partial -o build/kjv-osis.sqlite   # OSIS
tool/bin/bibles tool/samples/kjv.vpl.txt  --allow-partial -o build/kjv-vpl.sqlite    # VPL
tool/bin/bibles tool/samples/kjv.usj      --allow-partial -o build/kjv-usj.sqlite    # USJ
tool/bin/bibles tool/samples/asv-rtf/     --allow-partial -o build/asv-rtf.sqlite    # RTF, a folder of books
```

## Folders and zip archives

Bible downloads usually come as a zip with one file per book, next to metadata, stylesheets and licences (a
Digital Bible Library bundle, an eBible.org zip). Give the zip itself, or the folder it unzips to:

```sh
tool/bin/bibles "Biblia Livre Para Todos.zip" --allow-partial -n bible_blt
```

```
Source: Biblia Livre Para Todos.zip
Input: zip archive, 27 usx files in release/USX_1; 5 other files ignored
Format: usx (detected from content)
...
Wrote 27 books, 260 chapters and 7942 verses (version BLT)
```

- The folder and its subfolders are searched. Every file whose format is detected is a book file; the rest
  (metadata, stylesheets, versification, licences) are ignored. A zip is unpacked into a temporary folder that
  is removed when the run ends.
- The book files must all be in one format; when they are not, the run lists what it found and `--format`
  picks one.
- Front matter, glossaries and the Apocrypha are skipped with a warning. A book found again in another file with
  identical text is kept once (the KJV bundle carries every book twice); copies that differ fail the run.
- A Digital Bible Library `metadata.xml` supplies the version (`BLT` above) and its name.

See [folders and zip archives](tool/docs/sources.md) for the details, including the RTF layout.

## Supported formats

| Format | Typical files | What is read |
| --- | --- | --- |
| [USFM](https://ubsicap.github.io/usfm/) | `.usfm`, `.sfm` | `\id` starts a book, `\c` a chapter, `\v` a verse; the verse runs until the next verse, chapter or book. Several books may follow each other in one file. |
| [USX](https://ubsicap.github.io/usx/) | `.usx`, `.xml` | A `<usx>` document: `<book code>`, `<chapter number>` / `sid`, `<verse number>` / `sid`, with `eid` end milestones. USX 2 and 3. |
| [OSIS](https://crosswire.org/osis/) | `.osis`, `.xml` | Verse elements identified by `osisID` (`Gen.1.1`), as containers or `sID`/`eID` milestones, in any namespace. Version name from the header. |
| VPL | `.vpl`, `.txt` | One verse per line: `GEN 1:1 text` or `GEN.1.1 text`. The book may be a USFM code, an OSIS code, a book name or an eBible.org code (`SOL`, `JOH`, ...). |
| [USJ](https://docs.usfm.bible/usfm/latest/usj/) | `.usj`, `.json` | A JSON object with `"type": "USJ"` whose `content` holds book, chapter, verse, para, char and note nodes. |
| RTF | `.rtf` | One book per file, as in the ASV bundle: headings such as `Ruth 1` start chapters, bold numbers start verses. See [RTF book files](tool/docs/sources.md#rtf-book-files). |

### Format detection

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

### Known limitations

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
- **RTF.** Only the layout described in [RTF book files](tool/docs/sources.md#rtf-book-files) is understood, one
  book per file. Textual notes, section headings, Psalm titles and the Psalm 119 acrostic letters are dropped,
  but a line after a chapter's last verse (Habakkuk 3's subscription in the ASV) stays in that verse.

## Verse text

The schema stores one plain text column per verse, so every parser applies the same rules (see
[normalization](tool/docs/normalization.md) for the full list):

- Headings, titles, book introductions, footnotes, endnotes, cross references and figures are removed.
- Character formatting (`\nd LORD\nd*`, `<char style="wj">`, `<w>`) keeps its text and loses its markup; word
  attributes such as Strong's numbers are dropped.
- Poetry lines and paragraphs within a verse are joined with a single space.
- Whitespace is collapsed to single spaces and trimmed; no-break spaces inside the text are kept. Punctuation
  is never changed. No verse is ever empty.

Because USFM, USX and USJ share one marker handler, the same Bible in those formats produces identical text;
the test suite checks this with real files.

## Output schema

The database matches the reference schema exactly (a test compares the two):

| Table | Columns | Notes |
| --- | --- | --- |
| `metadata` | `key TEXT PRIMARY KEY`, `value TEXT NOT NULL` | One row per key, listed below. |
| `books` | `id INTEGER PRIMARY KEY`, `sort_order INTEGER NOT NULL UNIQUE`, `canonical_name TEXT NOT NULL UNIQUE`, `common_name TEXT NOT NULL`, `slug TEXT NOT NULL UNIQUE`, `testament TEXT NOT NULL CHECK (testament IN ('old', 'new'))` | `id` equals `sort_order` (1 to 66; Old Testament 1 to 39). `canonical_name` is for example `I Samuel`, `common_name` `1 Samuel`, `slug` `1-samuel`. |
| `chapters` | `id INTEGER PRIMARY KEY`, `book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE`, `chapter_number INTEGER NOT NULL` | `UNIQUE (book_id, chapter_number)`. Numbered from 1 with no gaps. |
| `verses` | `id INTEGER PRIMARY KEY`, `book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE`, `chapter_id INTEGER NOT NULL REFERENCES chapters(id) ON DELETE CASCADE`, `chapter_number INTEGER NOT NULL`, `verse_number INTEGER NOT NULL`, `text TEXT NOT NULL` | `UNIQUE (book_id, chapter_number, verse_number)`. `chapter_number` repeats the chapter row's number for direct lookups. |

Relationships: each chapter belongs to a book; each verse belongs to a book and a chapter, and deleting a book
or chapter deletes its rows. Indexes: `idx_books_testament_order (testament, sort_order)`,
`idx_chapters_book_number (book_id, chapter_number)`,
`idx_verses_book_chapter_verse (book_id, chapter_number, verse_number)` and
`idx_verses_chapter_number (chapter_id, verse_number)`.

Metadata keys:

| Key | Value |
| --- | --- |
| `version` | Short version name from the source (OSIS `osisIDWork`, or a bundle's DBL `metadata.xml` abbreviation), otherwise the source name without its extension. The TUI shows it. |
| `version_name` | Full version name from the source (OSIS work title, or the DBL bundle name), otherwise `version`. |
| `source` | Source file, folder or zip name and format, for example `kjv.usfm (usfm)`. |
| `created_at_utc` | When the database was written, ISO 8601 in UTC, for example `2026-10-22T14:30:05+00:00`. |
| `book_count`, `chapter_count`, `verse_count` | The number of rows written. |

## Validation

Every conversion validates the database before moving it into place, and `--validate` checks an existing one:
SQLite integrity, foreign keys, metadata, 66 books in canonical order with the right names and testaments,
contiguous chapters, chapters with verses, duplicate and empty verses, and verse to chapter links fail; verse
gaps, unusual chapter counts and totals different from the reference only warn. Every check is listed with its
result. See [validation](tool/docs/validation.md).

## Documentation

- [Verse text normalization](tool/docs/normalization.md): how headings, notes, poetry lines, whitespace, verse
  ranges and absent verses are handled.
- [Folders and zip archives](tool/docs/sources.md): how book files are found and combined, and the RTF layout.
- [Database validation](tool/docs/validation.md): every check, and which ones fail or only warn.
- [Samples](tool/samples/README.md): where the sample files come from and how they differ.
- [AGENTS.md](AGENTS.md): conventions and commands for contributors and coding agents.

## Development

Requires Python 3.9 or newer (developed on 3.12). No third-party packages.

```sh
python3 -m unittest discover -s tool/tests -t tool                               # run the test suite
python3 -m py_compile tool/bibles/*.py tool/bibles/parsers/*.py tool/tests/*.py  # syntax check
```

Some tests compare against the reference project at `../bible-esv` (`bible_esv.sqlite` and `tui/bible_tui.py`);
they are skipped when it is not present.
