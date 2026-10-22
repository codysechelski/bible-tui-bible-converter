---
id: TASK-013
title: README and project documentation
status: Ready for Testing
assignee:
  - '@cody'
created_date: '2026-10-22 14:09'
updated_date: '2026-10-22 15:10'
labels:
  - cli
dependencies:
  - TASK-001
  - TASK-012
references:
  - /Users/codysechelski/Developer/Projects/bible-esv
priority: medium
type: docs
ordinal: 14
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The tool is only useful if the user knows what to type and what the resulting database contains. This task writes the documentation that makes the tool usable without reading the source.

The README is the main deliverable. An agent facing file such as AGENTS.md should also exist so that later contributors and coding agents know the conventions, the commands, and where the reference schema lives.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The README documents how to run the tool and shows a complete example invocation for each of the five supported formats
- [x] #2 The README documents the output schema, listing the tables, their columns, their relationships, and the metadata keys
- [x] #3 The README documents the supported formats, explains how format detection works, and explains how to force a specific format
- [x] #4 The README documents the verse text normalization policy and lists the known limitations of each format
- [x] #5 An AGENTS.md file records the repository conventions, the commands for running the tests and the validation, and the location of the reference project used for schema parity
- [x] #6 Any supporting documentation files are linked from the README
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
Rewrote README.md: quick start with sample output, usage and options (incl. --allow-partial, --validate), output path rules, exit statuses, an example for each format using samples/, the eBible concatenation recipe, a supported-formats table, detection and --format, known limitations per format, the verse text rules, the full output schema (tables, columns, constraints, relationships, indexes, metadata keys), validation, and links to docs/normalization.md, docs/validation.md, samples/README.md and AGENTS.md. Rewrote AGENTS.md (repo map incl. pipeline and samples, commands for tests/validation/syntax check, reference project location and how parity is tested, conventions). Brought docs/normalization.md and docs/validation.md in line with book skipping and --allow-partial.

Every README example was run for real: the five sample commands (exit 0, database written), the four output-naming examples and --validate on a full KJV built with the cat recipe (66/1189/31102, validation passed).

Verification: `python3 -m py_compile bibles/*.py bibles/parsers/*.py tests/*.py` OK; `python3 -m unittest discover -s tests -t .` -> 160 tests OK; all files parse with the Python 3.9 grammar (only 3.12 is installed, so 3.9 was not run). DoD #7 N/A. No linter installed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Documented usage, formats, detection, schema, normalization, limitations and validation in the README and AGENTS.md.
<!-- SECTION:FINAL_SUMMARY:END -->
