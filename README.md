# bibles

> **Status:** early scaffold. The command line surface is in place, but no input format is parsed yet and
> no database is written. Full documentation is tracked in TASK-013.

`bibles` converts a text-formatted Bible (USFM, USX, OSIS, VPL or USJ) into a SQLite database that the
custom Bible terminal UI can read. It is Python 3 and standard library only, so it runs anywhere the TUI does.

## Usage

```sh
./bin/bibles SOURCE [-o OUTPUT] [-n NAME] [-f {usfm,usx,osis,vpl,usj}]
# or, from the repository root
python3 -m bibles SOURCE ...
```

| Option | Meaning |
| --- | --- |
| `SOURCE` | Path to the source Bible file (required). |
| `-o, --output` | Output directory or full output file path. Defaults to the current working directory. |
| `-n, --name` | Output file name inside the output directory. Defaults to the source base name with `.sqlite`. `.sqlite` is appended when the name has no extension. |
| `-f, --format` | Force a specific input format instead of detecting it (`usfm`, `usx`, `osis`, `vpl`, `usj`). |
| `--validate` | Validate an existing database (`SOURCE`) instead of converting. |

How `--output` is interpreted:

- An existing directory, a path ending in `/`, or a path without a file extension is a **directory**; the
  file name is placed inside it. Missing directories are created.
- Anything else (for example `build/kjv.db`) is a **full file path** and is used directly. `--name` cannot be
  combined with a full file path.

How the input format is detected:

- The file content is checked first and always wins over the extension: an XML root of `<usx>` is USX and
  `<osis>` is OSIS, a JSON object with `"type": "USJ"` is USJ, a line starting with a USFM marker such as `\id`,
  `\c` or `\v` is USFM, and lines starting with a reference such as `Gen 1:1` are VPL.
- If the content is inconclusive, a format-specific extension (`.usfm`, `.sfm`, `.usx`, `.osis`, `.vpl`, `.usj`)
  is used. `.xml`, `.json` and `.txt` say nothing on their own.
- Otherwise the run fails with exit status 1 and lists the supported formats. Use `--format` to override
  detection; the output shows whether the format was detected or forced.

Examples:

```sh
./bin/bibles kjv.usfm                      # ./kjv.sqlite
./bin/bibles kjv.usfm -n king-james        # ./king-james.sqlite
./bin/bibles kjv.usfm -o build/            # ./build/kjv.sqlite
./bin/bibles kjv.usfm -o build/bible.db    # ./build/bible.db
```

Running with no arguments prints usage and exits with status 2; a successful run exits with status 0.

## Validating a database

```sh
./bin/bibles --validate bible.sqlite
```

Runs every check (integrity, foreign keys, 66 books in canonical order, contiguous chapters, duplicate and
empty verses, and more), lists each result, and exits 1 if any check fails. Conversions run the same checks
before writing. See [validation](docs/validation.md).

## Documentation

- [Verse text normalization](docs/normalization.md): how headings, notes, poetry lines and whitespace are
  handled so every input format produces the same verse text.
- [Database validation](docs/validation.md): every check, and which ones fail or only warn.

## Development

Requires Python 3.9 or newer (developed on 3.12). No third-party packages.

```sh
python3 -m unittest discover -s tests -t .   # run the test suite
python3 -m py_compile bibles/*.py tests/*.py # syntax check
```
