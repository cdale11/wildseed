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
- [x] Publish tested source on the public main branch.

## World creation and powers (0.3.0)
- [x] Fresh random world setup, eight geographies, nine climate choices and exact previews.
- [x] Thirty validated god powers with brush controls and measured feedback.
- [x] Procedural biome colors, shaded relief, coasts, trees and creature sprites.
- [x] Save v3 migration and archive-before-replacement.
- [x] Bounded local runoff, sediment transport and cooling lava with visible map effects.
- [ ] Watershed-scale rivers, biome succession and deeper temperature adaptation experiments.

## Phase 1: ecological depth
- [x] Species-aware directional perception of prey, threats, food and materials.
- [ ] Demonstrate learned predator tracking/threat avoidance against frozen-policy baselines.
- [x] Reproducible paired learned/frozen runs with exposure-adjusted hunts and a directional policy probe.
- [x] Eight-value recurrent hidden-state memory persisted per organism; long-horizon gradient training remains open.
- [x] Tile seed banks, local dispersal and grass/tree competition.
- [x] Explicit local plant cohorts, population counts and inherited climate trait means.
- [x] Local water flow, suspended soil transport and lava cooling.
- [ ] Watershed-scale rivers, weather systems and nutrient cycles.
- [x] Two-parent genetic recombination, bounded ancestry records and ecotype counts.
- [ ] Speciation with reproductive isolation and validated species metrics.
- [ ] Deferred by owner: multi-seed 100k-tick stability runs. Ten paired 500-tick learned/frozen runs are documented; random-policy comparison remains open.
Acceptance: measurable behavioral adaptation and ecological diversity without scripted population replenishment, with published failure cases.

## Phase 2: human societies
- [x] Households with food ownership, demand-based occupations, house construction and traffic-made roads.
- [x] House/road decay and route-based inter-settlement caravans.
- [x] Resource-scarcity-driven occupations and barter between settlements.
- [ ] Sustained society validation, institutions, directed migration and deeper cultural transmission.
- [ ] Technology from composable operations and experimentation rather than fixed era transitions.
- [ ] Diplomacy/conflict grounded in resources and individual/social objectives.
Acceptance: settlements survive and fail for inspectable reasons; reproducible histories show several distinct development paths across seeds.

## Phase 3: scale and experimentation
- [ ] Structure-of-arrays state, vectorized learning and GPU-resident policy tensors.
- [ ] Deterministic phased tile work, spatial partitioning and regional simulation.
- [ ] Delta streams, interest management and client backpressure.
- [x] Administrator/spectator roles, bounded connections, per-peer rate limits, metrics and loopback load tests.
- [ ] Save migrations, replay/branching, experiment registry and deployment CI.
Acceptance: documented latency/memory curves and backend parity tolerances on specified Linux hardware.

## Phase 4: open-ended evolution research
- [ ] Adaptable network topology, developmental body plans and evolving sensory/action capabilities.
- [ ] Novelty archives, ecosystem diversity metrics and causal intervention tools.
- [ ] Evaluate unexpected behaviors against baselines; distinguish novelty from bugs/reward exploitation.
No promise of unlimited novelty or general intelligence. All behavior remains constrained by the simulated physical substrate.
