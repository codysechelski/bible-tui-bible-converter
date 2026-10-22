---
id: TASK-009
title: VPL parser
status: Ready for Testing
assignee:
  - '@cody'
created_date: '2026-10-22 14:08'
updated_date: '2026-10-22 14:47'
labels:
  - parsing
dependencies:
  - TASK-003
priority: high
type: feature
ordinal: 8
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
VPL, verse per line, is the simplest of the supported formats. Each line holds one verse prefixed by its reference, in a form such as GEN 1:1 In the beginning, or GEN.1.1 In the beginning. eBible.org distributes this as a plain text download and the BibleNLP corpus uses the same shape aligned to a canonical verse list.

Two details matter for correctness. A blank line means the verse was not present in that translation rather than that it was empty, and a verse range is represented by putting the whole range text on the first verse and a range marker token on the following lines.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The parser reads a VPL file and produces normalized books, chapters and verses through the shared model
- [x] #2 References are parsed from a leading BOOK CHAPTER:VERSE token and from a leading BOOK.CHAPTER.VERSE token, and the book code resolves through the canonical book reference data
- [x] #3 A line that is not a verse reference is reported rather than silently dropped, so the run output makes the problem visible
- [x] #4 A blank line is treated as an absent verse and does not create an empty verse row
- [x] #5 A verse range is either expanded into its component verses or kept on the first verse, consistent with the policy written down in the normalization documentation
- [x] #6 Automated tests cover both reference forms, a blank line, a verse range and a line that is not a verse
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
Added `bibles/parsers/vpl.py` and `find_book` in books.py (USFM code, OSIS code, canonical/common name, or eBible alias SOL/EZE/JOE/MAR/JOH/PHI/JAM/1JO/2JO/3JO, found in the real eBible VPL).

- `BOOK C:V text` and `BOOK.C.V text`; ranges (`C:V-W`) are kept on the first verse; `<range>` lines and references with no text are absent verses; blank lines skipped.
- Design decision (please review): a line that is not a verse reference is skipped and recorded in `Bible.warnings` (to be printed by the pipeline, TASK-014) rather than failing the run. Unknown book codes and duplicate verses are ParseErrors with the line number.
- Detector (TASK-005) now also recognizes the dotted form.

Verification: `python3 -m py_compile bibles/*.py bibles/parsers/*.py tests/*.py` OK; `python3 -m unittest discover -s tests -t .` -> 110 tests OK (tests/test_parsers.py is new, incl. one passage in all five formats producing identical verses). Real-data smoke test (scratchpad, not committed): eBible.org World English Bible (engwebp) USFM, all 66 book files, parsed with 0 errors (31,098 verses, 5 warnings for verses WEB omits, e.g. ACT 8:37); the eBible VPL edition parsed to the same 31,098 references and wrote a 66-book / 1,189-chapter database through write_database. Text matched USFM except Psalm titles (\\d) and Song of Solomon speaker labels (\\sp), which eBible's VPL keeps and our policy drops, and one source-faithful spacing difference (PSA 68:32). eBible no longer serves USX/OSIS downloads at the usual URLs, so USX/OSIS/USJ are covered by fixtures only. Committed together in c0e1769 (shared core + cross-format test). DoD #7 N/A. No linter installed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added the VPL parser with range, blank-line and bad-line handling.
<!-- SECTION:FINAL_SUMMARY:END -->
