---
id: TASK-015
title: >-
  Move tooling into a dedicated folder so the repo root holds converted
  databases
status: Ready for Testing
assignee:
  - '@cody'
created_date: '2026-10-22 15:01'
updated_date: '2026-10-22 16:11'
labels:
  - repo-layout
dependencies: []
priority: medium
type: chore
ordinal: 1014
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
This repository has two jobs: it ships the tooling that converts a text-formatted Bible into a SQLite database, and it collects the converted databases themselves. Today the tooling sits at the repository root (the `bibles` package, `bin/bibles`, `tests/` and `docs/`), so the root doubles as a source tree and as the place where converted `.sqlite` files land. Those two uses collide.

Create a single new top-level folder that holds all of the tooling, so the repository root becomes the home for the converted SQLite Bible databases. Nothing about how the tool behaves changes; this is a move plus the path updates it forces: the CLI wrapper, test discovery, documentation links and the repository map.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All tooling lives under a single new top-level folder (the `bibles` package, the `bin/bibles` wrapper, `tests/` and `docs/`), and the repository root holds no tooling source files
- [x] #2 `bin/bibles` still runs from any working directory after the move, and `python3 -m bibles` still works from the new package root, with output path handling unchanged
- [x] #3 The test suite still passes when run with the documented command, updated for the new layout
- [x] #4 README and AGENTS.md describe the new layout: where the tooling lives, the updated run and test commands, and that the repository root holds the converted databases
- [x] #5 A converted database written to the repository root is a trackable file rather than an ignored one, and the existing ignore rules for generated caches (`__pycache__/`, `*.pyc`) still apply
- [x] #6 The move is recorded as renames in git history rather than deletions and re-additions, and no tool behaviour changes as a result of the move
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 When you are asked to work on a task, first move it to `In Progress` if it is not already there
- [x] #2 After you have ensured the task has the proper status, you must assign the work to yourself (@claude, @codex, @opencode, etc.)
- [x] #3 Completed the development work outlined in the task. Ask questions if things are unclear
- [x] #4 Before making changes, be sure that you understand the codebase. Look for existing patterns, components, tooling, etc., before forging your own path
- [x] #5 Before making sweeping architecture decisions, or making changes with a high likelihood of breaking other parts of the app, stop and ask first
- [x] #6 Unit tests are written for new code
- [ ] #7 If creating a new reusable component with a UI, or adding a variant to an existing component, add an example in the design system (style-guide) page
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
Moved bibles/, bin/, tests/, docs/ and samples/ into tool/ with git mv (36 renames). No code changes were needed: bin/bibles resolves the package relative to itself and the tests locate files from __file__. REPO_ROOT in test_cli.py and test_samples.py is renamed TOOL_ROOT. README, AGENTS.md, tool/samples/README.md and tool/docs/validation.md use tool/ paths. .gitignore adds build/ (scratch output); a .sqlite at the root is not ignored (checked with git check-ignore).

Verification: py_compile over tool/bibles, tool/bibles/parsers and tool/tests (ok); python3 -m unittest discover -s tool/tests -t tool (160 tests OK); tool/bin/bibles run from another directory converted tool/samples/kjv.usfm; cd tool && python3 -m bibles --version printed bibles 0.1.0. DoD #7 (style guide) does not apply.

Follow-up (Cody): the root now has two directories, tool/ and bibles/; the converted databases live in bibles/ rather than at the root itself (commit 'feat(cli): collect databases in bibles/...').
<!-- SECTION:NOTES:END -->
