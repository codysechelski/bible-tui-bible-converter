---
id: TASK-014
title: Conversion pipeline and parser dispatch
status: In Progress
assignee:
  - '@claude'
created_date: '2026-10-22 14:12'
updated_date: '2026-10-22 15:10'
labels:
  - cli
  - core
dependencies:
  - TASK-001
  - TASK-003
  - TASK-004
  - TASK-005
  - TASK-006
  - TASK-007
  - TASK-008
  - TASK-009
  - TASK-010
  - TASK-011
references:
  - /Users/codysechelski/Developer/Projects/bible-esv
priority: high
type: feature
ordinal: 12
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
This task is the integration point. It wires the pieces built by the other tasks into one working command: detect the format, run the matching parser, normalize the result, write the SQLite database, then validate it.

Today each of those pieces exists on its own and the tool still cannot convert a real file end to end. This task closes that gap and is the first point at which a user can run the CLI against a real Bible and open the resulting database in the terminal UI.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The CLI runs the full path of detect, parse, normalize, write and validate for a given input file and reports which format was detected and which parser ran
- [x] #2 Each of the five supported formats is routed to its parser, and the forced format flag routes to the requested parser instead
- [x] #3 A conversion that fails at any stage exits with a non zero status and a message that names the failing stage, and no partial or empty database is left behind
- [x] #4 A successful conversion writes the database to the resolved output path and prints the output path along with a summary of the books, chapters and verses written
- [x] #5 The pipeline reports validation results produced by the validation step rather than duplicating those checks
- [x] #6 Automated tests cover the full pipeline for at least one format and cover the failure path for an unreadable or unsupported input
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
Added `bibles/pipeline.py` (`convert(source, output, forced_format, allow_partial) -> ConversionResult`; `ConversionError.stage` is detect, parse, write or validate; parse includes normalization). The CLI prints Source, Format (detected/forced), Parser (module), parser warnings (first 20), the full validation report, Output, and 'Wrote N books, N chapters and N verses (version X)'. Failure: exit 1, 'bibles: error: <stage> failed: ...', 'no database was written'; directories the run created are removed again; an existing output is replaced only on success; output == source is rejected.

Design decisions (please review):
- Books outside the 66 (Apocrypha, FRT, GLO, ...) are now SKIPPED with a named warning ('skipped book TOB: not one of the 66 canonical books') in all five parsers instead of failing the parse. Without this, every real eBible download (KJV OSIS and USFM include the Apocrypha) was unconvertible. The warning keeps it from being silent (TASK-002 AC #6).
- New flag `--allow-partial` (convert and --validate): fewer than 66 books becomes a warning; book names/slugs/testaments and all other checks still apply. Needed for NT-only Bibles and for the TASK-012 samples. Strict remains the default.
- VPL now recognises 4-prefixed codes (4ES) so they are skipped as books rather than reported as bad lines.

Real-data run (scratchpad, not committed): full eBible KJV in all five formats (USFM = all 81 eBible book files concatenated; USX and USJ generated by usfm-grammar 3.2.1; eBible's OSIS; eBible's VPL) -> each exit 0, 66 books / 1189 chapters / 31102 verses, Apocrypha skipped with warnings, 1-3 s each. USFM, USX and USJ text identical for all 31,102 verses. OSIS differs only by source edition (e.g. Bethel vs Beth-el, no pilcrows); VPL only by its [added word] brackets and Psalm titles.

Verification: `python3 -m py_compile bibles/*.py bibles/parsers/*.py tests/*.py` OK; `python3 -m unittest discover -s tests -t .` -> 160 tests OK; all files parse with the Python 3.9 grammar (only 3.12 is installed, so 3.9 was not run). DoD #7 N/A. No linter installed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Wired detect, parse, write and validate into one CLI conversion with stage-named failures, book skipping and --allow-partial.
<!-- SECTION:FINAL_SUMMARY:END -->
