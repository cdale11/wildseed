# Agent instructions and standard operating procedures

## Product intent

Build a maintainable, performant, original god simulation with procedural graphics, evolving terrain/ecology and adaptive organisms including humans. Headless Linux owns simulation; browsers are windows into it. Aim for emergent combinations of simple interactions and quantify novelty rather than claiming unlimited intelligence.

## Working agreement

- Work directly on main; never force-push or discard other contributors' changes.
- Inspect git status, this file, ROADMAP.md and mistakes.md before editing.
- Keep changes cohesive. Avoid unrelated refactors and dependencies without a demonstrated need.
- Never commit credentials, tokens, personal data, generated saves or cache files.
- Use `python3 -m wildseed.branch` for reproducible save-based intervention comparisons; keep generated branches and experiment manifests out of Git.
- Use `python3 -m wildseed.backup` for verified no-overwrite copies to separate storage; never treat an in-volume copy as off-host protection.
- Keep all simulation state/RNG authoritative on the server. Client render timing must not affect outcomes.
- No proprietary game assets, copied UI artwork or extracted game code.
- No hidden external LLM calls. Learning is local and inspectable.

## Implementation SOP

1. Identify acceptance criteria and the smallest complete change.
2. Preserve deterministic iteration, seeded random sources and save compatibility. Bump save version and provide migrations for incompatible schema changes.
3. Use spatial indexes for agent interactions, batched inference and bounded workloads. Profile before increasing process counts; tiny batches can run locally.
4. Validate external commands before mutation. Keep remote authentication, origin checks and payload limits intact.
5. Add tests for meaningful invariants, regressions, state continuation and cross-backend agreement. Do not add tests that merely restate trivial implementation.
6. Run `python3 -m unittest discover -s tests -v`. Exercise affected browser flows and run benchmarks for hot-path changes.
7. Update CHANGELOG.md and ROADMAP.md. Record actual mistakes with cause, fix, prevention and verification in mistakes.md.
8. Review the diff for secrets, accidental files and misleading claims; commit on main and push when access is authorized and available.
9. Report changes, evidence and limitations. Do not claim untested GPU behavior, remote deployment or sustained emergence.

## Architecture boundaries

- world.py: rules, state, RNG, persistence. No HTTP or DOM.
- plants.py and society.py: bounded cohort and human-society rules called by the authoritative world.
- Mineral nutrient and litter pools are authoritative tile state. Keep plant uptake, recycling, water transport and god-power effects bounded; use geography.client_tiles for both previews and active snapshots.
- geography.py: deterministic terrain/climate generation and map options.
- Biome succession derives map labels from authoritative climate, vegetation and bounded scar state. Initialize scar in previews, migrate it in old saves, and keep god-power restoration and submerged tiles consistent.
- weather.py: deterministic coarse cloud-grid evolution; use a separate seeded RNG from organisms, simultaneous advection, and persisted state. Preview weather must equal the newly created world's weather.
- watershed.py: periodic deterministic lowest-spill routing to ocean outlets; keep catchment accumulation bounded and use the shared client tile format for river rendering. Channel strength is diagnostic and must never add water. Basin-capacity changes must transfer overflow without clipping loss. This is not yet a calibrated full-cycle hydrology model.
- Inland lakes store water only in bounded drainage basins. Lake powers must carve a retaining rim that survives the next drainage refresh; lakes affect spawn, movement, migration and plant habitat. Keep previews and active snapshots identical for a chosen seed.
- powers.py: shared power catalog and measured authoritative effects. Every new power needs a state-effect test.
- New server starts must request world selection with random seeds. Do not restore implicit auto-resume. Preserve old saves before replacing worlds.
- brain.py: inference and training. Workers must not mutate authoritative state.
- Preserve reference-equivalent neural updates when changing sparse CPU inference/training. Benchmark full ticks at multiple population sizes before altering worker thresholds; do not assume using more CPUs is faster.
- Recurrent observations include each organism's previous hidden state; save/migrate that state and preserve old policy connections when input dimensions change.
- Value heads train only on authoritative CPU state. Persist pending credit and learned value weights, flush terminal transitions, keep frozen mode truly frozen, and clear stale traces when god powers mutate networks. Treat TD bootstrapping as a mechanism until held-out behavior improves against an ablation.
- Keep immediate-reward/value-head ablation behavior separately configurable and saved. Report negative paired results; the current smaller TD policy correction is a cautious response, not a validated gain.
- Human social learning stays local to a settlement and culture, uses a bounded mentor advantage and blend, and never runs in frozen mode. Persist recent-reward estimates and lesson counts; clear off-policy credit when sharing weights. Do not claim social benefit without an ablation.
- Behavioral novelty records count only executed neural choices, exclude guided movement, require enough observations, and remain bounded by species and archive size. Persist action histories and archive entries. Treat action-distribution distance and mode entropy as descriptors, not proof of intelligence or emergence.
- Society-directed migration routes are authoritative saved state. Check passability and destination existence each step; do not train the neural policy on a socially directed move as though it chose that action.
- Treat mate-signal bins and encounter rejection rates as proxies for reproductive divergence, not validated species. Preserve direct-mate compatibility and save migration when changing reproduction.
- server.py: transport, validation, tick ownership, persistence orchestration.
- Preserve admin/spectator roles, per-peer API limits and bounded connections when changing transport; no viewer command may mutate world state.
- web/: rendering and commands only; no duplicate simulation.
- tests/: deterministic, dependency-free baseline. Optional accelerator tests may skip with an explicit reason.

## Performance and reliability

Target 8 ticks/sec at 250 organisms / 96×64, measured on stated hardware; this is a target, not a benchmark claim. Population cap 2500. Profile serialization, training and snapshot costs separately. All available CPUs may participate in inference; do not create busywork to force 100% utilization. CUDA is optional and must fail clearly when explicitly selected but unavailable. Use bounded clients/rate limiting via a production proxy before public exposure. Keep saves on a persistent volume and back them up. Do not load untrusted snapshots.
