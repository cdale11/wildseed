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
- [x] Fresh random world setup, nine geographies, twelve climate choices and exact previews.
- [x] Thirty-five validated god powers with brush controls and measured feedback, including plague.
- [x] Procedural biome colors, shaded relief, coasts, trees and creature sprites.
- [x] Save v3 migration and archive-before-replacement.
- [x] Bounded local runoff, sediment transport and cooling lava with visible map effects.
- [x] Finite subsurface ore veins and weathering/erosion exposure make mineable resource availability change without a god power.
- [x] World-scale catchment routing and cumulative river channels that erode over time.
- [x] Disturbance-driven grassland, woodland and burn-scar succession with an ecological growth effect.
- [x] Explicit basin-stored lakes, Lake Country preset and persistent lake brush with movement/plant effects.
- [x] Persisted ledgers close the represented tile-water and mineral-plus-litter pools across weather, ecology, local routing and powers; external exchange categories are explicit.
- [x] Controlled 5,000-tick burn-scar → grassland → woodland recovery and temperature-trait climate-reversal tests.
- [ ] Calibrated, mass-conserving watershed and nutrient budgets across weather, terrain, plants and settlements; current local transport has only a conservation check.

## Phase 1: ecological depth
- [x] Species-aware directional perception of prey, threats, food and materials.
- [ ] Demonstrate learned predator tracking/threat avoidance against frozen-policy baselines.
- [x] Reproducible paired learned/frozen/value-ablation runs with exposure-adjusted hunts and predator-prey and grazer-threat directional probes.
- [x] Eight-value recurrent hidden-state memory persisted per organism; long-horizon gradient training remains open.
- [x] Per-organism online value heads and one-step temporal-difference credit for earlier neural actions, with frozen controls and save migration.
- [ ] Demonstrate a reliable behavioral gain from value learning against an immediate-reward ablation across replicated seeds and held-out tasks.
- [x] Run a ten-seed matched immediate-reward ablation and retain the negative result; provide a repeatable `--value-ablation` experiment mode.
- [x] Repeat the value ablation for ten matched 500-tick worlds; hunting gain remained unproven (mean −0.798 per 1,000 predator-ticks, three positive seeds).
- [x] Test opt-in predator proximity credit against a matched no-credit ablation; retain the mixed/negative result and keep ordinary worlds on the established policy.
- [x] Reject a four-move hunt-credit trace after a ten-seed ablation reduced hunting; retain the existing one-move credit.
- [x] Tile seed banks, local dispersal and grass/tree competition.
- [x] Grazer/human seed carriage couples foraging, movement and plant colonization with bounded trait-preserving transfers.
- [x] Contact-spread disease, inherited/acquired resistance and a plague/healing power loop.
- [x] Explicit local plant cohorts, population counts and inherited climate trait means.
- [x] Local water flow, suspended soil transport and lava cooling.
- [x] Bounded soil nutrient/litter recycling with plant uptake, grazing/death returns, fire ash and runoff transport.
- [x] Coarse traveling cloud fronts with elevation-sensitive rainfall and deterministic save/replay.
- [ ] Calibrated watershed, weather and nutrient budgets across land, plants, animals and settlements.
- [x] Two-parent genetic recombination, bounded ancestry records and ecotype counts.
- [x] Inherited mate-recognition signal, compatibility barrier and measured candidate rejection fraction.
- [ ] Speciation with reproductive isolation and validated species metrics.
- [x] Offline exact adult mating-compatibility component report for trusted saves; candidate groups are not validated species.
- [x] Forced-contact test: two incompatible adult mating pools reproduce within their pools with no cross-group children.
- [x] Controlled six-generation mutation test retains the mating barrier under forced contact; spontaneous, persistent divergence in normal worlds remains open.
- [ ] Deferred by owner: multi-seed 100k-tick stability runs. Ten paired 500-tick learned/frozen runs are documented; random-policy comparison remains open.
Acceptance: measurable behavioral adaptation and ecological diversity without scripted population replenishment, with published failure cases.

## Phase 2: human societies
- [x] Households with food ownership, demand-based occupations, house construction and traffic-made roads.
- [x] House/road decay and route-based inter-settlement caravans.
- [x] Resource-scarcity-driven occupations and barter between settlements.
- [x] Food-shortage-driven, route-based migration between reachable settlements with spare food and housing.
- [x] Surplus-funded communal granaries buffer household rations and delay famine migration using an actual food reserve.
- [ ] Sustained society validation, institutions, broader migration paths and deeper cultural transmission.
- [x] Bounded reward-gated imitation of local, same-culture human policy and value weights, with frozen controls and save replay.
- [x] Add a saved no-imitation ablation and run ten matched 500-tick worlds; measured settlement benefit was not established.
- [ ] Test whether peer learning improves held-out settlement outcomes versus a no-imitation ablation without collapsing policy diversity.
- [ ] Technology from composable operations and experimentation rather than fixed era transitions.
- [x] First compositional technology: resource-costed, order-sensitive tool trials with locally retained and caravan-transmitted designs.
- [ ] Broaden operation/material repertoires and validate sustained productivity gains across matched settlements.
- [ ] Diplomacy/conflict grounded in resources and individual/social objectives.
- [x] Scarcity-driven route-bound food raids and trade/raid-dependent settlement relations, with real food and raider energy costs.
- [ ] Broader negotiations, alliances, combat and individual political objectives.
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
- [x] Add per-kind trait spread and effective primary-parent lineage diversity, with bounded-ancestry caveats.
- [ ] Add dynamic ecological interaction-network metrics beyond the current fixed trophic roles.
- [ ] Evaluate unexpected behaviors against baselines; distinguish novelty from bugs/reward exploitation.
No promise of unlimited novelty or general intelligence. All behavior remains constrained by the simulated physical substrate.
