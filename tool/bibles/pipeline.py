"""The conversion pipeline: detect the format, parse and normalize, write the database, validate it."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from bibles.detect import Detection, FormatDetectionError, detect_format
from bibles.model import Bible
from bibles.parsers import PARSERS, ParseError, parse_file
from bibles.validate import DatabaseValidationError, ValidationReport
from bibles.writer import DatabaseWriteError, write_database

# Stage names used in error messages. Parsing includes text normalization.
DETECT, PARSE, WRITE, VALIDATE = "detect", "parse", "write", "validate"


class ConversionError(Exception):
    """A conversion failed. `stage` names the failing stage; `report` is set when validation failed."""

    def __init__(self, stage: str, message: str, report: Optional[ValidationReport] = None,
                 detection: Optional[Detection] = None) -> None:
        super().__init__(f"{stage} failed: {message}")
        self.stage = stage
        self.report = report
        self.detection = detection


@dataclass(frozen=True)
class ConversionResult:
    detection: Detection
    parser: str
    bible: Bible
    output: Path
    metadata: Dict[str, str]
    validation: ValidationReport


def parser_name(source_format: str) -> str:
    """The module that parses `source_format`, for example `bibles.parsers.usfm`."""
    return PARSERS[source_format].__module__


def convert(
    source: Path,
    output: Path,
    forced_format: Optional[str] = None,
    allow_partial: bool = False,
) -> ConversionResult:
    """Convert `source` to a database at `output`.

    Raises `ConversionError` naming the failing stage. Nothing is written to `output` unless every
    stage succeeds.
    """
    try:
        detection = detect_format(source, forced_format)
    except FormatDetectionError as error:
        raise ConversionError(DETECT, str(error)) from error

    try:
        bible = parse_file(source, detection.format)
    except ParseError as error:
        raise ConversionError(PARSE, str(error), detection=detection) from error

    try:
        result = write_database(bible, output, source, detection.format, allow_partial=allow_partial)
    except DatabaseValidationError as error:
        raise ConversionError(VALIDATE, str(error), error.report, detection) from error
    except (DatabaseWriteError, sqlite3.Error, OSError) as error:
        raise ConversionError(WRITE, str(error), detection=detection) from error

    assert result.validation is not None
    return ConversionResult(detection, parser_name(detection.format), bible, output, result.metadata,
                            result.validation)
