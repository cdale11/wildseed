# Changelog

## 0.3.0 — 2026-10-01

- Fresh-world startup with random rerollable previews; eight geographies, nine climate choices, three sizes and initial-life options.
- Expanded to 30 god powers with adjustable brush/strength and actual state-change feedback.
- Fixed silent no-effect spawning and delayed removal of submerged vegetation.
- Added biome-sensitive color palettes, relief shading, coastal foam, procedural trees, creature sprites and culture colors.
- Added temperature effects on plant growth and organism energy, plus mutable biome classification.
- Save schema v3 migrates v1/v2 worlds; previous worlds are archived before replacement, and resume is explicit via --load.
- Shared clients reconnect without resetting the running world; stale world-replacement commands are rejected.
- Cognitive policies remain locally trained, inherited MLPs; no external inference service or scripted hunting was introduced.

## 0.2.0 — 2026-10-01

- Added species-specific three-tile food/prey, threat/fire and material perception with terrain occlusion and periodic-boundary support.
- Expanded policies to 20 inputs; added version 1 → 2 save migration that retains existing learned connections.
- Added four perception/migration regression tests; all 14 tests pass.
- This adds sensory capability; improved hunting/avoidance has not yet been demonstrated against behavioral baselines.

## 0.1.0 — 2026-10-01

Initial runnable prototype:
- Seeded tile terrain, seasonal moisture, vegetation, fire and sediment movement.
- Organism neural policies with online learning and mutated inheritance.
- Grazers, predators, humans, resource extraction and basic settlements.
- Headless HTTP simulation server, browser canvas atlas, powers, overlays and inspection.
- Atomic JSON snapshots including policies and random state; periodic autosave.
- CPU multiprocessing and optional CUDA inference implementation (hardware validation pending).
- Tests, benchmark command, container configuration and agent development SOP.

Repository creation succeeded through a fresh task after the original task retained a stale GitHub browser denial. All 25 baseline files were published to main. GitHub SSH authentication was subsequently configured and local/published histories reconciled without source differences or a force-push.
