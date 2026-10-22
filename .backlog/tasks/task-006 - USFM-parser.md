---
id: TASK-006
title: USFM parser
status: In Progress
assignee:
  - '@claude'
created_date: '2026-10-22 14:08'
updated_date: '2026-10-22 14:47'
labels:
  - parsing
dependencies:
  - TASK-003
priority: high
type: feature
ordinal: 5
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
USFM, the Unified Standard Format Markers, is plain text that uses backslash markers. A book file starts with an id marker such as \id GEN, chapters are introduced by a c marker and verses by a v marker, and a verse continues across following lines until the next marker. eBible.org and Paratext distribute USFM as one file per book, and a single file may also contain several books in sequence.

The parser must produce the shared verse model, resolve the book from its id marker, and apply the shared normalization rules so that the output is identical to the same Bible converted from another format.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The parser reads a USFM file and produces normalized books, chapters and verses through the shared model
- [x] #2 Book identity comes from the id marker and resolves to the canonical book record, and a file containing more than one book is split into separate books in order
- [x] #3 Chapters come from the c marker and verses from the v marker, and verse text continues across following lines until the next verse, chapter or book marker
- [x] #4 Paragraph, poetry and character formatting markers do not leak into verse text
- [x] #5 Non verse content such as title markers, section headings, table of contents entries and reminder markers is excluded from verse text
- [x] #6 Footnotes, endnotes and cross references are removed or inlined consistently with the documented normalization policy
- [x] #7 UTF-8 files are read correctly, and files carrying a byte order mark or a legacy encoding are handled without a crash
- [x] #8 Automated tests cover a single book excerpt and a file containing multiple books
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 When you are asked to work on a task, first move it to `In Progress` if it is not already there
- [ ] #2 After you have ensured the task has the proper status, you must assign the work to yourself (@claude, @codex, @opencode, etc.)
- [ ] #3 Completed the development work outlined in the task. Ask questions if things are unclear
- [ ] #4 Before making changes, be sure that you understand the codebase. Look for existing patterns, components, tooling, etc., before forging your own path
- [ ] #5 Before making sweeping architecture decisions, or making changes with a high likelihood of breaking other parts of the app, stop and ask first
- [ ] #6 Unit tests are written for new code
- [ ] #7 If creating a new reusable component with a UI, or adding a variant to an existing component, add an example in the design system (style-guide) page
- [ ] #8 Choose a verification scope based on the files changed, risk, and user-visible behavior. Full test suites are required only for cross-cutting, infrastructure, auth/session, router/app-shell, editor-core, migration, build/dependency, or release-baseline work.
- [ ] #9 Run the selected verification for real and record the commands/results. Acceptable scopes include no tests for docs/backlog/comment-only work, static checks, targeted unit/API/web tests, targeted browser/E2E checks, smoke/visual E2E, or full suites when warranted.
- [ ] #10 If automated verification is configured, use the project's verification workflow with the smallest sufficient profile, or document why verification was intentionally skipped.
- [ ] #11 Linting and formatting pass when code or style files changed
- [ ] #12 If the task has multiple Acceptance Criteria, check them off as they are completed. Do not wait for the end to check them all because I will not be able to gauge your progress
- [ ] #13 The README is up to date, with changes made if required
- [ ] #14 AGENTS.md/CLAUDE.md is up to date, and any new memories with lasting value have been added
- [ ] #15 If there is a need to document anything, create docs in the docs folder using Markdown files. Link those doc files into the README, where it makes sense
- [ ] #16 All work is committed using Conventional Commits, authored as Cody (the project owner), never as the agent itself
- [ ] #17 Commits are pushed to the remote repo
- [ ] #18 The task is moved to "Ready for Testing"
- [ ] #19 The task is assigned to Cody (the project owner) so he can review the changes.
<!-- DOD:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added `bibles/parsers/usfm.py` (tokenizer) on top of the shared core: `parsers/base.py` (`ParseError`, `VerseCollector`, `read_text`, `parse_number`) and `parsers/markers.py` (`MarkerEvents`, shared with USX/USJ). `parsers/__init__.py` registers all five parsers in `PARSERS` and exposes `parse_file(path, format)`.

- \\id starts a book (rest of the line ignored); several \\id in one file give several books in order.
- Paragraph/poetry markers start a new fragment; character markers keep their text; \\w attributes after | are dropped; milestones (\\qt-s ... \\*) and sidebars (\\esb..\\esbe) are skipped; note-internal markers (\\fp etc.) are treated as character-level so a note never leaks.
- Encoding: UTF-8 with or without BOM; otherwise cp1252 then latin-1, with a warning.
- Errors raise ParseError with file and line.

Design decisions (please review):
- A verse with no text (e.g. only a footnote, as for omitted verses like ACT 8:37) is left out with a warning instead of failing the run.
- Verse ranges (\\v 1-2) are kept on the first verse; segments (3a/3b) are joined.
- \\qa (Psalm 119 acrostic letters) added to the dropped headings.
- Unknown book codes (FRT, GLO, deuterocanon) still fail the parse, per TASK-002. eBible USFM zips include 00-FRT*.usfm etc., so converting a whole folder will need the pipeline (TASK-014) to skip those files.
- Psalm titles (\\d) are still dropped (TASK-003 decision). Note: both the ESV reference db and eBible's VPL keep them in verse 1; flipping is a one-line change in NON_VERSE_BLOCK_MARKERS.

Verification: `python3 -m py_compile bibles/*.py bibles/parsers/*.py tests/*.py` OK; `python3 -m unittest discover -s tests -t .` -> 110 tests OK (tests/test_parsers.py is new, incl. one passage in all five formats producing identical verses). Real-data smoke test (scratchpad, not committed): eBible.org World English Bible (engwebp) USFM, all 66 book files, parsed with 0 errors (31,098 verses, 5 warnings for verses WEB omits, e.g. ACT 8:37); the eBible VPL edition parsed to the same 31,098 references and wrote a 66-book / 1,189-chapter database through write_database. Text matched USFM except Psalm titles (\\d) and Song of Solomon speaker labels (\\sp), which eBible's VPL keeps and our policy drops, and one source-faithful spacing difference (PSA 68:32). eBible no longer serves USX/OSIS downloads at the usual URLs, so USX/OSIS/USJ are covered by fixtures only. Committed together in c0e1769 (shared core + cross-format test). DoD #7 N/A. No linter installed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added the USFM parser and the shared parser core used by every format.
<!-- SECTION:FINAL_SUMMARY:END -->
