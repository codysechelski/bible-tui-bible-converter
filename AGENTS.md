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
  The conversion pipeline (TASK-014) must not leave a partial or empty database behind on failure.
