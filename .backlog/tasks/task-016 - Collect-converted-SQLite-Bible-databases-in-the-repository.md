---
id: TASK-016
title: Collect converted SQLite Bible databases in the repository
status: Ready for Testing
assignee:
  - '@cody'
created_date: '2026-10-22 15:01'
updated_date: '2026-10-22 16:11'
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
- [x] #1 Each converted database lives at the repository root under a file name that identifies the translation, and is committed to the repository
- [x] #2 Each committed database passes the validation checks built into the tool and matches the reference schema
- [x] #3 The source of each committed database and its licence are recorded in the repository, so the collection can be redistributed
- [x] #4 The README lists the available converted databases and explains how to add another one
- [x] #5 Re-converting the same source produces the same books, chapters and verses as the committed database
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
Converted KJV and ASV (chosen by Cody) from the eBible.org USFM zips (cat eng-kjv/*.usfm > KJV.usfm, so metadata version is KJV / ASV like the reference ESV) into bible_kjv.sqlite and bible_asv.sqlite at the root. The README section Converted Bibles records the source URL, source-file date, zip SHA-256 and licence for each, and how to add another. New tool/tests/test_collection.py checks every root database is listed, validates strictly, matches the reference schema and has the expected version and counts.

Results: KJV 66 books, 1189 chapters, 31102 verses (Apocrypha and front matter skipped); ASV 66, 1189, 31086 (the 16 NT verses the ASV omits are absent; validation warns). tool/bin/bibles --validate passes for both with 0 failures. Re-converting each source gave an identical SHA-256 over slug, chapter, verse and text of every verse.

Verification: python3 -m unittest discover -s tool/tests -t tool (165 tests OK). Note: the writer creates files with mode 0600 (mkstemp), so the databases were chmod 644 before committing. DoD #7 does not apply.

Follow-up (Cody): databases moved to bibles/ (git mv). A conversion without --output now writes to bibles/ (cli.COLLECTION_DIR, resolved from the package location); --name alone only renames; relative --output still uses the working directory. Tests patch COLLECTION_DIR (test_cli, test_detect) or run the wrapper from a copied tool/ layout (test_samples), so the suite never writes into the real bibles/; a stray bibles/notes.sqlite from test_detect found during this work was removed and the test fixed. Verification: py_compile ok; python3 -m unittest discover -s tool/tests -t tool OK; tool/bin/bibles run from the scratchpad without -o wrote to bibles/ (smoke file removed).
<!-- SECTION:NOTES:END -->
