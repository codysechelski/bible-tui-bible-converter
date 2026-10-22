# Backlog Manager Cache — bibles

Last updated: 2026-10-22

## Project

`bibles` is a CLI tool that converts a text-formatted Bible file into a SQLite database
for a custom Bible terminal UI application. Supported source formats: USX, USFM, OSIS, VPL, USJ.

The repository serves two purposes: it ships the conversion tooling, and it is meant to hold a
collection of the converted SQLite databases (see TASK-015 / TASK-016).

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

## Task index (as of 2026-10-22)

| ID | Title | Status | Area |
| --- | --- | --- | --- |
| TASK-001 | Scaffold project and CLI entry point | completed | cli |
| TASK-002 | Canonical 66-book reference data | completed | core |
| TASK-003 | Shared verse model and text normalization rules | completed | core |
| TASK-004 | SQLite writer using the reference schema | completed | schema |
| TASK-005 | Input format detection and parser dispatch | completed | cli, parsing |
| TASK-006 | USFM parser | Ready for Testing | parsing |
| TASK-007 | USX parser | Ready for Testing | parsing |
| TASK-008 | OSIS parser | Ready for Testing | parsing |
| TASK-009 | VPL parser | Ready for Testing | parsing |
| TASK-010 | USJ parser | Ready for Testing | parsing |
| TASK-011 | Database validation and validate mode | Ready for Testing | validation |
| TASK-012 | End to end tests and sample files for all five formats | In Progress | testing |
| TASK-013 | README and project documentation | In Progress | cli |
| TASK-014 | Conversion pipeline and parser dispatch | In Progress | cli, core |
| TASK-015 | Move tooling into a dedicated folder so the repo root holds converted databases | To Do | repo-layout |
| TASK-016 | Collect converted SQLite Bible databases in the repository | To Do | repo-layout |

Build order: 001 -> 002 -> 003 -> 004 -> 006..010 -> 005 -> 011 -> 014 -> 012 -> 013.
TASK-016 depends on TASK-015 and TASK-014.

## Notes

- Labels configured in `.backlog/config.yml`: `cli`, `core`, `parsing`, `schema`, `validation`, `testing`, `repo-layout`.
- `auto_commit: true` in the canonical config, so Backlog.md self-commits each task edit with its own
  wording ("Create task TASK-0NN"), not Conventional Commits. Config changes and cache updates are not
  self-committed and need an explicit commit.
- The working tree often carries in-flight application code changes from implementation agents
  (e.g. `bibles/pipeline.py` for TASK-014). Stage only `.backlog/**` for backlog commits.
- Startup acknowledgement flag `.backlog/.backlog-manager-acknowledged` already exists.
- Verification commands (paths change when TASK-015 lands):
  `python3 -m unittest discover -s tests -t .` and `python3 -m py_compile bibles/*.py tests/*.py`.
