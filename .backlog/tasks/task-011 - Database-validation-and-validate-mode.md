---
id: TASK-011
title: Database validation and validate mode
status: Ready for Testing
assignee:
  - '@cody'
created_date: '2026-10-22 14:09'
updated_date: '2026-10-22 14:51'
labels:
  - validation
dependencies:
  - TASK-004
references:
  - /Users/codysechelski/Developer/Projects/bible-esv/tools/build_sqlite.py
priority: medium
type: feature
ordinal: 11
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A quietly wrong database is worse than a failed conversion, because the terminal UI would happily display corrupt or missing verses.

The reference project validates its database thoroughly before shipping it: an integrity check, a foreign key check, book and chapter and verse counts, contiguous numbering, duplicate reference detection and empty verse text detection. This task brings that level of rigour to every conversion, and adds a mode that validates a database that already exists without converting anything.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Validation runs automatically at the end of every conversion and reports any problem it finds
- [x] #2 Checks cover SQLite integrity, foreign keys, a book count of 66 with contiguous sort order and the correct testament split, contiguous chapter and verse numbering within each book, no duplicate book chapter verse references, and no empty verse text
- [x] #3 A translation that legitimately omits verses is reported as a warning rather than a failure, and the totals from the reference project are used as a sanity check only
- [x] #4 A validate mode accepts the path to an existing database, validates it without converting anything, and exits with a non zero status when validation fails
- [x] #5 Validation output lists every check that was performed together with its result
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
Added `bibles/validate.py` (`validate_database(path) -> ValidationReport`, `require_valid`, `DatabaseValidationError`) and `bibles --validate DB` (exit 0 pass/warn, 1 fail, 2 when combined with -o/-n/-f). Checks documented in docs/validation.md, linked from README.

- Validation runs inside `write_database` on the temporary file before `os.replace`, so a failing database never reaches the output path. `write_database` now returns `WriteResult(metadata, validation)`; the pipeline (TASK-014) should print `result.validation.lines()` and catch `DatabaseValidationError` (its `.report` has every check).
- 15 checks, all run and listed; a missing table stops early.

Design decisions (please review):
- Fail: integrity, FK, required metadata, book count != 66, book order/names/slugs differ from books.py, testament split, chapter gaps, chapters with no verses, duplicates, verse/chapter mismatch, empty text.
- Warn only: verse gaps (omitted verses, ranges), chapter count differing from the usual count (Hebrew versification: Joel 4, Malachi 3), totals differing from the ESV reference (1189/31104).
- A Bible missing books (e.g. NT-only) FAILS validation and therefore is not written. This follows AC #2 but blocks NT-only translations; relaxing it to a warning would need the writer to keep book ids = sort order (it already does).
- Missing verses at the end of a chapter cannot be detected (no per-chapter verse counts in the reference data), e.g. WEB's ROM 16:25-27.

Verification: `python3 -m py_compile bibles/*.py bibles/parsers/*.py tests/*.py` OK; `python3 -m unittest discover -s tests -t .` -> 134 tests OK (24 new). Manual: `./bin/bibles --validate bible-esv/bible_esv.sqlite` -> 15 PASS, exit 0; on the real WEB database built from eBible VPL -> pass with 2 warnings (4 omitted verses; totals 31098 vs 31104); on README.md -> FAIL, exit 1. DoD #7 N/A. No linter installed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added full database validation, run during every write and available as bibles --validate.
<!-- SECTION:FINAL_SUMMARY:END -->
