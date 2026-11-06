# Pearl interface verification — 2026-11-07

## Delivered
- Pearl design layer, responsive layouts, local fonts, keyboard navigation, focus-managed dialogs, reduced-motion transitions, and visible request notifications.
- Accurate educational/simulation labels replacing unsupported hospital, physician, encryption, and real-dispatch claims.
- Safe transcript and generated-note rendering without a remote Markdown dependency.
- Complete encounter artifact reset, note invalidation after new lab input, and encounter/revision checks for late responses.
- Document generation blocked while a newer intake is pending.
- Unknown scenario IDs return 404 instead of another patient's case.
- Legacy API walkthrough no longer runs during pytest collection.

## Evidence
- `python -m pytest -q`: 40 passed.
- `python tests/browser_regressions.py URL`: 5 regression cases passed, covering literal transcript text, cleared documents, new labs, pending intake, and late medication checks.
- `python tests/browser_smoke.py URL`: all 5 prepared scenarios through intake, labs, SOAP, evidence and FHIR; calculator and medication controls; actual FHIR download; AVS/chart previews; keypad; Escape and focus restoration.
- All 5 workspaces checked at widths 1440, 768, and 390 pixels: no page overflow, no uncaught JavaScript errors in the feature walkthrough.
- JavaScript syntax and Git whitespace checks passed. Desktop and mobile screenshots reviewed.
- Independent review identified two stale-response races in Vaani; focused browser regressions reproduced them before correction and passed afterward.

## Boundaries
These are local synthetic tests, not clinical validation. Real microphone permissions, recognition accuracy, voice playback, real patients, emergency dispatch, healthcare compliance, and external EHR ingestion were not validated. Existing Starlette/httpx test-client deprecation warning remains. Browser checks create synthetic local records. No database is committed.
