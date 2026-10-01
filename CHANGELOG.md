# Changelog

## 0.9.0 — 2026-10-02

- Added administrator and read-only spectator tokens, with spectator controls disabled in the browser.
- Bounded the HTTP server to 64 active connections and API traffic to 120 requests per ten seconds per peer; excess work receives 503 or 429.
- Added administrator-only `/api/metrics` and a repeatable local HTTP load test.

## 0.8.0 — 2026-10-02

- Organisms now feed their previous eight hidden activations into the next neural decision, giving policies recurrent state across ticks.
- Recurrent state persists in saves; v1–v9 policies migrate with zero-weight memory connections, preserving their existing input/output weights.
- Save schema v10 migrates pending predator move traces as well as policies. Training remains one-step and does not backpropagate through time.

## 0.7.0 — 2026-10-02

- Settlements with food surpluses now barter through pathfinding caravans for scarce ore or wood; goods leave stock on dispatch and arrive after route-dependent travel.
- Caravans create traffic along passable land routes and render on the browser map. Disconnected settlements cannot trade through water.
- Empty settlements lose food and houses, then become abandoned; this appears in the world chronicle.
- Save schema v9 preserves in-transit shipments and migrates v1–v8 worlds.

## 0.6.0 — 2026-10-02

- Added settlement households with members, ownership of stored food and rationing.
- Human work now follows local shortages: farming, woodcutting, mining and construction draw on actual tile and town resources.
- Repeated human travel wears paths into roads that lower movement energy cost; roads render on the terrain.
- Save schema v8 migrates v1–v7 worlds and preserves households, occupations and roads.

## 0.5.0 — 2026-10-02

- Added bounded surface runoff, downhill sediment transport, lava flow and cooling; rain, drought and volcano powers feed those fields, and water/lava render on the map.
- Added explicit local grass/tree cohort counts with inherited temperature/moisture preferences and climate-dependent growth. Seed dispersal carries traits with variation during colonization.
- Added optional two-parent reproduction, neural-weight recombination, heritable thermal preference, bounded ancestry records and ecological type counts.
- Save schema v7 migrates v1–v6 worlds; clients inspect plant populations, parent IDs, runoff and lava.
- GPU validation and 100,000-tick stability runs are deferred at the owner's request.

## 0.4.0 — 2026-10-01

- Added reproducible paired learning/frozen ecology experiments, predator hunts and exposure-adjusted metrics, and a directional prey-cue probe.
- Successful predator hunts now also train the preceding move, giving delayed credit to navigation; this state is saved for exact continuation.
- Save schema v5 persists training mode, hunt counts and navigation credit; v1–v4 saves migrate.
- Graceful SIGTERM now flushes the active world to disk for container shutdown.
- Ten paired 500-tick seeds increased mean exposure-adjusted hunts from 13.06 to 14.24 per 1,000 predator-ticks, but the directional probe remained near zero. Tracking is still an open research task.

## 0.3.1 — 2026-10-01

- Added grass and tree seed banks, local dispersal, vegetation competition and fire/flood seed loss so bare ground recolonizes from neighboring life.
- Nature and biome powers now establish matching seed banks; saves migrate to version 4 from versions 1–3.
- Stopped all local preview game instances at the owner's request; this release leaves no server running.

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
