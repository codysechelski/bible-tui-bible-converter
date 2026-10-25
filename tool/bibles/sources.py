"""Sources that hold more than one file: a folder of book files, or a zip archive of one.

Bible downloads are usually a zip holding one file per book beside metadata, stylesheets, licences and
other files (a Digital Bible Library bundle, an eBible.org zip). `open_source` extracts a zip to a
temporary folder for the length of a run, and `find_book_files` picks out the files in a supported
format, searching subfolders. A Digital Bible Library `metadata.xml` supplies the version, the language
and the book names.
"""

from __future__ import annotations

import os
import posixpath
import tempfile
import xml.etree.ElementTree as ET
import zipfile
import zlib
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

from bibles.books import UnknownBookError, book_for_code
from bibles.detect import (
    EXTENSION_FORMATS,
    SUPPORTED_FORMATS,
    Detection,
    FormatDetectionError,
    sniff_content,
)

FILE, FOLDER, ARCHIVE = "file", "folder", "zip archive"
METADATA_FILE = "metadata.xml"
# A damaged, truncated, encrypted (RuntimeError) or unusually compressed archive, or a full disk.
_EXTRACT_ERRORS = (zipfile.BadZipFile, zlib.error, EOFError, RuntimeError, NotImplementedError, OSError)
# How many folder names `BookFiles.describe` lists before summarizing.
_MAX_FOLDERS = 3


class SourceError(Exception):
    """The source cannot be opened, for example a damaged or encrypted zip archive."""


@dataclass(frozen=True)
class OpenedSource:
    """`root` is the file itself, the folder, or the temporary folder a zip was extracted to."""

    kind: str
    root: Path


@dataclass(frozen=True)
class SourceFile:
    path: Path  # on disk
    name: str  # relative to the source root, with `/` separators
    format: str
    method: str  # "content", "extension" or "forced", as in `Detection`


@dataclass(frozen=True)
class BookFiles:
    """The Bible files found in a folder or zip archive, and what the bundle says about itself."""

    kind: str
    files: Tuple[SourceFile, ...]
    ignored: Tuple[str, ...]
    detection: Detection
    version: Optional[str] = None
    version_name: Optional[str] = None
    language: Optional[str] = None
    # The bundle's short book names, by USFM book code.
    book_names: Dict[str, str] = field(default_factory=dict)

    def describe(self) -> str:
        folders = sorted({posixpath.dirname(f.name) or "." for f in self.files})
        where = ", ".join(folders[:_MAX_FOLDERS])
        if len(folders) > _MAX_FOLDERS:
            where += f" and {len(folders) - _MAX_FOLDERS} more folders"
        text = f"{self.kind}, {_count(len(self.files), self.detection.format + ' file')} in {where}"
        if self.ignored:
            text += f"; {_count(len(self.ignored), 'other file')} ignored"
        return text


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}{'' if number == 1 else 's'}"


@contextmanager
def open_source(path: Path) -> Iterator[OpenedSource]:
    """Open a source file, folder or zip archive. An extracted archive is removed afterwards."""
    if path.is_dir():
        yield OpenedSource(FOLDER, path)
        return
    if not zipfile.is_zipfile(path):
        yield OpenedSource(FILE, path)
        return
    with tempfile.TemporaryDirectory(prefix="bibles-") as folder:
        try:
            with zipfile.ZipFile(path) as archive:
                # extractall keeps every member inside `folder` (absolute paths and `..` are dropped).
                archive.extractall(folder)
        except _EXTRACT_ERRORS as error:
            raise SourceError(f"cannot extract the zip archive {path}: {error}") from error
        yield OpenedSource(ARCHIVE, Path(folder))


def _walk(root: Path) -> Iterator[Tuple[Path, str]]:
    """Every file below `root` in sorted order, skipping hidden files and macOS archive metadata."""
    for directory, folders, files in os.walk(root):
        folders[:] = sorted(f for f in folders if not f.startswith(".") and f != "__MACOSX")
        for file_name in sorted(files):
            if file_name.startswith("."):
                continue
            path = Path(directory) / file_name
            yield path, path.relative_to(root).as_posix()


def _file_format(path: Path, name: str) -> Tuple[Optional[str], str]:
    try:
        content_format = sniff_content(path)
    except OSError as error:
        raise FormatDetectionError(f"cannot read {name}: {error.strerror or error}") from error
    if content_format is not None:
        return content_format, "content"
    return EXTENSION_FORMATS.get(path.suffix.lower()), "extension"


def read_dbl_metadata(path: Path) -> Tuple[Optional[str], Optional[str]]:
    """The abbreviation and name in a Digital Bible Library `metadata.xml`, or Nones."""
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None, None
    if root.tag != "DBLMetadata":
        return None, None

    def value(tag: str) -> Optional[str]:
        text = root.findtext(f"identification/{tag}")
        return text.strip() if text and text.strip() else None

    return value("abbreviation") or value("abbreviationLocal"), value("name") or value("nameLocal")


def read_dbl_books(path: Path) -> Tuple[Optional[str], Dict[str, str]]:
    """The language code (`language/iso`) and the short book names (`names/name/short`, by USFM book
    code) in a Digital Bible Library `metadata.xml`."""
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None, {}
    if root.tag != "DBLMetadata":
        return None, {}
    language = (root.findtext("language/iso") or "").strip() or None
    names: Dict[str, str] = {}
    for name in root.findall("names/name"):
        identifier = name.get("id") or ""
        short = " ".join((name.findtext("short") or name.findtext("long") or "").split())
        if not identifier.startswith("book-") or not short:
            continue
        try:
            names[book_for_code(identifier[len("book-"):].upper()).usfm_code] = short
        except UnknownBookError:
            continue
    return language, names


def find_book_files(source: Path, opened: OpenedSource, forced: Optional[str] = None) -> BookFiles:
    """Find the Bible files in an opened folder or archive.

    Files whose format cannot be detected are ignored. Without `forced` the files must all be in one
    format; with it, only files in that format are used. Raises `FormatDetectionError` when no Bible
    file is found or the formats are mixed.
    """
    if forced is not None and forced not in SUPPORTED_FORMATS:
        raise FormatDetectionError(
            f"unsupported format {forced!r}; supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )
    found: Dict[str, List[SourceFile]] = {}
    ignored: List[str] = []
    metadata: List[Path] = []
    for path, name in _walk(opened.root):
        source_format, method = _file_format(path, name)
        if source_format is None or (forced is not None and source_format != forced):
            ignored.append(name)
            if path.name.lower() == METADATA_FILE:
                metadata.append(path)
            continue
        found.setdefault(source_format, []).append(
            SourceFile(path, name, source_format, "forced" if forced else method)
        )

    if not found:
        wanted = (f"{forced} files" if forced
                  else f"Bible files (supported formats: {', '.join(SUPPORTED_FORMATS)})")
        raise FormatDetectionError(
            f"no {wanted} found in the {opened.kind} {source} ({_count(len(ignored), 'file')} looked at)"
        )
    if len(found) > 1:
        formats = ", ".join(f"{fmt} ({len(files)})" for fmt, files in sorted(found.items()))
        raise FormatDetectionError(
            f"the {opened.kind} {source} holds Bible files in more than one format: {formats}; "
            "use --format to choose one"
        )

    (source_format, files), = found.items()
    if forced:
        method = "forced"
    else:
        method = "content" if all(f.method == "content" for f in files) else "extension"
    version, version_name, language, book_names = None, None, None, {}
    # The bundle's own metadata.xml sits at its top; one deeper down may belong to something else.
    for path in sorted(metadata, key=lambda p: len(p.parts)):
        version, version_name = read_dbl_metadata(path)
        if version or version_name:
            language, book_names = read_dbl_books(path)
            break
    return BookFiles(opened.kind, tuple(files), tuple(ignored), Detection(source_format, method),
                     version, version_name, language, book_names)
