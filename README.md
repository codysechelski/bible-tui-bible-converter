# bible-tui-bible-converter

<p align="center">
  <a href="https://github.com/codysechelski/bible-tui"><img alt="Companion to bible-tui" src="https://img.shields.io/badge/companion%20to-bible--tui-8A2BE2"></a>
  <a href="AGENTS.md#code-notes"><img alt="Python 3.9+" src="https://img.shields.io/badge/python-3.9%2B-blue"></a>
  <a href="AGENTS.md#code-notes"><img alt="Dependencies: none" src="https://img.shields.io/badge/dependencies-none-brightgreen"></a>
</p>

A companion to [bible-tui](https://github.com/codysechelski/bible-tui), a terminal Bible reader. This repository
converts open Bibles from common text formats (USFM, USX, OSIS, VPL, USJ and RTF) into SQLite databases that
bible-tui can read, and collects the converted databases.

The source can be a single file, a folder of book files, or the zip archive a Bible download usually comes as.
The converter is Python 3.9+ and standard library only, so it runs anywhere Python does.

## Quickstart

New to the command line, or to Bible file formats? The [Quickstart](Quickstart.md) walks you through
downloading a Bible and converting it, step by step.

```sh
tool/bin/bibles ~/Downloads/eng-web_usfm.zip --name bible_web   # writes bibles/bible_web.sqlite
mkdir -p ~/.config/bible-tui/bibles && cp bibles/bible_web.sqlite ~/.config/bible-tui/bibles/   # add it to bible-tui
```

## Repository layout

- [`bibles/`](bibles) holds the converted `.sqlite` databases, ready to use. A conversion without `--output` is
  written here.
- [`tool/`](tool) holds the converter: the `bibles` package, the `tool/bin/bibles` wrapper, the tests, the
  [documentation](tool/docs) and the [samples](tool/samples/README.md).

## Converted Bibles

These databases are in `bibles/`, ready to use; nothing needs converting first.

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

- The KJV zip also holds the Apocrypha and front matter; those books are skipped, leaving the 66. The `¶`
  paragraph marks that eBible.org keeps at the start of some verses are removed.
- The ASV leaves out 16 New Testament verses that later manuscripts add (Matthew 17:21, Acts 8:37 and others).
  They are absent rather than empty, so validation warns about the verse gaps and the totals.

To add one to the collection, see [adding a Bible](tool/docs/adding-bibles.md).

## Usage

```sh
tool/bin/bibles SOURCE [-o OUTPUT] [-n NAME] [-f {usfm,usx,osis,vpl,usj,rtf}]
                [--version-name NAME --abbreviation ABBREVIATION] [--allow-partial]
tool/bin/bibles --validate DATABASE [--allow-partial]
```

```sh
tool/bin/bibles kjv.usfm                      # writes bibles/kjv.sqlite
tool/bin/bibles eng-kjv_usfm.zip -n kjv       # a whole download, as it came
tool/bin/bibles kjv.usfm -o build/            # writes ./build/kjv.sqlite
tool/bin/bibles web.usfm --abbreviation WEB --version-name "World English Bible"   # sets the version
tool/bin/bibles --validate bibles/kjv.sqlite  # checks an existing database
```

The format is detected from the content, and the version's abbreviation and full name are worked out from the
source (its header, `metadata.xml`, `\id` lines or file name) unless `--abbreviation` and `--version-name` give
them. Every database is validated before it is written; if anything fails,
nothing is left at the output path. Books outside the 66 of the Protestant canon (Apocrypha, front matter) are
skipped with a warning, and `--allow-partial` accepts a Bible with fewer than 66 books, such as a New Testament.

All options, output paths, exit codes and examples for each format are in [command line usage](tool/docs/usage.md).

## Database schema

Each database is one SQLite file with four tables: `metadata`, `books`, `chapters` and `verses`, one plain text
row per verse. [Database schema](tool/docs/schema.md) has the full SQL, the metadata keys, the rules for verse
text and the reference values for all 66 books.

**Any SQLite database that follows that schema works in bible-tui**, wherever it came from. If you or a coding
agent build one yourselves, for a Bible this tool can't convert or for another book entirely, follow the schema
and check the result with `tool/bin/bibles --validate`.

## Copyright and licensing

Many Bible translations are **not** in the public domain. Modern translations such as the ESV, NIV, NASB, NKJV
and NLT are copyrighted by their publishers, and their licences generally forbid copying the text into other
formats or redistributing it without permission. The databases committed to this repository are only of
translations that are in the public domain or licensed for free redistribution, and each one's licence is
recorded above.

This tool converts whatever text you give it and cannot tell whether you have the right to do so. **It is your
responsibility** to check the copyright and licence of any text before you convert it, keep it, or share it.

**Disclaimer.** This software and the databases in this repository are provided "as is", without warranty of
any kind. The author accepts no responsibility or liability for how they are used. If you use this tool, or any
other means, to create SQLite databases of copyrighted Bibles or other books, you do so at your own risk and
take on sole responsibility for complying with the publisher's copyright and licence terms. The author is not
liable for any infringement, claim or damages arising from databases you or a coding agent create, keep or
distribute.

If you choose to take on that responsibility for a copy you are entitled to keep (for example, for personal
offline reading under the terms of a licence you hold), a database that follows the
[schema](tool/docs/schema.md) will work in bible-tui. Please do not open pull requests adding copyrighted
translations to this repository.

## Documentation

- [Quickstart](Quickstart.md): a step-by-step guide for converting your first Bible.
- [Command line usage](tool/docs/usage.md): every option, where the output goes, exit codes, examples per format.
- [Supported formats](tool/docs/formats.md): what is read from each format, format detection, verse text and
  known limitations.
- [Folders and zip archives](tool/docs/sources.md): how book files are found and combined, and the RTF layout.
- [Verse text normalization](tool/docs/normalization.md): headings, notes, poetry lines, whitespace, verse ranges
  and absent verses.
- [Database schema](tool/docs/schema.md): the SQLite format bible-tui reads.
- [Database validation](tool/docs/validation.md): every check, and which ones fail or only warn.
- [Adding a Bible](tool/docs/adding-bibles.md): adding a converted database to this collection.
- [Samples](tool/samples/README.md): where the sample files come from.
- [AGENTS.md](AGENTS.md): conventions and commands for contributors and coding agents.

## Development

Requires Python 3.9 or newer (developed on 3.12). No third-party packages.

```sh
python3 -m unittest discover -s tool/tests -t tool                               # run the test suite
python3 -m py_compile tool/bibles/*.py tool/bibles/parsers/*.py tool/tests/*.py  # syntax check
```

Some tests compare the output with a reference database that is not part of this repository; they are skipped
when it is not present.
