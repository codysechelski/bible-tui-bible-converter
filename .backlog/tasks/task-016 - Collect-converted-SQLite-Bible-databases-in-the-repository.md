---
id: TASK-016
title: Collect converted SQLite Bible databases in the repository
status: To Do
assignee: []
created_date: '2026-10-22 15:01'
labels:
  - repo-layout
dependencies:
  - TASK-015
  - TASK-014
priority: medium
type: feature
ordinal: 2014
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The repository is not only a converter; it is also a collection of the SQLite databases it produces. Someone who clones this repository should be able to open a converted Bible straight from the repository root without running the tool first.

This task converts the chosen source texts into databases, commits them at the repository root, and records for each one where the source came from and under what licence it is published. It depends on TASK-015, which frees the repository root for these files.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Each converted database lives at the repository root under a file name that identifies the translation, and is committed to the repository
- [ ] #2 Each committed database passes the validation checks built into the tool and matches the reference schema
- [ ] #3 The source of each committed database and its licence are recorded in the repository, so the collection can be redistributed
- [ ] #4 The README lists the available converted databases and explains how to add another one
- [ ] #5 Re-converting the same source produces the same books, chapters and verses as the committed database
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
