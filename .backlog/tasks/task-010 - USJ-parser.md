---
id: TASK-010
title: USJ parser
status: Ready for Testing
assignee:
  - '@cody'
created_date: '2026-10-22 14:09'
updated_date: '2026-10-22 14:47'
labels:
  - parsing
dependencies:
  - TASK-003
priority: high
type: feature
ordinal: 9
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
USJ is the JSON serialization of USFM. Instead of backslash markers, the same structure is expressed as JSON objects carrying a mark property, so a book identifier is an object whose mark is id, a chapter is an object whose mark is c, a verse is an object whose mark is v, and nested content such as paragraph and poetry styles appear as nested arrays.

The parser must produce the shared verse model and apply the shared normalization rules, and it must fail loudly on malformed JSON rather than writing a partial database.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The parser reads a USJ file and produces normalized books, chapters and verses through the shared model
- [x] #2 JSON markers are mapped to their USFM equivalents, including id for book, c for chapter, v for verse, and the paragraph, poetry and character styles
- [x] #3 Nested text content is flattened into the verse text with markup removed, and the resulting verse text is never empty
- [x] #4 A file containing several books is parsed in book order
- [x] #5 Malformed JSON produces a clear error naming the file and the parse failure, and no database is written
- [x] #6 Automated tests cover a USJ excerpt containing a book, a chapter, a verse and a nested paragraph marker
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
Added `bibles/parsers/usj.py`: walks the JSON tree and feeds the shared `MarkerEvents`, so USJ text is identical to USFM/USX.

- Node types book/chapter/verse/para/char/note/figure map to the USFM markers (the task says a 'mark' property; the USJ spec uses 'marker' -- both are accepted). id/c/v are also recognized by marker alone. sidebar, periph, ms, optbreak skipped.
- Malformed JSON -> ParseError naming the file, line and column; non-USJ JSON and no verses -> ParseError. Parsing happens fully before any write, so no database is written on failure.

Verification: `python3 -m py_compile bibles/*.py bibles/parsers/*.py tests/*.py` OK; `python3 -m unittest discover -s tests -t .` -> 110 tests OK (tests/test_parsers.py is new, incl. one passage in all five formats producing identical verses). Real-data smoke test (scratchpad, not committed): eBible.org World English Bible (engwebp) USFM, all 66 book files, parsed with 0 errors (31,098 verses, 5 warnings for verses WEB omits, e.g. ACT 8:37); the eBible VPL edition parsed to the same 31,098 references and wrote a 66-book / 1,189-chapter database through write_database. Text matched USFM except Psalm titles (\\d) and Song of Solomon speaker labels (\\sp), which eBible's VPL keeps and our policy drops, and one source-faithful spacing difference (PSA 68:32). eBible no longer serves USX/OSIS downloads at the usual URLs, so USX/OSIS/USJ are covered by fixtures only. Committed together in c0e1769 (shared core + cross-format test). DoD #7 N/A. No linter installed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added the USJ parser on the shared marker model.
<!-- SECTION:FINAL_SUMMARY:END -->
