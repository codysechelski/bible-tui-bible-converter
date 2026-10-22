---
id: TASK-003
title: Shared verse model and text normalization rules
status: To Do
assignee: []
created_date: '2026-10-22 14:08'
updated_date: '2026-10-22 14:10'
labels:
  - core
dependencies:
  - TASK-002
references:
  - /Users/codysechelski/Developer/Projects/bible-esv
priority: high
type: feature
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
All five source formats must produce identical output for the same Bible, but each format expresses markup differently. USFM uses backslash markers, USX uses styled XML elements, OSIS wraps text in reference elements, VPL is bare text and USJ is JSON markers.

The schema stores one text column per verse with no place for headings, footnotes or poetry markers, so the rules for stripping non verse content, joining poetry lines, and handling notes have to be decided once and applied by every parser. Without a shared rule the same Bible converted from two formats would produce different verse text, which defeats the purpose of supporting multiple formats.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A shared in memory representation holds books, chapters and verses with book code, chapter number, verse number and verse text
- [ ] #2 Normalization removes non verse content from verse text, including headings, section titles, book introductions, footnote and endnote markers, cross references and figure markers
- [ ] #3 Poetry and paragraph lines within one verse are joined into a single verse text using a consistent documented separator
- [ ] #4 Whitespace is normalized so that verse text has no leading or trailing whitespace, no doubled spaces and no stray newlines, and verse text is never empty
- [ ] #5 The normalization rules are written down in the repository so the behaviour is discoverable without reading the code
- [ ] #6 Automated tests cover the rules with representative snippets, including a verse split across poetry lines and a verse containing a footnote
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
