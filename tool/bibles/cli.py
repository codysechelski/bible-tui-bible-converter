"""Command line entry point for the bibles converter."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from bibles import __version__
from bibles.detect import SUPPORTED_FORMATS, Detection
from bibles.identity import Version, VersionError, check_given
from bibles.pipeline import ConversionError, ConversionResult, convert, parser_name
from bibles.sources import BookFiles
from bibles.validate import ValidationReport, validate_database

OUTPUT_SUFFIX = ".sqlite"
# Where a conversion goes when no --output is given: the repository's bibles/ directory, beside tool/.
COLLECTION_DIR = Path(__file__).resolve().parents[2] / "bibles"
# How many parser warnings a run prints before summarizing the rest.
MAX_WARNINGS = 20


class CliError(Exception):
    """A user-facing error that should end the run with a non zero status."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bibles",
        description=(
            "Convert a text-formatted Bible into a SQLite database. The source is a file, a folder "
            "of book files, or a zip archive of one."
        ),
    )
    parser.add_argument(
        "source",
        type=Path,
        help=(
            "the source Bible: a file, a folder of book files (searched with its subfolders), or a "
            "zip archive of one (with --validate: the database to check)"
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        help=(
            "output directory or full output file path; a path ending in a separator, an existing "
            "directory, or a path without a file extension is treated as a directory "
            "(default: the bibles/ directory at the repository root)"
        ),
    )
    parser.add_argument(
        "-n",
        "--name",
        help=(
            f"output file name, used inside the output directory; {OUTPUT_SUFFIX} is appended when "
            f"the name has no extension (default: source base name + {OUTPUT_SUFFIX})"
        ),
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=SUPPORTED_FORMATS,
        help=(
            "force a specific input format instead of detecting it; for a folder or zip archive, "
            "only the files in this format are used"
        ),
    )
    parser.add_argument(
        "--version-name",
        metavar="NAME",
        help=(
            "the version's full name, stored as version_name (for example \"World English Bible\"); "
            "requires --abbreviation (default: worked out from the source)"
        ),
    )
    parser.add_argument(
        "--abbreviation",
        help=(
            "the version's abbreviation, stored as version (for example WEB); requires --version-name "
            "(default: worked out from the source)"
        ),
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="accept a Bible with fewer than 66 books (missing books are reported as a warning)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="validate an existing database instead of converting; exits 1 when a check fails",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def default_file_name(source: Path) -> str:
    # A folder's whole name is its base name; a file loses its extension.
    return (source.name if source.is_dir() else source.stem) + OUTPUT_SUFFIX


def normalize_file_name(name: str) -> str:
    if not name or name in (".", "..") or "/" in name or (os.sep != "/" and os.sep in name):
        raise CliError(f"--name must be a plain file name, not a path: {name!r}")
    if not Path(name).suffix:
        name += OUTPUT_SUFFIX
    return name


def output_is_directory(raw_output: str, path: Path) -> bool:
    # Path() drops a trailing separator, so check the text the user typed.
    if raw_output.endswith(("/", os.sep)):
        return True
    if path.is_dir():
        return True
    if path.exists():
        return False
    return not path.suffix


def resolve_output_path(
    source: Path,
    output: Optional[str] = None,
    name: Optional[str] = None,
    cwd: Optional[Path] = None,
) -> Path:
    """Work out the database path from the source path and the optional output flags.

    Without --output the database goes into `COLLECTION_DIR`; a relative --output is taken from `cwd`.
    """
    base_dir = cwd if cwd is not None else Path.cwd()
    file_name = normalize_file_name(name) if name is not None else default_file_name(source)

    if output is None:
        return COLLECTION_DIR / file_name

    raw_output = os.fspath(output)
    output_path = Path(raw_output).expanduser()
    if not output_path.is_absolute():
        output_path = base_dir / output_path
    if output_is_directory(raw_output, output_path):
        return output_path / file_name
    if name is not None:
        raise CliError("--name cannot be combined with an --output that is a full file path")
    return output_path


def _missing_parents(path: Path) -> List[Path]:
    """The ancestors of `path` that do not exist yet, nearest first."""
    missing = []
    for parent in path.parents:
        if parent.exists():
            break
        missing.append(parent)
    return missing


def run(args: argparse.Namespace) -> ConversionResult:
    source: Path = args.source
    if not source.is_file() and not source.is_dir():
        raise CliError(f"source not found: {source}")

    output_path = resolve_output_path(source, args.output, args.name)
    if output_path.is_dir():
        raise CliError(f"output path is a directory: {output_path}")
    if output_path.exists() and output_path.resolve() == source.resolve():
        raise CliError(f"output path is the source file: {output_path}")

    created = _missing_parents(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        return convert(source, output_path, args.format, args.allow_partial, args.abbreviation,
                       args.version_name)
    except BaseException:
        # Leave no trace of a failed run: remove directories this run created, if still empty.
        for directory in created:
            try:
                directory.rmdir()
            except OSError:
                break
        raise


def print_report(report: ValidationReport) -> None:
    print(f"Validating: {report.path}")
    for line in report.lines():
        print(line)


def print_detection(detection: Detection, files: Optional[BookFiles] = None) -> None:
    if files is not None:
        print(f"Input: {files.describe()}")
    print(f"Format: {detection.describe()}")
    print(f"Parser: {parser_name(detection.format)}")


def print_version(version: Version) -> None:
    print(f"Version: {version.abbreviation} ({version.abbreviation_origin})")
    print(f"Version name: {version.name} ({version.name_origin})")


def print_warnings(warnings: Sequence[str]) -> None:
    for warning in warnings[:MAX_WARNINGS]:
        print(f"Warning: {warning}")
    if len(warnings) > MAX_WARNINGS:
        print(f"Warning: ... and {len(warnings) - MAX_WARNINGS} more warnings")


def validate_command(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    if any(value is not None for value in (args.output, args.name, args.format, args.version_name,
                                           args.abbreviation)):
        parser.error("--validate cannot be combined with --output, --name, --format, --version-name "
                     "or --abbreviation")
    report = validate_database(args.source, args.allow_partial)
    print_report(report)
    return 0 if report.ok else 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        parser.print_usage(sys.stderr)
        print(f"{parser.prog}: error: a source file is required (see --help)", file=sys.stderr)
        return 2

    args = parser.parse_args(argv)
    if args.validate:
        return validate_command(parser, args)
    try:
        check_given(args.abbreviation, args.version_name)
    except VersionError as error:
        parser.error(str(error))

    print(f"Source: {args.source}")
    try:
        result = run(args)
    except ConversionError as error:
        if error.detection is not None:
            print_detection(error.detection, error.files)
        if error.report is not None:
            print_report(error.report)
        print(f"{parser.prog}: error: {error}", file=sys.stderr)
        print(f"{parser.prog}: no database was written", file=sys.stderr)
        return 1
    except CliError as error:
        print(f"{parser.prog}: error: {error}", file=sys.stderr)
        return 1

    metadata = result.metadata
    print_detection(result.detection, result.files)
    print_version(result.version)
    print_warnings(result.bible.warnings)
    print_report(result.validation)
    print(f"Output: {result.output}")
    print(
        f"Wrote {metadata['book_count']} books, {metadata['chapter_count']} chapters and "
        f"{metadata['verse_count']} verses (version {metadata['version']})"
    )
    return 0
