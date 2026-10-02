# Roadmap

## Phase 0: runnable foundation
- [x] Seeded terrain and procedural canvas rendering.
- [x] Shared server simulation and browser interaction.
- [x] Individual online-trained policies and inherited mutations.
- [x] Energy/food/reproduction/death and basic human settlements.
- [x] Save/reload with deterministic continuation tests.
- [x] Graceful SIGTERM save for Linux/container shutdown.
- [x] CPU process inference and optional CUDA implementation.
- [ ] Deferred by owner: validate CUDA on a real or compute-enabled virtual GPU when hardware is available.
- [ ] Benchmark and optimize full tick scaling across available CPUs.
- [x] Profile and reduce serial neural update work; compare one and all-affinity workers at 250, 1,000 and 2,000 starting organisms.
- [x] Remove generator overhead in policy inference and gradients; verify reference-equivalent math and full-tick behavior.
- [x] Publish tested source on the public main branch.

## World creation and powers (0.3.0)
- [x] Fresh random world setup, eight geographies, twelve climate choices and exact previews.
- [x] Thirty-three validated god powers with brush controls and measured feedback.
- [x] Procedural biome colors, shaded relief, coasts, trees and creature sprites.
- [x] Save v3 migration and archive-before-replacement.
- [x] Bounded local runoff, sediment transport and cooling lava with visible map effects.
- [x] World-scale catchment routing and cumulative river channels that erode over time.
- [x] Disturbance-driven grassland, woodland and burn-scar succession with an ecological growth effect.
- [ ] Explicit lakes, calibrated watershed hydrology, long-horizon biome succession validation and deeper temperature adaptation experiments.

## Phase 1: ecological depth
- [x] Species-aware directional perception of prey, threats, food and materials.
- [ ] Demonstrate learned predator tracking/threat avoidance against frozen-policy baselines.
- [x] Reproducible paired learned/frozen runs with exposure-adjusted hunts and a directional policy probe.
- [x] Eight-value recurrent hidden-state memory persisted per organism; long-horizon gradient training remains open.
- [x] Per-organism online value heads and one-step temporal-difference credit for earlier neural actions, with frozen controls and save migration.
- [ ] Demonstrate a reliable behavioral gain from value learning against an immediate-reward ablation across replicated seeds and held-out tasks.
- [x] Tile seed banks, local dispersal and grass/tree competition.
- [x] Explicit local plant cohorts, population counts and inherited climate trait means.
- [x] Local water flow, suspended soil transport and lava cooling.
- [x] Bounded soil nutrient/litter recycling with plant uptake, grazing/death returns, fire ash and runoff transport.
- [x] Coarse traveling cloud fronts with elevation-sensitive rainfall and deterministic save/replay.
- [ ] Calibrated watershed, weather and nutrient budgets across land, plants, animals and settlements.
- [x] Two-parent genetic recombination, bounded ancestry records and ecotype counts.
- [x] Inherited mate-recognition signal, compatibility barrier and measured candidate rejection fraction.
- [ ] Speciation with reproductive isolation and validated species metrics.
- [ ] Deferred by owner: multi-seed 100k-tick stability runs. Ten paired 500-tick learned/frozen runs are documented; random-policy comparison remains open.
Acceptance: measurable behavioral adaptation and ecological diversity without scripted population replenishment, with published failure cases.

## Phase 2: human societies
- [x] Households with food ownership, demand-based occupations, house construction and traffic-made roads.
- [x] House/road decay and route-based inter-settlement caravans.
- [x] Resource-scarcity-driven occupations and barter between settlements.
- [x] Food-shortage-driven, route-based migration between reachable settlements with spare food and housing.
- [ ] Sustained society validation, institutions, broader migration paths and deeper cultural transmission.
- [x] Bounded reward-gated imitation of local, same-culture human policy and value weights, with frozen controls and save replay.
- [ ] Test whether peer learning improves held-out settlement outcomes versus a no-imitation ablation without collapsing policy diversity.
- [ ] Technology from composable operations and experimentation rather than fixed era transitions.
- [ ] Diplomacy/conflict grounded in resources and individual/social objectives.
Acceptance: settlements survive and fail for inspectable reasons; reproducible histories show several distinct development paths across seeds.

## Phase 3: scale and experimentation
- [ ] Structure-of-arrays state, vectorized learning and GPU-resident policy tensors.
- [ ] Deterministic phased tile work, spatial partitioning and regional simulation.
- [ ] Delta streams, interest management and client backpressure.
- [x] Administrator/spectator roles, bounded connections, per-peer rate limits, metrics and loopback load tests.
- [x] Save migrations, reproducible local branches, intervention manifests and test CI.
- [x] Checksum-verified, no-overwrite backup command for trusted saves.
- [ ] Automated deployment and off-host save backups.
Acceptance: documented latency/memory curves and backend parity tolerances on specified Linux hardware.

## Phase 4: open-ended evolution research
- [ ] Adaptable network topology, developmental body plans and evolving sensory/action capabilities.
- [x] Save-based causal intervention branches with source/output hashes and summary metrics.
- [x] Bounded observed-action novelty archive and dominant-action diversity metric, with deterministic saves.
- [ ] Add ecological network, trait and lineage diversity metrics beyond dominant action modes.
- [ ] Evaluate unexpected behaviors against baselines; distinguish novelty from bugs/reward exploitation.
No promise of unlimited novelty or general intelligence. All behavior remains constrained by the simulated physical substrate.
