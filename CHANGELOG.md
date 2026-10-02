# Changelog

## 0.30.0 — 2026-10-03

- Added an offline matched learned/frozen emergence audit. It computes ecological interaction shares in disjoint windows, their total-variation shifts, and distances between learned-world novelty records and same-kind frozen-control records. All candidate patterns remain explicitly unverified; this is a comparison instrument, not proof of adaptive emergence or automatic bug detection.

## 0.29.0 — 2026-10-03

- Added a persisted observed-interaction graph. The simulation counts actual feeding, hunting, seed deposition, resource harvesting and disease transmission as named links. The browser shows the most frequent links and the server snapshot exposes the complete bounded graph. Save schema v29 migrates older worlds with an empty history.
- Link counts describe actions that occurred, not an emergent food web or beneficial adaptation; longer-run network reorganization remains an open research question.

## 0.28.0 — 2026-10-03

- Added persistent pairwise settlement relations. Successful barter improves relations; repeated food scarcity can trigger a route-bound raid by a different-culture town with at least two eligible residents. Raiders pay an immediate energy cost, and a successful arrival transfers food from the target instead of creating it. Hostility rises when a raid launches and can eventually prevent trade.
- The browser distinguishes raid parties from caravans, counts launched/successful raids, and shows each town's grievances and relations. Save schema v28 preserves relations, raid state and in-transit parties; older saves migrate with neutral relations. Three 500-tick seeds produced 2, 1 and 2 unforced raids. This is limited food conflict, not a full war or diplomacy system.

## 0.27.0 — 2026-10-03

- Added a plague power and local contact transmission after movement. Infection increases energy use, clears with time, and raises acquired immunity on recovery; children inherit bounded resistance with mutation. Healing cures infection, mutation can alter resistance, and the browser shows cases and individual health.
- Save schema v27 persists infection, resistance and case counts, with neutral defaults for older organisms. A forced-contact test verifies spread, complete resistance, recovery and deterministic continuation. Outbreaks currently need a plague intervention; the model does not claim calibrated epidemiology.

## 0.26.0 — 2026-10-03

- Surplus settlements can assign an inventor to try short sequences of handle, blade, temper and hone operations. Trials consume real wood and ore; operation order changes tool quality. Towns keep only improved designs, which modestly increase farming, logging and mining output. Existing food-for-material caravans also carry the source town's best design to a destination.
- Save schema v26 preserves design recipes, quality and trial counts; old towns start with no design. The browser reports design activity and shows each town's recipe, resources and reserves in the inspector. Three 500-tick seeds produced 17, 14 and 53 trials respectively, so the mechanic occurs without forced setup. This is one bounded compositional technology system, not open-ended invention.

## 0.25.0 — 2026-10-03

- Added a saved peer-learning switch and `--social-ablation` experiment mode. The switch isolates local human imitation from each organism's own online policy training; older saves retain the prior enabled behavior.
- Ten matched 500-tick worlds recorded 62 peer lessons when imitation was enabled. Compared with no imitation, mean differences were +0.1 living humans, −0.9 settlements, −1.542 human energy and −7.617 town food. These mixed outcomes do not establish a settlement benefit; the roadmap item remains open.

## 0.24.0 — 2026-10-03

- Settlements with residents, spare wood and a food surplus can build a communal granary. It transfers actual town food into a bounded reserve and releases it during shortages before households receive rations; empty towns lose stored food to spoilage. Migration now considers reserves when judging a food shortage.
- Save schema v24 preserves granaries and reserves; older towns migrate with neither. Browser statistics expose their count and stored food. A controlled shortage test verifies that a stocked granary feeds a resident after ordinary town stock is exhausted.

## 0.23.0 — 2026-10-03

- New worlds have finite subsurface ore reserves. Weathering and water erosion slowly transfer ore from a hidden vein into mineable surface stock; mining depletes the exposed stock. The tile inspector shows both pools, and the browser reports cumulative natural exposure. Save schema v23 migrates older worlds with no hidden reserve and preserves exact continuation.
- A separate ten-seed, 500-tick value-head ablation again failed to show a hunting gain over immediate-reward learning: mean paired difference −0.798 hunts per 1,000 predator-ticks (SE 0.440), with three positive seeds. This is a limited ecological measure, not proof that the value head harms every outcome; its roadmap acceptance item remains open.

## 0.22.0 — 2026-10-03

- Grazers and foraging humans now pick up a bounded, conserved share of local grass and tree seeds while eating and deposit carried seeds with their climate-trait means as they move or die on land. This gives animal travel a direct plant-colonization effect; a controlled transfer test confirms that deposited seeds can establish a cohort.
- Save schema v22 persists six seed-cargo values per organism and the cumulative seed-spread counter, migrates older organisms to empty cargo, and replays deterministic movement/deposition. The browser shows total deposited seed-bank units.

## 0.21.1 — 2026-10-03

- Added living trait dispersion and effective primary-parent lineage counts by organism kind to snapshots and the offline speciation report. Metrics use the bounded ancestry window and report untracked roots, so they describe variation without calling temporary mating components new species. A controlled six-generation contact test verifies that widely separated mate-recognition lineages remain incompatible under ordinary trait mutation; it does not establish spontaneous speciation in an open world.

## 0.21.0 — 2026-10-03

- Added saved water and soil-pool ledgers that separate precipitation, evaporation, ocean loss, seasonal exchange, plant/fire/grazing/death exchange and god interventions. In deterministic world runs with weather, ecology and destructive powers, the represented water and mineral-plus-litter pools close to floating-point precision. These are accounting ledgers for abstract stores, not calibrated physical mass budgets; biomass, organism and settlement nutrient stores remain outside the soil-pool ledger.
- Added opt-in predator prey-proximity movement credit and a matching experiment flag, with deterministic save migration and a direct movement-credit test. Ten matched 200-tick seeds showed no reliable gain over immediate-reward learning (mean +0.483 hunts per 1,000 predator-ticks, paired SE 1.163; five positive seeds), so ordinary worlds leave it disabled. The stronger trial reduced hunting, and neither trial established learned directional tracking or grazer threat avoidance.

## 0.20.1 — 2026-10-03

- Removed an artificial surface-water addition during river-channel refresh. Basin overflow now stays in lake storage when the surface pool is full, and local runoff transfers water from soil moisture rather than creating it.
- Added focused water-storage conservation and forced-contact reproductive-isolation tests. These verify local mechanics only; atmospheric inputs/evaporation, nutrient flows, persistent speciation and neural behavioral gains remain unvalidated.

## 0.20.0 — 2026-10-03

- Added Lake Country world creation, explicit freshwater storage in drainage basins, a rimmed inland-lake power, lake rendering and movement/ecology effects. Basin capacity refreshes with drainage; rain fills lakes and evaporation lowers them. Local runoff now respects water and nutrient receiving capacity.
- Raised bounded tree regrowth after disturbance. A controlled 5,000-tick single-site history now passes from burn scar through grassland to woodland; a two-trait climate-reversal experiment confirms that inherited plant temperature preference changes which cohort thrives.
- Added a value-learning ablation mode, predator prey-direction and grazer threat-direction probes, and an offline adult mating-compatibility graph. Ten short paired seeds found the original value-policy correction reduced hunting versus immediate-reward learning; a smaller correction narrowed that gap in the earlier ecology. After tree and lake changes the comparison was mixed across seeds. Behavioral gains and speciation claims remain open.

## 0.19.0 — 2026-10-02

- Added a bounded behavioral novelty archive. Every 100 ticks, each species can contribute one sufficiently observed organism whose seven-action frequency distribution differs from archived examples; the archive holds at most 64 records. Guided human migration does not count as a neural choice.
- The browser shows recent records and dominant-action diversity. Schema v19 persists per-organism action counts and the archive; older saves begin with empty histories. These descriptors measure distinct observed actions, not intelligence, beneficial adaptation or unexpected emergence.

## 0.18.0 — 2026-10-02

- Humans in the same settlement and culture can now weakly imitate a peer whose recent action reward is higher. Every society update selects one sufficiently trained mentor per local culture and blends 2% of that mentor's policy and value head into lower-scoring residents. Frozen worlds never share weights, and stale action-credit traces are cleared after imitation.
- Recent-reward estimates and social-learning counts persist in save schema v18; v17 saves initialize them to zero. The browser exposes peer lessons for individual humans and the whole world. This is a local adaptation mechanism, not evidence of beneficial cultural transmission or smarter societies.

## 0.17.0 — 2026-10-02

- Each organism now inherits a nine-parameter value head over its recurrent policy features and trains it online with bounded one-step temporal-difference error. A small future-value correction can train the preceding neural action; immediate reward-baseline training and predator hunt credit remain. Tiny corrections are filtered to limit CPU work.
- Value parameters, pending action credit and critic update counts persist in save schema v17. Older saves start with neutral value heads. Frozen-policy mode trains neither network, guided migration is excluded from policy credit, terminal deaths resolve pending credit, and the mutation power changes both neural components while clearing stale traces.
- Three short learned/frozen seed pairs did not establish improved predator tracking. The added training reduced measured one-worker throughput on the 250-organism workload; the result remains above the initial 8-tick/s target.

## 0.16.0 — 2026-10-02

- Added grassland, woodland and burn-scar map presets and god brushes. Biome labels now reflect plant cover and recent burning as well as climate.
- Fire and volcanic impacts leave bounded scars that fade faster in moist ground. Recovery temporarily favors pioneer grass over tree growth; forest and meadow powers speed restoration. Save schema v16 persists the scar field and migrates older saves to an unscarred baseline.
- The browser palette and tile inspector display the new landscapes and scar intensity. No calibrated fire ecology or long-run succession claim is made.

## 0.15.0 — 2026-10-02

- Hungry settlements with depleted local forage now send one able resident per society update toward a reachable settlement with food and housing. Migrants follow passable land routes, stop when a route floods or the destination disappears, and join a destination household after arrival.
- Migration plans persist in save schema v15 and resume deterministically. The browser shows active migrant counts, destinations and departure/arrival events. Guided travel is kept separate from neural training so its outcomes are not falsely credited to a policy choice.

## 0.14.2 — 2026-10-02

- Reduced Python generator overhead in the neural policy's hidden, action and gradient sums while preserving the same arithmetic order and save format.
- On a short seed-42, 1,000-organism CPU run, one-worker throughput rose from 18.95 to 20.92 ticks/s; 2,000-organism throughput reached 11.05 ticks/s. These are local measurements, not general scaling claims.

## 0.14.1 — 2026-10-02

- Sparse neural observations now skip zero-valued input connections during CPU inference and online updates. Direct bounds checks replace nested `min`/`max` calls in the hot weight-update loop.
- Added reference-equivalence tests for sparse/dense inference and learning. No save schema or policy dimensions changed.
- On the local 200-tick, 250-initial-organism workload, one-worker throughput improved from 31.69 to 35.07 ticks/s on the first repeat (34.19 on a second). All-affinity workers remained slower at this scale; worker selection stays configurable.

## 0.14.0 — 2026-10-02

- Added periodic lowest-spill drainage to ocean outlets and upstream flow accumulation across whole catchments. Channels receive water and slowly erode into sediment as rainfall and terrain change.
- Added a river-catchment map layer and visible channel tint. Save schema v14 persists channel strength; older saves initialize it to zero.
- The routing model has no explicit lake storage or calibrated water budget; it is a bounded world-scale drainage approximation.

## 0.13.0 — 2026-10-02

- Added a deterministic 8×8-tile cloud grid with periodic wind advection, ocean/land evaporation, elevation-sensitive rainfall and cloud-driven changes to soil moisture, surface water and fire.
- Added a cloud-front map layer and local cloud inspection. Fresh-world previews now include the exact starting weather grid.
- Save schema v13 persists cloud state; older saves initialize it from a separate seed stream without changing organism RNG. Weather remains a coarse local model, not a watershed or atmospheric solver.

## 0.12.0 — 2026-10-02

- Organisms now inherit and mutate a continuous mate-recognition signal. Two-parent reproduction requires signal and thermal compatibility; contact with incompatible adults blocks the solitary-birth fallback for that attempt.
- The server counts candidate mate encounters and incompatibility rejections. The browser shows signal diversity bins and the rejection fraction as mating isolation, without treating those bins as proven species.
- Save schema v12 migrates v1–v11 organisms with a neutral recognition signal and zero historical encounter counts. Mutation powers also alter the signal.

## 0.11.0 — 2026-10-02

- Added bounded mineral nutrients and organic litter to each tile. Plant growth draws down nutrients; litter from plant turnover, grazing and organism death decomposes back into available nutrients. Fire releases some ash minerals, while runoff transports dissolved nutrients downhill or out to water.
- Fertile-soil and biome powers now alter the nutrient state. The browser exposes nutrient and litter values and a soil-nutrients map layer.
- Save schema v11 initializes nutrient pools when loading older worlds. Preview and active-world tile data remain identical for the chosen seed.

## 0.10.0 — 2026-10-02

- Added `python3 -m wildseed.branch` to replay a trusted save into a separate branch, optionally apply one god intervention and advance a chosen number of ticks.
- Each branch records the parent and result hashes, seed, tick range, intervention effect and resulting metrics in an experiment manifest. Existing saves and manifests are protected from accidental overwrite.
- Documented causal comparisons and brought the README's feature inventory in line with the current implementation.
- Added a checksum-verified backup command for atomic saved worlds, with no-overwrite publication and deployment instructions for separate storage.

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
