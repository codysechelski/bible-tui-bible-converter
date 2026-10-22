---
id: TASK-014
title: Conversion pipeline and parser dispatch
status: In Progress
assignee:
  - '@claude'
created_date: '2026-10-22 14:12'
updated_date: '2026-10-22 14:58'
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
- [ ] #1 The CLI runs the full path of detect, parse, normalize, write and validate for a given input file and reports which format was detected and which parser ran
- [ ] #2 Each of the five supported formats is routed to its parser, and the forced format flag routes to the requested parser instead
- [ ] #3 A conversion that fails at any stage exits with a non zero status and a message that names the failing stage, and no partial or empty database is left behind
- [ ] #4 A successful conversion writes the database to the resolved output path and prints the output path along with a summary of the books, chapters and verses written
- [ ] #5 The pipeline reports validation results produced by the validation step rather than duplicating those checks
- [ ] #6 Automated tests cover the full pipeline for at least one format and cover the failure path for an unreadable or unsupported input
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
