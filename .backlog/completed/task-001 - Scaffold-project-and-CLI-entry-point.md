---
id: TASK-001
title: Scaffold project and CLI entry point
status: Done
assignee:
  - '@cody'
created_date: '2026-10-22 14:08'
updated_date: '2026-10-22 14:40'
labels:
  - cli
dependencies: []
references:
  - /Users/codysechelski/Developer/Projects/bible-esv
priority: high
type: chore
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The bibles project is a new, empty repository whose goal is a command line tool that converts a text formatted Bible into a SQLite database for the custom Bible terminal UI application.

This task establishes the project skeleton and the command line surface only. No format parsing happens yet.

The CLI must accept the path to a single source file, an optional output location, and an optional output file name. When the file name is not supplied it must default to the input file name with a SQLite extension. The tool should be Python 3 and standard library only, matching the reference project, so that it can be dropped into the same environment as the terminal UI.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The repository contains a runnable package or script that can be invoked from a shell, and running it with a help flag prints usage for every supported option
- [x] #2 The CLI accepts a source file path as a positional argument plus optional flags for the output location, the output file name, and forcing a specific input format
- [x] #3 When no output file name is given, the output file is the input file base name with a .sqlite extension; when a name is given, that name is used
- [x] #4 The output location can be given as a directory, in which case the file name is placed inside it, or as a full file path, in which case that path is used directly
- [x] #5 When the output location is omitted, the database is written to the current working directory
- [x] #6 A missing output directory is created rather than causing a failure
- [x] #7 Running the CLI with no arguments prints usage and exits with a non zero status, and a successful run exits with status 0
- [x] #8 The project has a README placeholder that states the intended usage, and the tool runs on the Python version available in the environment
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
Package `bibles/` (cli.py, __main__.py) runnable via `python3 -m bibles` or `./bin/bibles`. Flags: -o/--output, -n/--name, -f/--format {usfm,usx,osis,vpl,usj}, --version.

Design decisions (please review):
- `--output` is a directory if it exists as one, ends in a separator, or has no file extension; otherwise it is a full file path.
- `--name` without an extension gets `.sqlite` appended; `--name` combined with a full-file-path `--output` is an error; `--name` must not contain a path separator.
- A successful run currently validates the source exists, resolves the output path, creates the parent directory, prints Source/Format/Output, and writes no database (deferred to TASK-004/014).
- No-args exits 2; CliError (e.g. missing source) exits 1.

Verification: `python3 -m unittest discover -s tests -t .` -> 22 tests OK; `python3 -m py_compile bibles/*.py tests/*.py` OK; manual `./bin/bibles --help` and bare `./bin/bibles` (exit 2). No linter/formatter installed (ruff/black absent); automated verification disabled in .agent/verification.json.

DoD #7 (style guide) not applicable: no UI component.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Scaffolded the Python 3 stdlib-only CLI with output path resolution, a bash wrapper, 22 unittest tests, README, AGENTS.md and CLAUDE.md.
<!-- SECTION:FINAL_SUMMARY:END -->
