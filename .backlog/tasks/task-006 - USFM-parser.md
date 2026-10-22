---
id: TASK-006
title: USFM parser
status: To Do
assignee: []
created_date: '2026-10-22 14:08'
labels:
  - parsing
dependencies: []
priority: high
type: feature
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
USFM, the Unified Standard Format Markers, is plain text that uses backslash markers. A book file starts with an id marker such as \id GEN, chapters are introduced by a c marker and verses by a v marker, and a verse continues across following lines until the next marker. eBible.org and Paratext distribute USFM as one file per book, and a single file may also contain several books in sequence.

The parser must produce the shared verse model, resolve the book from its id marker, and apply the shared normalization rules so that the output is identical to the same Bible converted from another format.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The parser reads a USFM file and produces normalized books, chapters and verses through the shared model
- [ ] #2 Book identity comes from the id marker and resolves to the canonical book record, and a file containing more than one book is split into separate books in order
- [ ] #3 Chapters come from the c marker and verses from the v marker, and verse text continues across following lines until the next verse, chapter or book marker
- [ ] #4 Paragraph, poetry and character formatting markers do not leak into verse text
- [ ] #5 Non verse content such as title markers, section headings, table of contents entries and reminder markers is excluded from verse text
- [ ] #6 Footnotes, endnotes and cross references are removed or inlined consistently with the documented normalization policy
- [ ] #7 UTF-8 files are read correctly, and files carrying a byte order mark or a legacy encoding are handled without a crash
- [ ] #8 Automated tests cover a single book excerpt and a file containing multiple books
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
