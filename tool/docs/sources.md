# Folders and zip archives

Most Bible downloads are a zip archive with one file per book, next to metadata, stylesheets, licences and other
files: a Digital Bible Library (DBL) bundle, or an eBible.org zip. The converter takes the zip itself, or the
folder you get by unzipping it, and converts every book file in it as one Bible. `bibles/sources.py` finds the
files, and `parse_files` in `bibles/parsers/__init__.py` combines them.

```sh
tool/bin/bibles "Biblia Livre Para Todos.zip" --allow-partial -n bible_blt   # a zip archive
tool/bin/bibles eng-kjv_usfm/ -n bible_kjv                                   # the folder it unzips to
```

A DBL bundle looks like this. Only the files under `release/USX_1/` hold Bible text:

```
metadata.xml                 the bundle's description: name, abbreviation, language, rights holder
license.xml
release/styles.xml
release/por_pt-BR.ldml
release/versification.vrs
release/USX_1/MAT.usx        one file per book
release/USX_1/MRK.usx
...
```

## Finding the book files

- A source is a zip archive when its content is one, whatever its extension. A zip is unpacked into a temporary
  folder for the length of the run, and that folder is removed afterwards, whether or not the run succeeds.
  Paths inside the archive cannot reach outside that folder.
- The folder and all of its subfolders are searched in sorted order. Hidden files and folders (names starting
  with `.`, such as `.DS_Store`) and macOS `__MACOSX` folders are skipped.
- The format of each file is detected the same way as for a single source: by its content, or by a
  format-specific extension when the content is not recognisable (see "Format detection" in the README).
  Files that are not in a supported format, such as `metadata.xml`, `styles.xml`, `.ldml`, `.vrs`, `.htm` and
  signature files, are ignored and counted in the run's `Input:` line.
- All the Bible files must be in one format. If a folder holds, say, both USFM and USX files, the run fails and
  lists the formats it found with how many files each. Use `--format` to pick one; only the files in that format
  are used then.
- If no Bible file is found, the run fails in the `detect` stage.

The run reports what it found:

```
Source: Biblia Livre Para Todos.zip
Input: zip archive, 27 usx files in release/USX_1; 5 other files ignored
Format: usx (detected from content)
```

## Combining the books

- Each file is parsed on its own, and its books are added in file order. The database orders books canonically
  in any case.
- A file may hold more than one book.
- A file with no canonical book (an Apocrypha book, front matter or a glossary) is fine. Its books are skipped
  with the usual warning, such as `skipped book TOB: not one of the 66 canonical books`.
- Some bundles carry the same books twice. The KJV bundle has `release/USX_1/` with the Apocrypha and
  `release/USX_2/` without it. When a book turns up again with identical verses, the later copy is skipped
  and one warning sums up all the copies:
  `66 books in release/USX_2 repeat release/USX_1 with identical text and were skipped (1CH, 1CO, ...)`.
  When the copies differ, the run fails in the `parse` stage and names both files.
- Error messages name a file by its path inside the folder or archive, for example
  `release/USX_1/JON.usfm, line 3: ...`.

## Version and name

When the bundle has a DBL `metadata.xml` (the shallowest one is used), its `identification/abbreviation`
becomes the database's `version` and `identification/name` its `version_name`. A version that the parsed
text supplies itself (an OSIS header) takes precedence, and `--abbreviation` with `--version-name` overrides
both. Without any of them, the `\id` lines and the zip's or folder's name are tried, as described in
[version and abbreviation](usage.md#version-and-abbreviation).

The default output file name is the zip's name without `.zip`, or the folder's name, plus `.sqlite`. Download
names are often long (`King James Version [eng] without Strong's numbers, 1769 standardized text.zip`), so give
`-n` for anything you keep.

## RTF book files

Some bundles ship formatted text instead of USFM or USX. The ASV bundle has `release/USX_1/RUT.rtf` and so on,
despite the folder's name. `bibles/parsers/rtf.py` reads RTF in that layout, one book per file:

- **Book.** It comes from the file name when that is a USFM code (`RUT.rtf`). Otherwise it comes from the first
  heading, the book title (`Ruth`).
- **Chapters.** A heading paragraph (paragraph style `\s1` or higher) that is the title followed by a number
  (`Ruth 1`) starts that chapter. Any other heading, such as `BOOK I` in the Psalms, is dropped. A one-chapter
  book with no chapter heading is chapter 1.
- **Verses.** A bold run holding only a number (`{\b 16}`) starts that verse. Each paragraph is one line of the
  verse, so poetry is joined as in the other formats.
- **Dropped.**
  - Textual notes: a paragraph that starts with a bold `chapter:verse` reference, such as
    `{\b 7:16 }Many ancient authorities insert ...`.
  - The Psalm 119 acrostic letters: a paragraph holding only a Hebrew letter and its name, such as `ב BETH.`.
  - Psalm titles: any text before the first verse of a chapter.
  - Document tables (fonts, styles, document info), pictures, footnotes, field codes and other `{\*...}`
    destinations.
- **Omitted verses.** A verse whose only text is `*` marks a verse the translation leaves out. It is left out with
  a warning, like any empty verse.
- **Characters.** `\uN` characters (with their fallback skipped), `\'hh` bytes in the document's code page
  (`\ansicpgN`, Windows-1252 by default) and the common character control words (`\~`, `\emdash`, `\rquote` and
  so on) are decoded.

RTF is rendered text, so the parser relies on the layout above. RTF from other producers converts only if it
marks chapters and verses the same way. A line of text after the last verse of a chapter stays in that verse:
the ASV's subscription to Habakkuk 3 (`For the Chief Musician, on my stringed instruments.`) ends up in 3:19.
