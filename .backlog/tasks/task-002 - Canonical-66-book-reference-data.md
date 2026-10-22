---
id: TASK-002
title: Canonical 66-book reference data
status: Ready for Testing
assignee:
  - '@cody'
created_date: '2026-10-22 14:08'
updated_date: '2026-10-22 14:27'
labels:
  - core
dependencies: []
references:
  - /Users/codysechelski/Developer/Projects/bible-esv
  - /Users/codysechelski/Developer/Projects/bible-esv/bible_esv.sqlite
priority: high
type: feature
ordinal: 2
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Every supported source format identifies books by USFM 3 letter code (GEN, PSA, JHN and so on) or by a name, while the output schema requires a canonical name, a common name, a slug, a testament, and a sort order.

The reference project already fixes these conventions, and the generated database must match it exactly or the existing terminal UI will not read it. The reference list is 66 books, sort order 1 through 66, Old Testament 1 through 39 and New Testament 40 through 66. Common names convert a leading Roman numeral to Arabic, so I Samuel becomes 1 Samuel and III John becomes 3 John, and Revelation of John becomes Revelation. Slugs are the lowercased, dash separated common name, so 1 Samuel becomes 1-samuel and Song of Solomon becomes song-of-solomon.

This task builds that list once, in one place, so every parser resolves books the same way.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A single source of truth lists all 66 books with USFM code, canonical name, common name, slug, testament, and sort order
- [x] #2 Sort order is exactly 1 through 66 with the Old Testament occupying 1 through 39 and the New Testament 40 through 66
- [x] #3 Common names convert a leading Roman numeral prefix to Arabic numerals and map Revelation of John to Revelation
- [x] #4 Slugs are the lowercased, dash separated common name and match the reference project for all 66 books, including numbered books such as 1-samuel and 3-john
- [x] #5 Each book also records its expected chapter count, matching the reference project, for example Psalms 150 and Revelation 22
- [x] #6 A USFM book code that is not in the 66 book list produces a clear, named error rather than a silently skipped book
- [x] #7 Automated tests cover the naming, slug and testament rules for all 66 books and confirm agreement with the reference database
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added `bibles/books.py`: `BOOKS` (66 frozen `Book` records in canonical order), `book_for_code` (case/whitespace-insensitive USFM lookup) and `UnknownBookError(ValueError)` carrying `.code`. `common_name`/`slugify` copy the reference `tools/build_sqlite.py` rules verbatim; testament is derived from sort order (<=39 old).

Design decision (please review): deuterocanonical/apocrypha codes (TOB, SIR, ...) raise UnknownBookError like any other unknown code. Whether the pipeline skips them with a warning or fails is left to TASK-014.

Verification: `python3 -m py_compile bibles/*.py tests/*.py` OK; `python3 -m unittest discover -s tests -t .` -> 35 tests OK (13 new), including a read-only comparison of all 66 books + chapter counts against bible_esv.sqlite (skipped if that file is absent). README unchanged: no user-visible behavior. DoD #7 N/A (no UI). No linter installed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added the canonical 66-book table and lookup in bibles/books.py with tests that confirm it matches the reference database.
<!-- SECTION:FINAL_SUMMARY:END -->
