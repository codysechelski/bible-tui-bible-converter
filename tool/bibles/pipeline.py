"""The conversion pipeline: detect the format, parse and normalize, write the database, validate it."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from bibles.detect import Detection, FormatDetectionError, detect_format
from bibles.model import Bible
from bibles.parsers import PARSERS, ParseError, parse_file, parse_files
from bibles.sources import FILE, BookFiles, OpenedSource, SourceError, find_book_files, open_source
from bibles.validate import DatabaseValidationError, ValidationReport
from bibles.writer import DatabaseWriteError, write_database

# Stage names used in error messages. Parsing includes text normalization.
DETECT, PARSE, WRITE, VALIDATE = "detect", "parse", "write", "validate"


class ConversionError(Exception):
    """A conversion failed. `stage` names the failing stage; `report` is set when validation failed.

    `files` is set when the source is a folder or zip archive and its Bible files were found.
    """

    def __init__(self, stage: str, message: str, report: Optional[ValidationReport] = None,
                 detection: Optional[Detection] = None, files: Optional[BookFiles] = None) -> None:
        super().__init__(f"{stage} failed: {message}")
        self.stage = stage
        self.report = report
        self.detection = detection
        self.files = files


@dataclass(frozen=True)
class ConversionResult:
    detection: Detection
    parser: str
    bible: Bible
    output: Path
    metadata: Dict[str, str]
    validation: ValidationReport
    files: Optional[BookFiles] = None


def parser_name(source_format: str) -> str:
    """The module that parses `source_format`, for example `bibles.parsers.usfm`."""
    return PARSERS[source_format].__module__


def convert(
    source: Path,
    output: Path,
    forced_format: Optional[str] = None,
    allow_partial: bool = False,
) -> ConversionResult:
    """Convert `source` (a file, a folder of book files, or a zip archive of one) to a database at
    `output`.

    Raises `ConversionError` naming the failing stage. Nothing is written to `output` unless every
    stage succeeds, and a zip archive's extracted files are removed either way.
    """
    try:
        with open_source(source) as opened:
            return _convert(source, opened, output, forced_format, allow_partial)
    except SourceError as error:
        raise ConversionError(DETECT, str(error)) from error


def _convert(source: Path, opened: OpenedSource, output: Path, forced_format: Optional[str],
             allow_partial: bool) -> ConversionResult:
    files: Optional[BookFiles] = None
    try:
        if opened.kind == FILE:
            detection = detect_format(source, forced_format)
        else:
            files = find_book_files(source, opened, forced_format)
            detection = files.detection
    except FormatDetectionError as error:
        raise ConversionError(DETECT, str(error)) from error

    try:
        if files is None:
            bible = parse_file(source, detection.format)
        else:
            bible = parse_files([(f.path, f.name) for f in files.files], detection.format)
            bible.version = bible.version or files.version
            bible.version_name = bible.version_name or files.version_name
    except ParseError as error:
        raise ConversionError(PARSE, str(error), detection=detection, files=files) from error

    try:
        result = write_database(bible, output, source, detection.format, allow_partial=allow_partial)
    except DatabaseValidationError as error:
        raise ConversionError(VALIDATE, str(error), error.report, detection, files) from error
    except (DatabaseWriteError, sqlite3.Error, OSError) as error:
        raise ConversionError(WRITE, str(error), detection=detection, files=files) from error

    assert result.validation is not None
    return ConversionResult(detection, parser_name(detection.format), bible, output, result.metadata,
                            result.validation, files)
