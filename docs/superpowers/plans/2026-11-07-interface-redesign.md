# Vaani and Tark Interface Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship the approved Pearl Vaani and Obsidian Tark interfaces with reproduced bugs fixed and verified GitHub pushes.
**Architecture:** Preserve FastAPI routes and vanilla DOM controllers. Add product-specific design layers, semantic UI chrome, and focused state/rendering fixes.
**Tech Stack:** Python, FastAPI, HTML, CSS, JavaScript; pytest and Playwright with installed Edge for verification.
**Spec:** ../specs/2026-11-07-interface-redesign-design.md

## Global constraints
- Pearl Vaani; Obsidian Tark. User approved 2026-11-07.
- Preserve existing feature set, use local fonts, honor reduced motion, support 390px screens.
- No framework migration, hosting deployment, or unsupported clinical/compliance claims.
- Push verified changes to the existing repositories; exclude databases and private data.

## Review focus
- Reset during an in-flight request must not attach old results to a new encounter.
- Successful runs and challenge switches must preserve edited code appropriately.
- User-controlled text must remain text throughout transcript, reports, and result rendering.
- Boolean/null/string test fixtures must survive sandbox serialization.
- Small screens, error responses, keyboard focus, and print/export must remain usable.

## Task 1: Fix reproduced defects
Files: both frontend/js/app.js; Tark backend/sandbox.py and tests/test_sandbox.py; Vaani backend/scenarios.py, backend/main.py, tests/test_api.py; browser regression scripts in tests/browser_regressions.py in each repository.
- [x] Add regressions for sandbox JSON primitives and missing scenario IDs; run and observe failures.
- [x] Add browser regressions for transcript injection, encounter reset, and successful-run editor preservation; run against baseline and observe failures.
- [x] Fix sandbox fixture serialization, scenario 404 behavior, text rendering, encounter artifact clearing and request identity guards, and challenge draft preservation. Check API response status and visible errors.
- [x] Rerun focused regressions and full backend suites.

## Task 2: Pearl Vaani
Files: frontend/index.html, frontend/css/vaani.css, frontend/css/pearl.css, frontend/js/app.js.
- [x] Add compact semantic header, workspace introduction, simplified navigation, accurate simulation labels, and accessible form/dialog labels.
- [x] Implement ivory/teal tokens, frosted white cards, improved type and spacing, responsive grids, dark ECG inset, print styles, and reduced-motion transitions.
- [x] Exercise all five tabs, intake, labs, calculators, records/export, scenarios, reset, dialog focus and mobile overflow in a real browser.

## Task 3: Obsidian Tark
Files: frontend/index.html, frontend/css/tark.css, frontend/css/obsidian.css, frontend/js/app.js.
- [x] Replace terminal chrome with product header, readable navigation, challenge context and focused actions. Remove CRT overlay default.
- [x] Implement graphite glass tokens, blue/silver accents, rounded panels, readable editor, adaptive grids, restrained transitions and reduced-motion behavior.
- [x] Exercise challenge drafts, run results, AST/CFG, complexity, fuzzing, recall, tutor, API errors and mobile navigation in a real browser.

## Task 4: Verification and publication
Files: README.md and docs in each repository.
- [x] Run complete pytest suites and browser regressions, JS syntax checks, desktop/mobile screenshot review, and diff checks.
- [x] Get an independent review, fix actionable findings and recheck affected flows.
- [x] Document actual verification and remaining boundaries; commit separately, fast-forward main, push, and compare remote commit hashes.


## Execution record
- Native implementation in the existing checkouts on separate codex branches, following the user's approval to proceed.
- Baselines: 39 Vaani tests and 21 Tark tests passed before edits.
- Reproduced transcript/test/fuzz HTML execution, stale encounter artifacts, pending-request races, lost solutions/drafts, JSON literal failures, and live network access during pytest collection before fixing them.
- Independent review's four actionable findings were corrected and covered by passing browser regressions.
- Final local verification: 40 Vaani and 26 Tark pytest tests, 5 Vaani and 7 Tark browser regression cases, feature walkthroughs, and all five workspaces at 1440/768/390px.
- Integration: explicit user authorization covers publishing to the existing GitHub repositories. Fast-forward main only; no force push.
