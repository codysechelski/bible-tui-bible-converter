# Command line usage

```sh
tool/bin/bibles SOURCE [-o OUTPUT] [-n NAME] [-f {usfm,usx,osis,vpl,usj,rtf}] [--allow-partial]
tool/bin/bibles --validate DATABASE [--allow-partial]
```

The commands are shown run from the repository root. The wrapper works from any directory, and
`python3 -m bibles` works from inside `tool/`.

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

## Options

| Option | Meaning |
| --- | --- |
| `SOURCE` | The source Bible (required): a file, a folder of book files (subfolders included), or a zip archive of one. With `--validate`, the database to check. |
| `-o, --output` | Output directory or full output file path, relative to the current directory. Defaults to `bibles/` at the repository root, wherever the command is run from. |
| `-n, --name` | Output file name inside the output directory. Defaults to the source base name (a file's or zip's name without its extension, a folder's name) with `.sqlite`; `.sqlite` is appended when the name has no extension. |
| `-f, --format` | Force a format instead of detecting it: `usfm`, `usx`, `osis`, `vpl`, `usj` or `rtf`. For a folder or zip, only the files in that format are used. |
| `--allow-partial` | Accept a Bible with fewer than 66 books (a New Testament, or a sample). Missing books become a warning. |
| `--validate` | Validate an existing database instead of converting. Cannot be combined with `-o`, `-n` or `-f`. |
| `--version`, `-h` | Print the version or the help. |

## Where the database is written

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

## Exit status

0 on success (warnings allowed), 1 when the conversion or validation fails, 2 for a usage error or no
arguments. A failure names its stage (`detect`, `parse`, `write` or `validate`), and no database is left at the
output path.

## Examples for each format

The [`tool/samples/`](../samples/README.md) directory has the same three KJV books in every format, and the
same books of the ASV as RTF files in a folder. They hold 3 books rather than 66, hence `--allow-partial`; a
whole Bible needs no flag.

```sh
tool/bin/bibles tool/samples/kjv.usfm     --allow-partial -o build/kjv-usfm.sqlite   # USFM
tool/bin/bibles tool/samples/kjv.usx      --allow-partial -o build/kjv-usx.sqlite    # USX
tool/bin/bibles tool/samples/kjv.osis.xml --allow-partial -o build/kjv-osis.sqlite   # OSIS
tool/bin/bibles tool/samples/kjv.vpl.txt  --allow-partial -o build/kjv-vpl.sqlite    # VPL
tool/bin/bibles tool/samples/kjv.usj      --allow-partial -o build/kjv-usj.sqlite    # USJ
tool/bin/bibles tool/samples/asv-rtf/     --allow-partial -o build/asv-rtf.sqlite    # RTF, a folder of books
```

Folders and zip archives, including what the run prints for them, are covered in
[folders and zip archives](sources.md).
