---
id: TASK-012
title: End to end tests and sample files for all five formats
status: Ready for Testing
assignee:
  - '@cody'
created_date: '2026-10-22 14:09'
updated_date: '2026-10-22 15:10'
labels:
  - testing
dependencies:
  - TASK-006
  - TASK-007
  - TASK-008
  - TASK-009
  - TASK-010
  - TASK-014
priority: medium
type: task
ordinal: 13
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The point of supporting five formats is that the same Bible produces the same database whichever format it arrives in. That has to be proven by tests rather than assumed.

The tests need real sample files, one per format, for the same translation so the results can be compared. Small permissively licensed excerpts are enough; the point is exercising every parser against real markup rather than a synthetic minimal case.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The repository contains a small sample file for each of the five supported formats, covering the same translation
- [x] #2 Each sample converts to a database whose schema matches the reference schema and whose books, chapters and verses match the expected content of that sample
- [x] #3 Converting the same Bible expressed in two different formats yields identical verse text for the references they share
- [x] #4 The command line path is exercised end to end, covering the default output file name, an explicit output file name, an explicit output directory, and a failure case such as a missing input file or an unsupported format, each with the expected exit status
- [x] #5 A generated database can be opened and read by the queries the reference terminal UI uses, joining books, chapters and verses, without error
- [x] #6 The command that runs the test suite is documented in the repository
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
Added `samples/` with Ruth, Jonah and 3 John (3 books, 9 chapters, 147 verses) of the KJV in all five formats, all real eBible.org material: USFM = eBible's three book files unchanged; USX/USJ = usfm-grammar 3.2.1 conversions of those files (independent converter, used only to generate the samples, not a dependency); OSIS = eBible's eng-kjv OSIS (via the open-bibles mirror) with other books removed; VPL = eBible's lines unchanged. Provenance, licence (public domain) and expected differences in samples/README.md.

`tests/test_samples.py` (18 tests): every sample converts through the CLI with its format detected; schema equals the reference db; books, per-chapter verse counts and spot texts match; USFM, USX and USJ produce identical text for all 147 verses; OSIS and VPL share every reference; footnotes do not leak; strict validation fails and --allow-partial passes; the reference TUI's own BibleStore (imported from bible-esv/tui/bible_tui.py) and copies of its queries read the database; the bin/bibles wrapper covers default name, -n, -o dir, -o file, missing input (1), unsupported --format (2), undetectable input (1) and strict validation failure (1), each leaving nothing behind.

Note (please review): the samples are 3 whole books, so converting them needs --allow-partial (added in TASK-014). AC #3 identical-text comparison is USFM vs USX vs USJ; eBible's OSIS and VPL are separate exports whose text differs by edition/brackets, so they are compared on references only. Test command documented in README and AGENTS.md.

Verification: `python3 -m py_compile bibles/*.py bibles/parsers/*.py tests/*.py` OK; `python3 -m unittest discover -s tests -t .` -> 160 tests OK; all files parse with the Python 3.9 grammar (only 3.12 is installed, so 3.9 was not run). DoD #7 N/A. No linter installed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added real KJV samples in all five formats and end-to-end tests through the CLI, wrapper and reference TUI.
<!-- SECTION:FINAL_SUMMARY:END -->
