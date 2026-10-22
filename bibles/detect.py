"""Work out which supported format a source file is in.

The content is sniffed first and wins over the file extension. The extension is used only when the
content gives no answer and the extension is specific to one format (`.xml`, `.json` and `.txt` are
not).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

SUPPORTED_FORMATS = ("usfm", "usx", "osis", "vpl", "usj")

EXTENSION_FORMATS = {
    ".usfm": "usfm",
    ".sfm": "usfm",
    ".usx": "usx",
    ".osis": "osis",
    ".vpl": "vpl",
    ".usj": "usj",
}

# How much of the file the text and XML sniffers look at.
SNIFF_BYTES = 64 * 1024

_XML_ROOT = re.compile(r"<([A-Za-z_][\w.-]*:)?([A-Za-z_][\w.-]*)")
_XML_PROLOG = re.compile(r"\s*(<\?.*?\?>|<!--.*?-->|<!DOCTYPE[^>]*>)", re.DOTALL | re.IGNORECASE)
_USFM_MARKER = re.compile(
    r"^[ \t]*\\(?:id|usfm|ide|h|toc\d|mt\d?|c|v|p|q\d?|s\d?)(?:\s|$)", re.MULTILINE
)
# "Gen 1:1 ...", "GEN 1:1 ...", "GEN.1.1 ...", "1 John 3:16 ...", "Song of Solomon 2:1 ...".
_VPL_LINE = re.compile(
    r"^\s*(?:[1-3]\s?)?[A-Za-z][A-Za-z]*(?: [A-Za-z][A-Za-z]*)*(?:\s+\d+:\d+|\.\d+\.\d+)\s+\S"
)
_VPL_SAMPLE_LINES = 20


class FormatDetectionError(Exception):
    """The source format could not be determined."""


@dataclass(frozen=True)
class Detection:
    format: str
    method: str  # "content", "extension" or "forced"

    def describe(self) -> str:
        how = {"content": "detected from content", "extension": "detected from file extension",
               "forced": "forced with --format"}[self.method]
        return f"{self.format} ({how})"


def _sniff_xml(text: str) -> Optional[str]:
    position = 0
    while True:
        prolog = _XML_PROLOG.match(text, position)
        if not prolog:
            break
        position = prolog.end()
    root = _XML_ROOT.match(text[position:].lstrip())
    if not root:
        return None
    name = root.group(2).lower()
    if name == "usx":
        return "usx"
    if name in ("osis", "osistext"):
        return "osis"
    return None


def _sniff_json(path: Path) -> Optional[str]:
    try:
        with path.open(encoding="utf-8-sig") as file:
            data = json.load(file)
    except (ValueError, UnicodeDecodeError):
        return None
    if isinstance(data, dict) and str(data.get("type", "")).upper() == "USJ":
        return "usj"
    return None


def _sniff_text(text: str) -> Optional[str]:
    if _USFM_MARKER.search(text):
        return "usfm"
    lines = [line for line in text.splitlines() if line.strip()][:_VPL_SAMPLE_LINES]
    if lines and _VPL_LINE.match(lines[0]):
        matching = sum(1 for line in lines if _VPL_LINE.match(line))
        if matching * 2 >= len(lines):
            return "vpl"
    return None


def sniff_content(path: Path) -> Optional[str]:
    """Return the format the file's content looks like, or None."""
    with path.open("rb") as file:
        head = file.read(SNIFF_BYTES)
    text = head.decode("utf-8-sig", errors="replace")
    start = text.lstrip()[:1]
    if start == "<":
        return _sniff_xml(text)
    if start in ("{", "["):
        return _sniff_json(path)
    return _sniff_text(text)


def detect_format(path: Path, forced: Optional[str] = None) -> Detection:
    """Return the source's format, raising `FormatDetectionError` when it cannot be determined."""
    if forced is not None:
        if forced not in SUPPORTED_FORMATS:
            raise FormatDetectionError(
                f"unsupported format {forced!r}; supported formats: {', '.join(SUPPORTED_FORMATS)}"
            )
        return Detection(forced, "forced")

    try:
        content_format = sniff_content(path)
    except OSError as error:
        raise FormatDetectionError(f"cannot read {path}: {error.strerror or error}") from error
    if content_format is not None:
        return Detection(content_format, "content")

    extension_format = EXTENSION_FORMATS.get(path.suffix.lower())
    if extension_format is not None:
        return Detection(extension_format, "extension")

    raise FormatDetectionError(
        f"could not detect the format of {path}; supported formats: "
        f"{', '.join(SUPPORTED_FORMATS)} (use --format to choose one)"
    )
