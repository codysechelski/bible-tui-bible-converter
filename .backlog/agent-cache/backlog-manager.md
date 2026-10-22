# Backlog Manager Cache — bibles

Last updated: 2026-10-22

## Project

`bibles` is a new CLI tool that converts a text-formatted Bible file into a SQLite database
for a custom Bible terminal UI application. Supported source formats: USX, USFM, OSIS, VPL, USJ.

Reference project (schema + conventions, read-only): `/Users/codysechelski/Developer/Projects/bible-esv`
- `bible_esv.sqlite` — the reference database, schema is the contract.
- `tools/build_sqlite.py` — reference builder/validator, source of the validation rules.
- `tui/bible_tui.py` — the consuming terminal UI; it queries `books`, `chapters`, `verses`, `metadata`.

## Output schema (contract)

- `metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)`
- `books(id, sort_order UNIQUE, canonical_name UNIQUE, common_name, slug UNIQUE, testament CHECK old|new)`
- `chapters(id, book_id FK cascade, chapter_number, UNIQUE(book_id, chapter_number))`
- `verses(id, book_id FK cascade, chapter_id FK cascade, chapter_number, verse_number, text, UNIQUE(book_id, chapter_number, verse_number))`
- Indexes: `idx_books_testament_order`, `idx_chapters_book_number`, `idx_verses_book_chapter_verse`, `idx_verses_chapter_number`
- Conventions: 66 books, sort_order 1..66, old 1..39 / new 40..66; common_name converts Roman to Arabic
  (`I Samuel` -> `1 Samuel`); `Revelation of John` -> `Revelation`; slug = lowercase dashed common name
  (`1-samuel`, `song-of-solomon`).

## Task index (all To Do as of 2026-10-22)

| ID | Title | Area |
| --- | --- | --- |
| TASK-001 | Scaffold project and CLI entry point | cli |
| TASK-002 | Canonical 66-book reference data | core |
| TASK-003 | Shared verse model and text normalization rules | core |
| TASK-004 | SQLite writer using the reference schema | schema |
| TASK-005 | Input format detection | cli, parsing |
| TASK-006 | USFM parser | parsing |
| TASK-007 | USX parser | parsing |
| TASK-008 | OSIS parser | parsing |
| TASK-009 | VPL parser | parsing |
| TASK-010 | USJ parser | parsing |
| TASK-011 | Database validation and validate mode | validation |
| TASK-014 | Conversion pipeline and parser dispatch | cli, core |
| TASK-012 | End to end tests and sample files for all five formats | testing |
| TASK-013 | README and project documentation | cli |

Build order: 001 -> 002 -> 003 -> 004 -> 006..010 -> 005 -> 011 -> 014 -> 012 -> 013.

## Notes

- Labels configured in `.backlog/config.yml`: `cli`, `core`, `parsing`, `schema`, `validation`, `testing`.
- `auto_commit: true` in the canonical config, so Backlog.md self-commits each task edit.
  Task-edit commits use Backlog.md wording, not Conventional Commits.
- Startup acknowledgement flag `.backlog/.backlog-manager-acknowledged` already exists.
- No application code exists in this repo yet; only backlog files are tracked.
