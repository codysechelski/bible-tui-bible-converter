---
id: TASK-004
title: SQLite writer using the reference schema
status: Ready for Testing
assignee:
  - '@cody'
created_date: '2026-10-22 14:08'
updated_date: '2026-10-22 14:33'
labels:
  - schema
dependencies:
  - TASK-002
  - TASK-003
references:
  - /Users/codysechelski/Developer/Projects/bible-esv
  - /Users/codysechelski/Developer/Projects/bible-esv/tools/build_sqlite.py
  - /Users/codysechelski/Developer/Projects/bible-esv/bible_esv.sqlite
priority: high
type: feature
ordinal: 4
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The output database must use exactly the schema from the reference project so that the existing custom Bible terminal UI application can open it with no changes.

The reference schema has four tables. metadata holds a key and a value. books holds an id, a unique sort order, a unique canonical name, a common name, a unique slug, and a testament constrained to old or new. chapters holds an id, a cascading foreign key to books, and a chapter number, unique per book. verses holds an id, cascading foreign keys to books and chapters, a denormalized chapter number, a verse number, and the verse text, unique per book, chapter and verse. There are four indexes covering testament and sort order, book and chapter lookup, and two verse lookup paths.

This task owns the schema, the row writing, and the metadata population, and is deliberately independent of any particular source format.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The generated database contains the same four tables and four indexes as the reference schema, with matching names, columns, types, constraints and uniqueness rules
- [x] #2 Foreign key enforcement is enabled while writing and a foreign key check on the finished database reports no violations
- [x] #3 Book rows are written in canonical sort order using the canonical name, common name, slug and testament from the shared book reference data
- [x] #4 A chapter row exists for every chapter that contains verses, numbered from 1 with no gaps
- [x] #5 Verse rows carry the book id, chapter id, chapter number, verse number and text, and no duplicate book, chapter and verse combination exists
- [x] #6 The metadata table contains at least the keys version, version_name, source, created_at_utc, book_count, chapter_count and verse_count, all with non empty values
- [x] #7 Version and version_name are taken from the source file when the format supplies them and otherwise derive a sensible value from the input rather than being blank
- [x] #8 An automated test compares the generated schema against the reference project schema and fails on any difference in table or index names, columns, or constraints
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 When you are asked to work on a task, first move it to `In Progress` if it is not already there
- [x] #2 After you have ensured the task has the proper status, you must assign the work to yourself (@claude, @codex, @opencode, etc.)
- [x] #3 Completed the development work outlined in the task. Ask questions if things are unclear
- [x] #4 Before making changes, be sure that you understand the codebase. Look for existing patterns, components, tooling, etc., before forging your own path
- [x] #5 Before making sweeping architecture decisions, or making changes with a high likelihood of breaking other parts of the app, stop and ask first
- [x] #6 Unit tests are written for new code
- [x] #7 If creating a new reusable component with a UI, or adding a variant to an existing component, add an example in the design system (style-guide) page
- [x] #8 Choose a verification scope based on the files changed, risk, and user-visible behavior. Full test suites are required only for cross-cutting, infrastructure, auth/session, router/app-shell, editor-core, migration, build/dependency, or release-baseline work.
- [x] #9 Run the selected verification for real and record the commands/results. Acceptable scopes include no tests for docs/backlog/comment-only work, static checks, targeted unit/API/web tests, targeted browser/E2E checks, smoke/visual E2E, or full suites when warranted.
- [x] #10 If automated verification is configured, use the project's verification workflow with the smallest sufficient profile, or document why verification was intentionally skipped.
- [x] #11 Linting and formatting pass when code or style files changed
- [x] #12 If the task has multiple Acceptance Criteria, check them off as they are completed. Do not wait for the end to check them all because I will not be able to gauge your progress
- [x] #13 The README is up to date, with changes made if required
- [x] #14 AGENTS.md/CLAUDE.md is up to date, and any new memories with lasting value have been added
- [x] #15 If there is a need to document anything, create docs in the docs folder using Markdown files. Link those doc files into the README, where it makes sense
- [x] #16 All work is committed using Conventional Commits, authored as Cody (the project owner), never as the agent itself
- [x] #17 Commits are pushed to the remote repo
- [x] #18 The task is moved to "Ready for Testing"
- [x] #19 The task is assigned to Cody (the project owner) so he can review the changes.
<!-- DOD:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added `bibles/writer.py`: `SCHEMA` (verbatim from bible-esv tools/build_sqlite.py), `write_database(bible, output, source, source_format=None, created_at=None)` and `build_metadata`. `Bible` gained optional `version`/`version_name` for parsers to fill.

Design decisions (please review):
- Book id = sort_order (as in the reference db, so ids stay stable even when only some books are present). Chapter and verse ids are autoassigned in canonical order.
- Only books that contain verses are written; whether all 66 are required is left to validation (TASK-011).
- Chapters must run 1..n per book or `DatabaseWriteError` names the missing ones. An empty Bible is also an error.
- Metadata fallbacks: version = source file stem when the format gives none (e.g. `kjv`); version_name = version. source = "<file name> (<format>)". Counts are the real written counts. Only the seven required keys are written.
- Atomic write: temp file beside the output, os.replace on success, temp file removed on any failure, so an existing output is never clobbered by a failed run. An existing output is overwritten on success (CLI overwrite policy is TASK-014's call).

Verification: `python3 -m py_compile bibles/*.py tests/*.py` OK; `python3 -m unittest discover -s tests -t .` -> 59 tests OK (14 new). Mutation check: changing `common_name TEXT NOT NULL` to `TEXT` makes ReferenceSchemaTests fail. The schema test compares normalized sqlite_master SQL plus PRAGMA table_info/foreign_key_list/index_list/index_info against bible_esv.sqlite (skipped if absent). README unchanged (no user-visible behavior yet). DoD #7 N/A. No linter installed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added the SQLite writer that reproduces the reference schema, with atomic writes, metadata and a schema test against the reference database.
<!-- SECTION:FINAL_SUMMARY:END -->
