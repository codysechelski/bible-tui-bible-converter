---
id: TASK-017
title: Accept zip archives and folders of book files as conversion input
status: Ready for Testing
assignee:
  - '@cody'
created_date: '2026-10-22 16:27'
updated_date: '2026-10-22 16:43'
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
- [x] #1 A zip archive given as SOURCE is converted: its book files are found, parsed and written as one database
- [x] #2 A folder given as SOURCE is converted the same way, searching subfolders
- [x] #3 Files that are not Bible text (metadata, stylesheets, versification, licences) are ignored; a folder with no Bible files, or with files in more than one format, fails with a clear message (--format picks one)
- [x] #4 A book that appears in more than one file with identical text is kept once with a warning; differing copies fail the parse
- [x] #5 A DBL metadata.xml in the bundle supplies the version abbreviation and name
- [x] #6 RTF book files in the layout of the ASV bundle (chapter headings, bold verse numbers) are parsed, with notes, titles and acrostic letters left out
- [x] #7 A failed run leaves nothing behind, including extracted archive files
- [x] #8 The three bundles in ~/Downloads (ASV, Biblia Livre Para Todos, KJV) convert, and README/docs/AGENTS.md describe the new input forms
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
Commit 416e51c. New bibles/sources.py (open_source, find_book_files, DBL metadata), parse_files in parsers/__init__.py (merge, identical repeats skipped, differing copies fail), Bible.add_book, parsers/rtf.py (ASV bundle layout), detection of {\rtf and .rtf. Docs: tool/docs/sources.md, README, normalization.md, samples/README.md, AGENTS.md. Sample: tool/samples/asv-rtf (RUT, JON, 3JN unchanged from the ASV bundle).

Verification: python3 -m py_compile (all modules) and python3 -m unittest discover -s tool/tests -t tool: 194 tests OK. Real bundles from ~/Downloads: ASV RTF zip -> 66 books, 31086 verses; KJV USFM zip (USX_1 + duplicate USX_2) -> 66 books, 31102 verses, the 66 repeats reported in one warning; Biblia Livre Para Todos USX zip -> 27 NT books, 7942 verses, version BLT from metadata.xml (needs --allow-partial); ASV USX zip and eBible eng-asv_usfm.zip (given directly, no cat) both identical verse-for-verse to bibles/bible_asv.sqlite. No bibles-* temp folders left after runs.

Known differences: the ASV RTF drops the Psalm 119 acrostic letters, which the committed eBible ASV keeps at the end of the preceding verse (eBible marks them \qc, a poetry line); and it keeps Habakkuk 3's subscription in 3:19, which the USFM drops. DoD #7 (style guide) not applicable.
<!-- SECTION:NOTES:END -->
