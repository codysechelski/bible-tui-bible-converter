---
id: TASK-005
title: Input format detection
status: In Progress
assignee:
  - '@claude'
created_date: '2026-10-22 14:08'
updated_date: '2026-10-22 14:36'
labels:
  - cli
  - parsing
dependencies:
  - TASK-001
priority: high
type: feature
ordinal: 10
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The user hands the tool one file path and expects the right parser to run without being told which format the file is in.

File extensions are only a hint. USFM books are distributed with a .usfm extension, USX and OSIS files are often .xml, VPL files are often .txt, and USJ files are often .json, so extension alone is not reliable. The content itself is a stronger signal: USX and OSIS are both XML but have distinct root elements, USJ is JSON, USFM is plain text containing backslash markers, and VPL is plain text whose lines begin with a book chapter verse reference.

This task builds the detection layer only. It returns which of the five supported formats a file appears to be, so that the conversion pipeline can pick the right parser. It also owns the flag that lets a user force a specific format when detection guesses wrong.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Detection identifies the format from the file extension and from content sniffing, and content wins when the extension is missing or misleading
- [x] #2 Content sniffing distinguishes USX from OSIS by their XML root elements, recognises USJ by JSON shape, recognises USFM by backslash markers, and recognises VPL by a leading book chapter verse reference
- [x] #3 An unsupported or undetectable file produces a clear error that names the supported formats and exits with a non zero status
- [x] #4 A flag is available to force a specific parser for a file that is detected incorrectly, and the forced format is reported in the run output
- [x] #5 Automated tests include at least one positive and one negative sample for each of the five formats
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
Added `bibles/detect.py` (`SUPPORTED_FORMATS`, `detect_format(path, forced=None) -> Detection(format, method)`, `sniff_content`, `FormatDetectionError`). The CLI now detects before creating the output directory and prints e.g. `Format: osis (detected from content)` or `Format: vpl (forced with --format)`.

Rules:
- Content first (first 64 KiB, BOM tolerated): XML root `usx` -> usx, `osis`/`osisText` (any namespace prefix) -> osis, other XML -> none; JSON object with type USJ -> usj (whole file parsed); a line starting with a common USFM marker (\\id, \\c, \\v, \\p, \\h, \\mt, \\toc, \\q, \\s, \\usfm, \\ide) -> usfm; first non-empty line plus at least half of the first 20 matching `Book C:V text` -> vpl.
- Fallback when content is inconclusive: .usfm/.sfm/.usx/.osis/.vpl/.usj. .xml/.json/.txt never decide on their own.
- Otherwise exit 1 with the supported formats listed and a hint to use --format. Unreadable files raise 'cannot read'.

Design decisions (please review):
- An unrecognisable file with a format-specific extension (e.g. junk in a .usfm) is accepted by extension and left for the parser to reject, rather than failing detection.
- Parser dispatch itself lives in TASK-014; this task only returns the format.

Verification: `python3 -m py_compile bibles/*.py tests/*.py` OK; `python3 -m unittest discover -s tests -t .` -> 73 tests OK (14 new: positive and negative samples for all five formats, misleading extensions, extension fallback, forced format, CLI reporting and exit codes). Manual: `./bin/bibles tests/test_detect.py -o ...` -> exit 1 with the supported-formats message. README updated with the detection rules. DoD #7 N/A. No linter installed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added content-first input format detection with extension fallback and --format override, reported in the CLI output.
<!-- SECTION:FINAL_SUMMARY:END -->
