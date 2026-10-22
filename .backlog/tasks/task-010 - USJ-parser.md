---
id: TASK-010
title: USJ parser
status: To Do
assignee: []
created_date: '2026-10-22 14:09'
updated_date: '2026-10-22 14:10'
labels:
  - parsing
dependencies:
  - TASK-003
priority: high
type: feature
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
USJ is the JSON serialization of USFM. Instead of backslash markers, the same structure is expressed as JSON objects carrying a mark property, so a book identifier is an object whose mark is id, a chapter is an object whose mark is c, a verse is an object whose mark is v, and nested content such as paragraph and poetry styles appear as nested arrays.

The parser must produce the shared verse model and apply the shared normalization rules, and it must fail loudly on malformed JSON rather than writing a partial database.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The parser reads a USJ file and produces normalized books, chapters and verses through the shared model
- [ ] #2 JSON markers are mapped to their USFM equivalents, including id for book, c for chapter, v for verse, and the paragraph, poetry and character styles
- [ ] #3 Nested text content is flattened into the verse text with markup removed, and the resulting verse text is never empty
- [ ] #4 A file containing several books is parsed in book order
- [ ] #5 Malformed JSON produces a clear error naming the file and the parse failure, and no database is written
- [ ] #6 Automated tests cover a USJ excerpt containing a book, a chapter, a verse and a nested paragraph marker
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
