"""Command line entry point for the bibles converter."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Sequence, Tuple

from bibles import __version__
from bibles.detect import SUPPORTED_FORMATS, Detection, FormatDetectionError, detect_format
from bibles.validate import ValidationReport, validate_database

OUTPUT_SUFFIX = ".sqlite"


class CliError(Exception):
    """A user-facing error that should end the run with a non zero status."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bibles",
        description="Convert a text-formatted Bible file into a SQLite database for the Bible TUI.",
    )
    parser.add_argument(
        "source", type=Path, help="path to the source Bible file (with --validate: the database to check)"
    )
    parser.add_argument(
        "-o",
        "--output",
        help=(
            "output directory or full output file path; a path ending in a separator, an existing "
            "directory, or a path without a file extension is treated as a directory "
            "(default: current working directory)"
        ),
    )
    parser.add_argument(
        "-n",
        "--name",
        help=(
            f"output file name, used inside the output directory; {OUTPUT_SUFFIX} is appended when "
            f"the name has no extension (default: source file base name + {OUTPUT_SUFFIX})"
        ),
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=SUPPORTED_FORMATS,
        help="force a specific input format instead of detecting it",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="validate an existing database instead of converting; exits 1 when a check fails",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def default_file_name(source: Path) -> str:
    return source.stem + OUTPUT_SUFFIX


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
    """Work out the database path from the source path and the optional output flags."""
    base_dir = cwd if cwd is not None else Path.cwd()
    file_name = normalize_file_name(name) if name is not None else default_file_name(source)

    if output is None:
        return base_dir / file_name

    raw_output = os.fspath(output)
    output_path = Path(raw_output).expanduser()
    if not output_path.is_absolute():
        output_path = base_dir / output_path
    if output_is_directory(raw_output, output_path):
        return output_path / file_name
    if name is not None:
        raise CliError("--name cannot be combined with an --output that is a full file path")
    return output_path


def run(args: argparse.Namespace) -> Tuple[Detection, Path]:
    source: Path = args.source
    if not source.is_file():
        raise CliError(f"source file not found: {source}")

    output_path = resolve_output_path(source, args.output, args.name)
    if output_path.is_dir():
        raise CliError(f"output path is a directory: {output_path}")
    try:
        detection = detect_format(source, args.format)
    except FormatDetectionError as error:
        raise CliError(str(error)) from error
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return detection, output_path


def print_report(report: ValidationReport) -> None:
    print(f"Validating: {report.path}")
    for line in report.lines():
        print(line)


def validate_command(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    if args.output is not None or args.name is not None or args.format is not None:
        parser.error("--validate cannot be combined with --output, --name or --format")
    report = validate_database(args.source)
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
        detection, output_path = run(args)
    except CliError as error:
        print(f"{parser.prog}: error: {error}", file=sys.stderr)
        return 1

    print(f"Source: {args.source}")
    print(f"Format: {detection.describe()}")
    print(f"Output: {output_path}")
    print("Conversion is not implemented yet; no database was written.")
    return 0
