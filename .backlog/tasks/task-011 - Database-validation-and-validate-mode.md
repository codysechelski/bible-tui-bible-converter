---
id: TASK-011
title: Database validation and validate mode
status: To Do
assignee: []
created_date: '2026-10-22 14:09'
updated_date: '2026-10-22 14:11'
labels:
  - validation
dependencies: []
references:
  - /Users/codysechelski/Developer/Projects/bible-esv/tools/build_sqlite.py
priority: medium
type: feature
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A quietly wrong database is worse than a failed conversion, because the terminal UI would happily display corrupt or missing verses.

The reference project validates its database thoroughly before shipping it: an integrity check, a foreign key check, book and chapter and verse counts, contiguous numbering, duplicate reference detection and empty verse text detection. This task brings that level of rigour to every conversion, and adds a mode that validates a database that already exists without converting anything.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Validation runs automatically at the end of every conversion and reports any problem it finds
- [ ] #2 Checks cover SQLite integrity, foreign keys, a book count of 66 with contiguous sort order and the correct testament split, contiguous chapter and verse numbering within each book, no duplicate book chapter verse references, and no empty verse text
- [ ] #3 A translation that legitimately omits verses is reported as a warning rather than a failure, and the totals from the reference project are used as a sanity check only
- [ ] #4 A validate mode accepts the path to an existing database, validates it without converting anything, and exits with a non zero status when validation fails
- [ ] #5 Validation output lists every check that was performed together with its result
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
