# Roadmap

## Phase 0: runnable foundation
- [x] Seeded terrain and procedural canvas rendering.
- [x] Shared server simulation and browser interaction.
- [x] Individual online-trained policies and inherited mutations.
- [x] Energy/food/reproduction/death and basic human settlements.
- [x] Save/reload with deterministic continuation tests.
- [x] CPU process inference and optional CUDA implementation.
- [ ] Validate CUDA on real or compute-enabled virtual GPU.
- [ ] Benchmark and optimize full tick scaling across available CPUs.
- [x] Publish tested source on the public main branch.

## World creation and powers (0.3.0)
- [x] Fresh random world setup, eight geographies, nine climate choices and exact previews.
- [x] Thirty validated god powers with brush controls and measured feedback.
- [x] Procedural biome colors, shaded relief, coasts, trees and creature sprites.
- [x] Save v3 migration and archive-before-replacement.
- [ ] Physical hydrology/lava, biome succession and deeper temperature adaptation experiments.

## Phase 1: ecological depth
- [x] Species-aware directional perception of prey, threats, food and materials.
- [ ] Demonstrate learned predator tracking/threat avoidance against frozen-policy baselines.
- [ ] Recurrent memory.
- [ ] Explicit plant populations, seed dispersal, plant genomes and competition.
- [ ] Water flow, rivers, sediment budgets, temperature, weather and nutrient cycles.
- [ ] Sexual reproduction, ancestry graphs, ecological niches and speciation metrics.
- [ ] Multi-seed 100k-tick stability runs; compare learned vs frozen/random policies.
Acceptance: measurable behavioral adaptation and ecological diversity without scripted population replenishment, with published failure cases.

## Phase 2: human societies
- [ ] Households, occupations, ownership, construction/decay, roads and transport.
- [ ] Trade, resource scarcity, institutions, migration and cultural transmission.
- [ ] Technology from composable operations and experimentation rather than fixed era transitions.
- [ ] Diplomacy/conflict grounded in resources and individual/social objectives.
Acceptance: settlements survive and fail for inspectable reasons; reproducible histories show several distinct development paths across seeds.

## Phase 3: scale and experimentation
- [ ] Structure-of-arrays state, vectorized learning and GPU-resident policy tensors.
- [ ] Deterministic phased tile work, spatial partitioning and regional simulation.
- [ ] Delta streams, interest management and client backpressure.
- [ ] Metrics, bounded connections, rate limits, authenticated roles and load tests.
- [ ] Save migrations, replay/branching, experiment registry and deployment CI.
Acceptance: documented latency/memory curves and backend parity tolerances on specified Linux hardware.

## Phase 4: open-ended evolution research
- [ ] Adaptable network topology, developmental body plans and evolving sensory/action capabilities.
- [ ] Novelty archives, ecosystem diversity metrics and causal intervention tools.
- [ ] Evaluate unexpected behaviors against baselines; distinguish novelty from bugs/reward exploitation.
No promise of unlimited novelty or general intelligence. All behavior remains constrained by the simulated physical substrate.
