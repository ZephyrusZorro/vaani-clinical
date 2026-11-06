# Vaani and Tark interface redesign

## Intent
Give both existing tools a distinctive, polished interface that feels thoughtfully designed. The user requested futuristic glassmorphism, transitions, a thorough bug check, fixes, and publication to the existing GitHub repositories. The user selected one Pearl interface and one Obsidian interface.

## Approaches considered
- Obsidian for both: cohesive, but misses the requested contrast between products.
- Pearl for both: clean, but also misses that contrast.
- Pearl Vaani and Obsidian Tark: proposed assignment, matching a calm clinical workspace with a focused coding studio. Keep both existing FastAPI and vanilla frontend stacks.

## Vaani: Pearl
Use warm off-white backgrounds, translucent white panels, ink typography, fine neutral borders, and restrained deep teal accents. Replace the dense enterprise header with a compact brand, honest simulation status, and encounter context. Add a clear workspace title and short explanation. Simplify the five navigation labels to Intake, Lab results, Decision support, Documentation, and Scenarios. Preserve ECG controls, intake, calculators, lab extraction, notes, export, and scenarios. Group detail into spacious cards, keep warning colors meaningful, and keep the waveform readable on a dark inset surface. Replace unsupported physician, hospital, encryption, and real-dispatch claims with accurate educational-demo language.

## Tark: Obsidian
Use graphite backgrounds, layered translucent panels, soft silver text, and muted cool-blue accents. Replace terminal chrome, CRT defaults, decorative window dots, and uppercase filename headings with a compact product header and readable workspace navigation. Preserve the challenge list, editor, test runner, flowchart, complexity views, recall, and tutor. Make the selected challenge, editor actions, test status, and tutor hierarchy clear. Keep source code monospace, while using proportional typography for interface text.

## Shared interaction and accessibility
Use 160–240ms hover/focus transitions, short workspace entrance transitions, subtle panel lift, and no perpetual decorative animation. Honor prefers-reduced-motion. Provide visible keyboard focus, meaningful labels, keyboard-operable navigation, and usable layouts from 390px mobile through desktop. Keep glass blur limited to major surfaces with opaque fallback backgrounds. Avoid adding a frontend framework or remote visual dependencies.

## Bug investigation and fixes
Reproduce issues before fixing them. Focus on stale encounter artifacts, challenge/editor state preservation, async races, unsafe rendering of user-controlled text, API errors, exports, modal keyboard behavior, and sandbox test data handling. Add focused regression tests for meaningful behavior fixes. Preserve existing algorithm and clinical behavior unless a reproducible defect calls for a correction; do not expand medical recommendations.

## Verification and delivery
Run both complete backend suites, JavaScript syntax checks, and browser workflows at desktop and mobile sizes. Verify navigation and critical flows with screenshots and runtime error checks. Exercise Vaani intake, scenario, labs, calculators, notes/export and reset; exercise Tark challenge selection, editing, tests, analysis, fuzzing, tutor and recall. Document remaining limitations honestly. Commit each repository separately, push to its existing GitHub main branch when verified and fast-forward safe, and verify remote commit hashes. Do not include local databases or private data.

## Builder decisions
The proposed product-to-theme assignment is the builder's recommendation. Reuse local fonts and existing IDs where they support current behavior. Exact spacing, icons, layout breakpoints, and motion curves are implementation decisions. Use isolated development branches while working, then fast-forward the original branches for the requested publication.

## Non-goals
No new hosting deployment, provider integrations, clinical validation claims, or framework migration. Passing tests does not establish clinical suitability or secure execution of hostile code.
