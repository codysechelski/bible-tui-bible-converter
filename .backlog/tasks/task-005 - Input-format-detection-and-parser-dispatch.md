---
id: TASK-005
title: Input format detection
status: To Do
assignee: []
created_date: '2026-10-22 14:08'
updated_date: '2026-10-22 14:11'
labels:
  - cli
  - parsing
dependencies:
  - TASK-001
priority: high
type: feature
ordinal: 10
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The user hands the tool one file path and expects the right parser to run without being told which format the file is in.

File extensions are only a hint. USFM books are distributed with a .usfm extension, USX and OSIS files are often .xml, VPL files are often .txt, and USJ files are often .json, so extension alone is not reliable. The content itself is a stronger signal: USX and OSIS are both XML but have distinct root elements, USJ is JSON, USFM is plain text containing backslash markers, and VPL is plain text whose lines begin with a book chapter verse reference.

This task builds the detection layer only. It returns which of the five supported formats a file appears to be, so that the conversion pipeline can pick the right parser. It also owns the flag that lets a user force a specific format when detection guesses wrong.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Detection identifies the format from the file extension and from content sniffing, and content wins when the extension is missing or misleading
- [ ] #2 Content sniffing distinguishes USX from OSIS by their XML root elements, recognises USJ by JSON shape, recognises USFM by backslash markers, and recognises VPL by a leading book chapter verse reference
- [ ] #3 An unsupported or undetectable file produces a clear error that names the supported formats and exits with a non zero status
- [ ] #4 A flag is available to force a specific parser for a file that is detected incorrectly, and the forced format is reported in the run output
- [ ] #5 Automated tests include at least one positive and one negative sample for each of the five formats
- [ ] #6 Detection identifies the format from the file extension and from content sniffing, and content wins when the extension is missing or misleading
- [ ] #7 Content sniffing distinguishes USX from OSIS by their XML root elements, recognises USJ by JSON shape, recognises USFM by backslash markers, and recognises VPL by a leading book chapter verse reference
- [ ] #8 An unsupported or undetectable file produces a clear error that names the supported formats and exits with a non zero status
- [ ] #9 A flag is available to force a specific format for a file that is detected incorrectly, and the forced format is reported in the run output
- [ ] #10 Automated tests include at least one positive and one negative sample for each of the five formats
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
