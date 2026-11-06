# Contrast and product depth refinement

User request: improve both projects, fix bugs, and move beyond the pale/simple appearance. Continue the approved light Vaani / dark Tark direction with stronger color, hierarchy, useful detail, and motion.

## Design decisions
- Vaani: crisp pearl canvas, saturated deep-teal primary surfaces, stronger ink text, subtle blue/coral detail, a dark telemetry strip, and a guided intake start state. Add encounter progress indicators that reflect actual state.
- Tark: ink-blue backdrop, violet/blue edge lighting, distinct panel levels, readable 13px source text with safe syntax highlighting, challenge search, and draft-save feedback.
- Keep glass effects restrained to primary layers, avoid perpetual decorative motion, respect reduced motion, and preserve mobile workflows.
- Retain the existing framework and feature set. New functionality stays focused on discovery, editing, and trustworthy feedback.

## Implementation plan
- [x] Reproduce and add regression coverage for latest lab values and fail-then-pass progress tracking.
- [x] Fix biomarker replacement/merging, inaccurate solved counters and streak reporting, and related UI state races.
- [x] Add safe syntax highlighting, challenge filtering, and resilient local draft persistence to Tark.
- [x] Add Vaani quick-start prompts, real encounter progress, richer empty states, and stronger visual hierarchy.
- [x] Refine both design layers, inspect screenshots, and verify all workspaces at desktop/tablet/mobile sizes.
- [x] Run full backend/browser suites and independent review. Refresh screenshots/documentation, commit, push under the user's existing publication authorization, and verify remote hashes.

## Evidence boundaries
Use temporary databases for browser review. Do not change clinical decision rules or claim clinical validation. Local browser draft persistence is not synchronization or a security boundary.


## Execution evidence
- Baselines: 40 Vaani and 26 Tark backend tests passed.
- Regression-first fixes: latest/cumulative labs, labs-before-intake, fail-then-pass solved state, attempt counts, UTC streaks, old aggregate repair, lab-pending document guards, conversational critical counters, cross-tab drafts, and stale result labels.
- Product checks cover prompt prefill, actual progress, safe source coloring, search/empty state, reload/empty drafts, storage failures, and different tabs.
- Independent review reproduced the cross-tab overwrite and stale critical-count bugs; both received failing regressions and passing fixes. Long-line editor scrolling was also checked by the reviewer.
- Existing UI/API contracts and the previously authorized GitHub publication flow are preserved.
