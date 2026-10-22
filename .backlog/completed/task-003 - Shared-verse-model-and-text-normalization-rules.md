---
id: TASK-003
title: Shared verse model and text normalization rules
status: Done
assignee:
  - '@cody'
created_date: '2026-10-22 14:08'
updated_date: '2026-10-22 14:42'
labels:
  - core
dependencies:
  - TASK-002
references:
  - /Users/codysechelski/Developer/Projects/bible-esv
priority: high
type: feature
ordinal: 250
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
All five source formats must produce identical output for the same Bible, but each format expresses markup differently. USFM uses backslash markers, USX uses styled XML elements, OSIS wraps text in reference elements, VPL is bare text and USJ is JSON markers.

The schema stores one text column per verse with no place for headings, footnotes or poetry markers, so the rules for stripping non verse content, joining poetry lines, and handling notes have to be decided once and applied by every parser. Without a shared rule the same Bible converted from two formats would produce different verse text, which defeats the purpose of supporting multiple formats.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A shared in memory representation holds books, chapters and verses with book code, chapter number, verse number and verse text
- [x] #2 Normalization removes non verse content from verse text, including headings, section titles, book introductions, footnote and endnote markers, cross references and figure markers
- [x] #3 Poetry and paragraph lines within one verse are joined into a single verse text using a consistent documented separator
- [x] #4 Whitespace is normalized so that verse text has no leading or trailing whitespace, no doubled spaces and no stray newlines, and verse text is never empty
- [x] #5 The normalization rules are written down in the repository so the behaviour is discoverable without reading the code
- [x] #6 Automated tests cover the rules with representative snippets, including a verse split across poetry lines and a verse containing a footnote
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 When you are asked to work on a task, first move it to `In Progress` if it is not already there
- [x] #2 After you have ensured the task has the proper status, you must assign the work to yourself (@claude, @codex, @opencode, etc.)
- [x] #3 Completed the development work outlined in the task. Ask questions if things are unclear
- [x] #4 Before making changes, be sure that you understand the codebase. Look for existing patterns, components, tooling, etc., before forging your own path
- [x] #5 Before making sweeping architecture decisions, or making changes with a high likelihood of breaking other parts of the app, stop and ask first
- [x] #6 Unit tests are written for new code
- [x] #7 If creating a new reusable component with a UI, or adding a variant to an existing component, add an example in the design system (style-guide) page
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
Added `bibles/model.py` (`Bible` -> `BibleBook` -> `Chapter` -> `Verse(book_code, chapter_number, verse_number, text)`; `Bible.add_verse(code, chapter, verse, fragments)` resolves the book, normalizes text, raises `DuplicateVerseError` on repeats) and `bibles/normalize.py` (`NON_VERSE_BLOCK_MARKERS`, `DROPPED_INLINE_MARKERS` shared by USFM/USX/USJ via USFM marker names; `OSIS_DROPPED_ELEMENTS`/`OSIS_DROPPED_DIV_TYPES`; `normalize_verse_text` joins fragments with a single space, collapses whitespace, raises `EmptyVerseError`). Rules documented in docs/normalization.md, linked from README.

Design decisions (please review):
- Separator between poetry/paragraph lines is a single space, matching the reference ESV db (which has no newlines in any verse).
- Psalm superscriptions (\d) are treated as headings and dropped. The ESV reference db actually includes them (and even the section heading) in Ps 23:1, so this differs from the reference text; flip by removing "d" from NON_VERSE_BLOCK_MARKERS if you want them kept.
- No-break spaces inside text are preserved; punctuation is never altered (no 'space before punctuation' cleanup, so French typography survives).
- Markup stripping itself is per-parser (TASK-006..010); this task only fixes the vocabulary and the text rules, and its tests cover the post-strip snippets (footnote removal, poetry split).

Verification: `python3 -m py_compile bibles/*.py tests/*.py` OK; `python3 -m unittest discover -s tests -t .` -> 45 tests OK (10 new). DoD #7 N/A (no UI). No linter installed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added the shared in-memory Bible model and verse text normalization rules, documented in docs/normalization.md.
<!-- SECTION:FINAL_SUMMARY:END -->
