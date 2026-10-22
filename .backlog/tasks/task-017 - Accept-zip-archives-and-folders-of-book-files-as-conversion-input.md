---
id: TASK-017
title: Accept zip archives and folders of book files as conversion input
status: In Progress
assignee:
  - '@claude'
created_date: '2026-10-22 16:27'
labels:
  - input
dependencies:
  - TASK-016
priority: medium
type: feature
ordinal: 3014
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Bible downloads (Digital Bible Library bundles, eBible.org zips) are usually a zip holding one file per book, often with metadata and other files beside them. The converter only accepts a single file, so users have to unzip and concatenate books by hand, which does not work at all for XML and JSON formats. The converter should accept the zip itself, or the folder it expands to, find the book files inside, and convert them as one Bible. Some of these bundles ship the text as RTF (the ASV bundle in ~/Downloads), so an RTF parser for that layout is added too.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A zip archive given as SOURCE is converted: its book files are found, parsed and written as one database
- [ ] #2 A folder given as SOURCE is converted the same way, searching subfolders
- [ ] #3 Files that are not Bible text (metadata, stylesheets, versification, licences) are ignored; a folder with no Bible files, or with files in more than one format, fails with a clear message (--format picks one)
- [ ] #4 A book that appears in more than one file with identical text is kept once with a warning; differing copies fail the parse
- [ ] #5 A DBL metadata.xml in the bundle supplies the version abbreviation and name
- [ ] #6 RTF book files in the layout of the ASV bundle (chapter headings, bold verse numbers) are parsed, with notes, titles and acrostic letters left out
- [ ] #7 A failed run leaves nothing behind, including extracted archive files
- [ ] #8 The three bundles in ~/Downloads (ASV, Biblia Livre Para Todos, KJV) convert, and README/docs/AGENTS.md describe the new input forms
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
