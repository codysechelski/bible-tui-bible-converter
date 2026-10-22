# AGENTS.md

## Repo Purpose

`bibles` is a command line tool that converts a text-formatted Bible file (USFM, USX, OSIS, VPL, USJ) into a
SQLite database for the custom Bible terminal UI. The repository also collects the converted databases: the
tooling lives under `tool/`, and the converted `.sqlite` files live under `bibles/`.

The reference project at `/Users/codysechelski/Developer/Projects/bible-esv` (read-only) defines the output
schema (`bible_esv.sqlite`), the validation rules (`tools/build_sqlite.py`) and the consuming TUI
(`tui/bible_tui.py`). Schema parity is enforced by tests that read it (`tool/tests/test_writer.py`,
`tool/tests/test_samples.py`); they skip when the project is absent.

## Repository Map

The repository root has two directories, `tool/` (the converter) and `bibles/` (the converted databases,
`bible_<short name>.sqlite`), plus the README, AGENTS.md, CLAUDE.md, `.gitignore` and `.backlog/`. The README's
"Converted Bibles" section records each database's source, download checksum and licence; add a row there and to
`COLLECTION` in `tests/test_collection.py` whenever a database is added or reconverted. The paths below are
relative to `tool/`, so `bibles/` there is the Python package (`tool/bibles/`), not the database directory.

- `bibles/cli.py` holds argument parsing, output path resolution and the output of a run; `bibles/__main__.py`
  makes `python3 -m bibles` work from `tool/`. `bin/bibles` is a bash wrapper that runs the package from any
  directory.
- `bibles/pipeline.py` is the conversion: `convert()` runs detect, parse (which normalizes), write and validate,
  and raises `ConversionError` whose `stage` names the failing stage.
- `bibles/books.py` is the single source of truth for the 66 canonical books (USFM and OSIS codes, names, slug,
  testament, sort order, chapter count). `book_for_code` is strict USFM; `book_for_osis` and `find_book` (VPL)
  accept more spellings. Codes outside the 66 raise `UnknownBookError`; the parsers catch it and skip the book
  with a warning (`VerseCollector.skip_book`).
- `bibles/detect.py` owns `SUPPORTED_FORMATS` and `detect_format`: content sniffing wins over the extension,
  format-specific extensions are a fallback, `--format` bypasses detection.
- `bibles/parsers/` has one module per format, registered in `PARSERS`; `parse_file(path, format)` returns a
  `Bible` or raises `ParseError`. USFM, USX and USJ translate their input into the events of
  `parsers/markers.py` (`MarkerEvents`), which applies the shared rules; OSIS and VPL feed `VerseCollector`
  (`parsers/base.py`) directly. Fix text handling in the shared layer, not in one front end, so the formats stay
  identical.
- `bibles/model.py` holds the in-memory `Bible` (books, chapters, verses, version, warnings); verses are added
  with `Bible.add_verse`, which applies `bibles/normalize.py`. The rules are documented in
  `docs/normalization.md`; keep the doc and the marker sets in sync.
- `bibles/writer.py` writes a `Bible` with `write_database`. `SCHEMA` is copied from the reference project; never
  change it on its own. The database is built in a temporary file beside the output, validated, and moved into
  place only when complete and valid. Book ids equal sort order. Tests that write partial Bibles pass
  `validate=False` or `allow_partial=True`.
- `bibles/validate.py` runs every check and returns a `ValidationReport` (pass/warn/fail per check). Checks are
  listed in `docs/validation.md`.
- `samples/` holds real KJV excerpts (Ruth, Jonah, 3 John) in all five formats; `samples/README.md` records
  where each came from. Regenerate them the same way rather than hand-editing.
- `docs/` holds Markdown documentation, linked from the README.
- `tests/` contains `unittest` tests. `test_parsers.py` checks one passage in all five formats;
  `test_samples.py` converts the samples end to end through the CLI and the wrapper and reads the result with
  the reference TUI's `BibleStore`. `test_collection.py` validates the committed databases in `bibles/`.
- `.backlog/` (at the repository root) holds Backlog.md tasks; work is planned there.

## Commands

Run from the repository root:

- Convert: `tool/bin/bibles SOURCE [-o OUTPUT] [-n NAME] [-f FORMAT] [--allow-partial]`
- Validate an existing database: `tool/bin/bibles --validate DATABASE [--allow-partial]`
- Run tests: `python3 -m unittest discover -s tool/tests -t tool`
- Syntax check: `python3 -m py_compile tool/bibles/*.py tool/bibles/parsers/*.py tool/tests/*.py`

No linter or formatter is installed; `py_compile` plus the test suite is the static check. Automated
verification (`.agent/verification.json`) is intentionally disabled.

## Code Notes

- Python 3 standard library only, matching the reference project. Keep it compatible with Python 3.9+
  (`from __future__ import annotations`, `typing.Optional`).
- `main(argv)` returns an exit code instead of calling `sys.exit`, so tests can call it directly. User-facing
  failures raise `CliError` or `ConversionError` and exit 1; argparse usage errors and a bare invocation exit 2.
- `--output` resolution: without `--output` the database goes to `COLLECTION_DIR` (`bibles/` at the repository
  root, found from the package's location, not the working directory); a relative `--output` is taken from the
  working directory. An existing directory, trailing separator, or no file extension means directory;
  otherwise it is a full file path. `--name` with a full file path is an error. `--name` without an extension
  gets `.sqlite` appended.
- A failed run must leave nothing behind: no database at the output path, no temporary file, and no directory
  the run created.
- Validation is strict by default (66 books). `--allow-partial` only relaxes the book count, order and
  testament totals; every other check is unchanged.
