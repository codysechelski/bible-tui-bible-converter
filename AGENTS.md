# AGENTS.md

## Repo Purpose

`bibles` is a command line tool that converts a text-formatted Bible file (USFM, USX, OSIS, VPL, USJ) into a
SQLite database for the custom Bible terminal UI.

The reference project at `/Users/codysechelski/Developer/Projects/bible-esv` (read-only) defines the output
schema (`bible_esv.sqlite`), the validation rules (`tools/build_sqlite.py`) and the consuming TUI
(`tui/bible_tui.py`).

## Repository Map

- `bibles/` is the Python package. `bibles/cli.py` holds argument parsing and output path resolution;
  `bibles/__main__.py` makes `python3 -m bibles` work.
- `bibles/books.py` is the single source of truth for the 66 canonical books (USFM code, names, slug,
  testament, sort order, chapter count). Parsers resolve books with `book_for_code`, which raises
  `UnknownBookError` for any code outside the 66 (deuterocanonical books included).
- `bibles/model.py` holds the in-memory `Bible` every parser builds; parsers add verses with
  `Bible.add_verse`, which applies the shared text rules in `bibles/normalize.py`. Those rules are documented in
  `docs/normalization.md`; keep the doc and the marker sets in sync.
- `bibles/writer.py` writes a `Bible` to SQLite with `write_database`. `SCHEMA` is copied from the reference
  project and a test compares it with `bible_esv.sqlite`; never change it on its own. The database is built in a
  temporary file beside the output, validated, and moved into place only when complete and valid. Book ids
  equal sort order. Tests that write partial Bibles pass `validate=False`.
- `bibles/validate.py` runs every check and returns a `ValidationReport` (pass/warn/fail per check); verse gaps
  and unusual chapter counts only warn. `bibles --validate DB` prints it. Checks are listed in `docs/validation.md`.
- `bibles/detect.py` owns `SUPPORTED_FORMATS` and `detect_format`: content sniffing wins over the extension,
  format-specific extensions are a fallback, `--format` bypasses detection. The CLI turns
  `FormatDetectionError` into a `CliError`.
- `bibles/parsers/` has one module per format, registered in `PARSERS`; `parse_file(path, format)` returns a
  `Bible` or raises `ParseError`. USFM, USX and USJ translate their input into the events of
  `parsers/markers.py` (`MarkerEvents`), which applies the shared rules; OSIS and VPL feed `VerseCollector`
  (`parsers/base.py`) directly. Fix text handling in the shared layer, not in one front end, so the formats stay
  identical (`tests/test_parsers.py` checks one passage in all five formats).
- `docs/` holds Markdown documentation, linked from the README.
- `bin/bibles` is a bash wrapper that runs the package from any directory.
- `tests/` contains `unittest` tests.
- `.backlog/` holds Backlog.md tasks; work is planned there.

## Commands

- Run the CLI: `./bin/bibles SOURCE [-o OUTPUT] [-n NAME] [-f FORMAT]`
- Run tests: `python3 -m unittest discover -s tests -t .`
- Syntax check: `python3 -m py_compile bibles/*.py tests/*.py`

No linter or formatter is installed; `py_compile` plus the test suite is the static check. Automated
verification (`.agent/verification.json`) is intentionally disabled.

## Code Notes

- Python 3 standard library only, matching the reference project. Keep it compatible with Python 3.9+
  (`from __future__ import annotations`, `typing.Optional`).
- `main(argv)` returns an exit code instead of calling `sys.exit`, so tests can call it directly. User-facing
  failures raise `CliError` and exit 1; argparse usage errors and a bare invocation exit 2.
- `--output` resolution: existing directory, trailing separator, or no file extension means directory;
  otherwise it is a full file path. `--name` with a full file path is an error. `--name` without an extension
  gets `.sqlite` appended.
- The CLI currently resolves the output path and creates its parent directory, but does not write a database.
  The conversion pipeline (TASK-014) wires parsers to `write_database`, which already guarantees no partial or
  empty database is left behind on failure.
