---
id: TASK-018
title: 'Spike: strategy for localized book names in converted Bibles'
status: In Progress
assignee:
  - '@claude'
created_date: '2026-10-23 18:46'
updated_date: '2026-10-23 18:48'
labels:
  - schema
  - core
dependencies: []
priority: medium
type: spike
ordinal: 4014
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Decide how translated Bibles should carry localized book names (and related display metadata), and write the decision up as a spike document.

## Context

Cody converted a Portuguese Bible with this tool. The verse text came through in Portuguese as expected, but all 66 book names were English. That is structural, not a parser bug: `tool/bibles/books.py` is the single source of truth for the 66 books and holds only English `canonical_name` / `common_name` values mirrored from the reference `bible-esv` schema, and `bibles/writer.py` writes those values unchanged into the `books` table. `bible-tui` renders `books.common_name` (`bible_tui/store.py`), so a Portuguese Bible displays as "Genesis", "I Samuel", "John" instead of "Gênesis", "1 Samuel", "João".

## Constraints that shape any answer

- `SCHEMA` in `tool/bibles/writer.py` is copied from `bible-esv/tools/build_sqlite.py`, and the TUI depends on it (`bible_tui/versions.py` declares the table/column sets it requires). A schema change is the most breaking option and needs strong justification.
- Already-converted databases live in `bibles/` and are validated by `tool/tests/test_collection.py`; `tool/tests/test_samples.py` reads converted samples through the reference TUI's `BibleStore`.
- The canonical order, USFM/OSIS codes and slugs are language-neutral and should stay stable for lookups, cross-references and sort order. Only human-facing names are in question.

## Required reading (read-only)

`/Users/codysechelski/Developer/Projects/bible-tui` is the app that reads and displays these SQLite databases. Read and understand it so the recommendation reflects how it actually resolves and shows book names. Do not modify that repository, do not commit there, and do not run any mutating command against it.

## Deliverables

- A `.spike-docs/` folder at the repository root containing the spike writeup as Markdown.
- `.spike-docs/` added to `.gitignore`.
- The writeup presents several options (at least three) with pros, cons, breaking-change risk, rough effort and interaction with the TUI contract, then recommends the least-breaking option with a migration/back-compatibility story for databases already converted.

This is a decision spike: produce the analysis and the recommendation, do not implement the change in this task.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 .spike-docs/ exists at the repository root and contains the spike writeup as a Markdown file.
- [ ] #2 .spike-docs/ is listed in .gitignore, and git status shows no spike output staged or tracked.
- [ ] #3 The writeup documents current behavior with file references: where the converter sources book names (tool/bibles/books.py, tool/bibles/writer.py) and where bible-tui reads and renders them (e.g. bible_tui/store.py, bible_tui/versions.py).
- [ ] #4 The writeup presents at least three distinct options for localized book names (plus any in-scope UI/localization concerns the author identifies), each with pros, cons, breaking-change risk and rough effort.
- [ ] #5 Each option is assessed against the fixed database contract (SCHEMA in tool/bibles/writer.py and the requirements in bible_tui/versions.py), stating clearly whether it requires a schema change and what that would cost.
- [ ] #6 The writeup recommends one option as the least-breaking path, with rationale, and explains what happens to databases already converted and committed under bibles/ (including whether reconversion is needed).
- [ ] #7 The writeup shows how the Portuguese example would appear under each option (e.g. Genesis/Gênesis, I Samuel/1 Samuel, John/João) and explains how codes, slugs and sort order stay stable.
- [ ] #8 The writeup lists the open questions or decisions left to Cody.
- [ ] #9 No files outside .backlog/, .spike-docs/ and .gitignore were changed, and /Users/codysechelski/Developer/Projects/bible-tui is untouched.
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
