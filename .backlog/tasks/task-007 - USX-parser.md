---
id: TASK-007
title: USX parser
status: In Progress
assignee:
  - '@claude'
created_date: '2026-10-22 14:08'
updated_date: '2026-10-22 14:47'
labels:
  - parsing
dependencies:
  - TASK-003
priority: high
type: feature
ordinal: 6
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
USX is the XML serialization of USFM, published by the Digital Bible Library and used by eBible.org as one of its preferred input formats. A document looks like a usx root element containing book elements whose id attribute is a USFM code, chapter elements whose s attribute is the chapter number, and verse elements whose s attribute is the verse number. Paragraph, poetry and character styles appear as nested elements, and notes appear as note elements.

The parser must produce the shared verse model and apply the shared normalization rules.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The parser reads a USX file and produces normalized books, chapters and verses through the shared model
- [x] #2 The book id attribute resolves to the canonical book record, and chapter and verse numbers come from the s attributes
- [x] #3 Paragraph, poetry and character style elements contribute their text to the enclosing verse and their markup does not appear in the output
- [x] #4 Note and cross reference elements are removed or inlined consistently with the documented normalization policy
- [x] #5 A document containing several books is parsed in book order
- [x] #6 An XML document that is not USX produces a clear error rather than an empty database
- [x] #7 Automated tests cover a USX excerpt that includes verse text, paragraph and poetry markup, and a note
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
Added `bibles/parsers/usx.py`: walks the ElementTree and feeds the shared `MarkerEvents`, so USX text is identical to USFM.

- book: `code` attribute (USX 2/3) or `id`; chapter/verse numbers from `number` or, if absent, from `sid` (the task text says 's attribute'; real USX uses number/sid). `eid` end milestones close the verse, so stray text after an end milestone is not verse text.
- para -> paragraph marker by style (headings etc. dropped by style), char/note -> character markers (notes dropped), figure -> fig; sidebar, periph, ms, optbreak skipped; table rows/cells separate fragments.
- Non-USX root, malformed XML, or no verses -> ParseError.

Verification: `python3 -m py_compile bibles/*.py bibles/parsers/*.py tests/*.py` OK; `python3 -m unittest discover -s tests -t .` -> 110 tests OK (tests/test_parsers.py is new, incl. one passage in all five formats producing identical verses). Real-data smoke test (scratchpad, not committed): eBible.org World English Bible (engwebp) USFM, all 66 book files, parsed with 0 errors (31,098 verses, 5 warnings for verses WEB omits, e.g. ACT 8:37); the eBible VPL edition parsed to the same 31,098 references and wrote a 66-book / 1,189-chapter database through write_database. Text matched USFM except Psalm titles (\\d) and Song of Solomon speaker labels (\\sp), which eBible's VPL keeps and our policy drops, and one source-faithful spacing difference (PSA 68:32). eBible no longer serves USX/OSIS downloads at the usual URLs, so USX/OSIS/USJ are covered by fixtures only. Committed together in c0e1769 (shared core + cross-format test). DoD #7 N/A. No linter installed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added the USX parser on the shared marker model.
<!-- SECTION:FINAL_SUMMARY:END -->
