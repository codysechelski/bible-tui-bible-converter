# Database validation

A quietly wrong database is worse than a failed conversion, so every database is validated. The rules live
in `bibles/validate.py` and follow the reference project's `tools/build_sqlite.py`.

- **During a conversion** `write_database` validates the database in its temporary file before moving it
  into place. If any check fails, nothing is written to the output path.
- **Validate mode** checks an existing database without converting anything:

  ```sh
  ./bin/bibles --validate path/to/bible.sqlite
  ```

  It exits 0 when every check passes or only warns, and 1 when any check fails. `--output`, `--name` and
  `--format` cannot be combined with `--validate`.

Every check runs and is listed with its result, for example:

```
Validating: web.sqlite
  PASS  Schema tables: metadata, books, chapters, verses
  PASS  SQLite integrity: ok
  ...
  WARN  Verse numbering: missing Luke 17:36, missing Acts 8:37, missing Acts 15:34, missing Acts 24:7
  ...
Validation passed: 15 checks, 0 failed, 2 warnings
```

## Checks

| Check | Fails when | Warns when |
| --- | --- | --- |
| Schema tables | `metadata`, `books`, `chapters` or `verses` is missing (later checks are skipped) | |
| SQLite integrity | `PRAGMA integrity_check` is not `ok` | |
| Foreign keys | `PRAGMA foreign_key_check` reports a violation | |
| Metadata | a required key (`version`, `version_name`, `source`, `created_at_utc`, `book_count`, `chapter_count`, `verse_count`) is missing or blank | |
| Book count | there are not exactly 66 books | |
| Book order and names | sort order is not 1..66, or a book's canonical name, common name or slug differs from `bibles/books.py` | |
| Testament split | the split is not 39 old / 27 new, or a book has the wrong testament | |
| Chapter numbering | a book's chapters do not run from 1 with no gaps | |
| Chapters with verses | a chapter row has no verses | |
| Chapter counts | | a book's chapter count differs from the usual count (versification traditions differ) |
| Verse numbering | | a chapter's verses have gaps or do not start at 1 |
| Duplicate references | a book, chapter and verse appears twice | |
| Verse chapter links | a verse's book or chapter number disagrees with its chapter row | |
| Empty verse text | a verse's text is empty or only whitespace | |
| Totals against reference | | the totals differ from the reference ESV database (1189 chapters, 31104 verses) |

Verse gaps are warnings because translations legitimately omit verses (for example Acts 8:37) and verse
ranges are stored on their first verse (see [normalization](normalization.md)). A verse missing from the end
of a chapter cannot be detected, because the reference data does not record verses per chapter.
