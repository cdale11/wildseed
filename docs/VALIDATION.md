# Validation — 2026-10-03

## Version 0.20.0 lakes and Phase 1 controls — 2026-10-03

The 108-test suite covers basin storage, a lake brush surviving drainage refresh, immediate ocean cleanup, passability, save v19→v20 migration and deterministic continuation, receiving-capacity conservation for local water/nutrient transport, a 5,000-tick controlled burn-scar → grassland → woodland sequence, a two-trait climate reversal, immediate-reward value-head ablation and an exact adult mate-compatibility graph. Browser modules pass Node syntax checks. In a temporary browser session, Lake Country was selectable and rendered inland water; the lake brush reported 29 changed tiles. The browser also exposed a defect: the first brush design drained after a watershed refresh. After the rim fix, replaying that browser seed and cast coordinate retained 0.119 lake depth after 64 ticks. The temporary browser tab and server were closed.

A seed-42, 96×64, 250-starting-organism, 200-tick one-worker CPU run reached 33.09 ticks/s with 692 final organisms. Ten 200-tick paired value-head ablations were negative on the earlier ecology; after the tree and lake changes, the value mode gained in five of ten seeds with a small, uncertain mean difference. Synthetic prey and threat probes remained near zero; details are in [EXPERIMENTS.md](EXPERIMENTS.md). The watershed/weather/nutrient pools are bounded and locally audited, not physically calibrated or globally mass-conserving. The mating graph identifies candidate isolated groups, not validated speciation. No GPU or multi-seed 100k-tick stability study was performed.

## Version 0.19.0 observed behavior archive — 2026-10-02

All 96 automated tests pass, including guided-move exclusion, distinct-versus-duplicate archive admission, minimum observations, action recording, v18 migration and exact save continuation. Browser JavaScript passes syntax check. A temporary local browser session displayed recent archive records, 15 accumulated records and seven action modes; its console had no errors. The tab and server were closed afterward. A seed-42, 96×64, 250-starting-organism, 200-tick one-worker run produced six records, seven action modes across 584 eligible living organisms, and 23.34 ticks/s (669 final organisms). The benchmark overlapped automated tests and is only a throughput sanity check. Action-frequency distance does not establish that behaviors are useful, surprising or learned.

## Version 0.18.0 local human peer learning — 2026-10-02

All 92 automated tests pass, including settlement-triggered peer learning, same-culture and reward-gap gates, frozen worlds, save continuation and v17 migration. Browser JavaScript passes syntax check; the new lesson counters were not visually inspected in a browser. In a seed-42, 96×64, 250-starting-organism, 200-tick one-worker CPU run, 17 peer lessons occurred among 95 surviving humans and 47 settlements. The run reached 26.94 ticks/s with 669 final organisms, above the 8-tick/s target; this is a short sanity check, not a social-benefit or stability study. No controlled no-imitation comparison has established better settlement outcomes or retained policy diversity.

## Version 0.17.0 online value learning — 2026-10-02

All 88 automated tests pass, including bounded positive/negative value learning, policy response to a learned successor value, terminal credit, neutral v16→v17 migration, exact save continuation with pending credit, frozen controls and mutation of both neural components. Browser JavaScript passes syntax check. In a temporary local browser world, the Value updates counter rose to 7,976 by age 33, while Learning steps reached 8,970; the browser tab and server were closed afterward. A seed-42, 96×64, 250-initial-organism, 200-tick one-worker CPU run measured 27.50 ticks/s (690 final organisms), versus 34.97 ticks/s (670 final organisms) before the value head; changing learning also changes the population trajectory, so this is a throughput sanity check rather than an isolated speed comparison. Three short paired learned/frozen ecology runs were mixed; see [EXPERIMENTS.md](EXPERIMENTS.md). No GPU or long stability validation was performed.

## Version 0.16.0 disturbance-driven biome succession — 2026-10-02

All 81 automated tests pass, including scar effects on grass/tree growth, fire-to-recovery biome transitions, active lava retaining its volcanic label, exact previews for three new presets, all 33 god powers changing authoritative state, v15→v16 save migration and deterministic continuation. Browser modules pass Node syntax checks. In a temporary local browser session, Burn scar appeared in world setup with a rendered brown/ash preview; creating that exact world exposed Grassland, Woodland and Burn scar brushes, and a Woodland cast reported 29 changed tiles. The test server was shut down afterward. A seed-42, 96×64, 250-initial-organism, 200-tick one-worker CPU run measured 34.97 ticks/s (670 final organisms); changed ecology alters the trajectory, so this is a sanity check rather than a controlled throughput comparison. The scar is a bounded, phenomenological disturbance memory: it temporarily shifts plant growth and fades with local moisture. It is not a calibrated fire ecology model.

## Version 0.15.0 directed human migration — 2026-10-02

All 77 automated tests pass, including deterministic save continuation during travel, arrival and household reassignment, blocked water routes, lack of destination food, flooding or destination loss during travel, and v14 save migration. Browser JavaScript passes syntax check. The feature sends at most one migrant per hungry town every 20 ticks, along a land route of at most 24 steps; a destination needs available housing and a food reserve. The choice is an explicit social rule, separate from the organism's adaptive neural policy. Tests establish these local mechanics, not that civilizations remain viable over long periods.

## Version 0.14.2 neural loop profiling — 2026-10-02

All 73 tests pass, including sparse/dense neural reference equivalence, deterministic replay and loopback HTTP. The policy dimensions and save schema remain unchanged. A 30-tick `cProfile` run with 1,000 starting organisms attributed about 1.24 s to inference, 0.97 s to training, 0.71 s to climate and 0.63 s to observation within 3.83 s total, indicating neural work is still the largest cost. Explicit accumulation loops remove generator setup in hidden, action and backward sums while retaining arithmetic order.

On this shared Linux host (Python 3.13.11, 16 affinity CPUs), seed-42 96×64 full-tick measurements were:

| Initial organisms | Ticks | Workers | Before | After | Final organisms |
|---:|---:|---:|---:|---:|---:|
| 250 | 200 | 1 | 34.19–35.07 ticks/s (prior runs) | 34.84 ticks/s | 666 |
| 1,000 | 50 | 1 | 18.95 ticks/s (same-turn run) | 20.92 ticks/s | 1,023 |
| 1,000 | 50 | 16 | 18.05 ticks/s (prior run) | 17.03 ticks/s | 1,023 |
| 2,000 | 30 | 1 | 9.99 ticks/s (prior run) | 11.05 ticks/s | 1,841 |

These short sequential runs have no confidence intervals. The all-affinity result shows that inference parallelism can cost more than it saves at this size; worker selection stays configurable. Broader scaling, GPU validation and long stability studies remain open or deferred.

## Version 0.14.1 sparse CPU neural updates — 2026-10-02

All 73 automated tests pass, including dense/sparse forward and update comparisons against the previous calculation to 12 decimal places, saturated weight bounds, scalar/process inference agreement, deterministic replay and loopback HTTP checks. Save schema remains v14. On this Linux host with Python 3.13.11 and 16 affinity CPUs, seed-42 full-tick runs ended with identical populations within each compared workload:

| Workload | CPU workers | Before | After | Final population |
|---|---:|---:|---:|---:|
| 96×64, 250 start, 200 ticks | 1 | 31.69 ticks/s | 35.07 ticks/s; 34.19 repeat | 666 |
| 96×64, 250 start, 200 ticks | 16 | 28.75 ticks/s | 29.98 ticks/s | 666 |
| 96×64, 1,000 start, 50 ticks | 1 | — | 18.88 ticks/s | 1,023 |
| 96×64, 1,000 start, 50 ticks | 16 | — | 18.05 ticks/s | 1,023 |
| 96×64, 2,000 start, 30 ticks | 1 | — | 9.99 ticks/s | 1,841 |
| 96×64, 2,000 start, 30 ticks | 16 | — | 10.02 ticks/s | 1,841 |

These are sequential short runs on a shared host, not confidence intervals or long-run scaling curves. The all-CPU configuration remains available but is slower at small population sizes here; there is no evidence to hardcode a worker cutoff for other hardware. GPU validation remains deferred at the owner's request.

## Version 0.14.0 catchment routing — 2026-10-02

All 71 automated tests pass, including deterministic lowest-spill routing down a constructed valley to a periodic ocean outlet, upstream accumulation, visible channel water and sediment-producing erosion, no false river in an all-land world, v13→v14 migration and exact save continuation. Browser JavaScript modules pass syntax checks. The 200-tick, 250-initial-organism, one-worker CPU benchmark reached 31.91 ticks/s (median 30.68 ms, p95 46.26 ms; 666 final organisms). The drainage network updates every 32 ticks, so the median alone understates periodic work; this short run is not a high-population scaling result. For seed 42 at 96×64 with no organisms, after the first 32-tick drainage update, the model produced 254/492/41 land tiles with channel strength above .03 in continents/riverlands/archipelago respectively. This checks that generated maps, not only a constructed valley, show channels. The model has no explicit lake storage or calibrated conservation of catchment water.

## Version 0.13.0 cloud fronts — 2026-10-02

All 67 automated tests pass, including periodic cloud advection, more rain on uplands than lowlands under an equal front, exact preview/weather match, v12→v13 migration and deterministic save continuation. Browser JavaScript modules pass syntax checks. The 200-tick, 250-initial-organism, one-worker CPU benchmark reached 33.07 ticks/s (median 29.28 ms, p95 44.85 ms; 669 final organisms). The changed weather rules alter the ecological trajectory, so this is not a controlled throughput comparison with v0.12. The model is an 8×8-tile cloud grid with bounded local effects; it has no pressure physics, watershed accounting or validated climatology.

## Version 0.12.0 reproductive divergence — 2026-10-02

All 63 automated tests pass, including forced incompatible adults sharing a tile (no birth and counted rejections), compatible two-parent inheritance, direct-mate validation, v11→v12 save migration and deterministic continuation. Browser JavaScript passes syntax checks. A seed-42, 96×64, 250-initial-organism, 200-tick, one-worker CPU benchmark reached 32.90 ticks/s (median 29.67 ms, p95 46.35 ms; 648 final organisms). The changed reproduction rules alter the population trajectory, so this is not a direct speed comparison with v0.11.

In three 48×32, 80-initial-organism, 300-tick seed runs (40/41/42), the server counted 6/2/5 rejected candidate encounters out of 10/12/6, with 4/10/1 two-parent births. These small counts show the barrier operates in ordinary simulations but cannot establish persistent speciation, population stability or selection benefit. Mate-signal bins are a diversity proxy, not species assignments.

## Version 0.11.0 nutrient recycling — 2026-10-02

All 60 automated tests pass with loopback socket access. Focused tests show nutrient-rich plant cohorts grow faster than otherwise identical nutrient-poor cohorts, litter decomposes into mineral nutrients, runoff transfers dissolved nutrients downhill without changing the two-tile total, and v10 saves migrate to v11 with deterministic continuation. Exact startup previews still match the created world; no-effect powers on submerged tiles still report zero. Browser JavaScript modules pass syntax checks.

A 200-tick, 250-initial-organism, one-worker CPU run on Python 3.13.11 reached 31.46 ticks/s (median 30.42 ms, p95 47.51 ms; 697 final organisms). Different nutrient rules alter the population trajectory, so this is not a controlled speed comparison to v0.10. The pools are bounded and phenomenological; watershed weather and a calibrated mass-conserving nutrient budget remain open.

## Version 0.10.0 save branches and current CPU scaling — 2026-10-02

All 56 automated tests pass, including source-preserving deterministic branches, different outcomes after a measured rain cast, manifest hashes, backup checksum verification and refusal to overwrite existing outputs. A current seed-42, 96×64, 250-initial-organism, 200-tick benchmark ended with 728 organisms in every worker configuration:

| CPU workers | Median tick | p95 tick | Throughput |
|---|---:|---:|---:|
| 1 | 35.09 ms | 52.44 ms | 29.27 ticks/s |
| 2 | 34.96 ms | 54.57 ms | 27.60 ticks/s |
| 4 | 35.52 ms | 53.29 ms | 28.54 ticks/s |
| 16 (all affinity CPUs) | 35.98 ms | 55.09 ms | 27.32 ticks/s |

These are sequential short runs on a shared Linux host, so small differences may be noise. They show no benefit from extra inference processes at this scale; the current automatic 16-worker option remains available, while a one-worker setting is preferable for this measured workload. A 60-tick cProfile run attributed about 1.62 s of 4.26 s world-step time to serial neural learning, 1.28 s to climate updates and 0.80 s to inference. This identifies optimization targets but does not establish high-population CPU scaling.

## Version 0.9.0 transport limits — 2026-10-02

All 52 automated tests pass. A real loopback HTTP test holds one connection open and confirms a second receives 503 at a one-connection cap; another checks spectator read access, denied mutations/metrics, administrator metrics and 429 rate limiting. The 200-request loopback load run at concurrency 32 with a 16-connection cap returned 120 successful responses and 80 rate-limited responses, median 158.89 ms, p95 218.38 ms, throughput 245.43 requests/s. It exercises transport and snapshot serialization for a 32×24, 80-organism world; it is not a production internet or multi-client scale result.

## Version 0.8.0 recurrent inference — 2026-10-02

All 50 automated tests pass, including policy migration from version 1 and version 9, zeroed new recurrent connections, pending movement-credit migration, memory persistence, deterministic continuation and scalar/process inference agreement. A 200-tick, 250-initial-organism, one-worker run reached 29.14 ticks/s (median 33.77 ms, p95 52.33 ms; 728 final organisms). This is slower than the prior 20-input policy but remains above the 8-tick target for this short workload.

A three-seed, 300-tick paired probe averaged 14.96 hunts per 1,000 predator-ticks with learning versus 13.02 frozen. Directional prey-cue scores averaged 0.119 and 0.140 percentage points respectively. This small study does not demonstrate improved directional tracking from memory, and cannot be compared directly with the previous 20-input 500-tick experiment. Long-horizon recurrent credit remains open.

## Version 0.7.0 barter and settlement decay — 2026-10-02

All 47 automated tests pass. Focused tests verify food and ore are deducted when a caravan leaves, delivered to the opposite towns at arrival, and never transported through a fully blocking water barrier. An empty town loses its houses and generates an abandonment event. A 200-tick, 250-initial-organism, one-worker benchmark reached 35.31 ticks/s on a repeat run (median 27.39 ms, p95 43.53 ms; 675 final organisms). The first run was slower at 28.01 ticks/s, so this short benchmark is sensitive to system load. No sustained-town result or large-world route scalability is claimed.

## Version 0.6.0 first society layer — 2026-10-02

All 43 automated tests pass. Focused tests verify founding a town from gathered wood, assigning a human to a household, household food rationing, farming work changing stock, traffic building a road, and version 7 save migration. Browser JavaScript modules pass syntax checks. The 200-tick, 250-initial-organism, one-worker benchmark reached 36.69 ticks/s (median 25.08 ms, p95 41.82 ms; 675 final organisms). This is not evidence of sustained towns or inter-settlement economies; those remain roadmap tasks.

## Version 0.5.0 evolving terrain, plants and ancestry — 2026-10-02

All 40 automated tests pass on Python 3.13.11, including exact preview/new-world tiles, v1–v6 save migration, water/sediment transfer, lava spread/cooling, plant trait fitness and colonization, two-parent births, thermal adaptation and deterministic save continuation. Browser JavaScript modules pass Node syntax checks. Visual inspection of the updated renderer has not yet been completed.

The 200-tick, 250-initial-organism, one-worker benchmark on the same local Linux environment reached 37.15 ticks/s (median 26.50 ms, p95 40.72 ms; 683 final organisms). This workload remains above the 8-tick target at this population, but it does not establish performance near the 2,500 cap or ecological stability. The new hydrology is local tile flow with bounded transfer, not a watershed solver. Plant genomes are cohort-level trait means, and ecotypes are coarse trait bins, not independently evolved species.

## Version 0.4.0 learning controls

The paired experiment command and limitations are in [EXPERIMENTS.md](EXPERIMENTS.md). Ten seeds × two modes × 500 ticks completed on CPU. Frozen runs were reproducible, with zero within-lifetime updates; learned worlds retained exact save/resume behavior, including pending one-step hunt credit. The normalized hunt-rate gain was modest and directional tracking remains unproven. Unit tests include forced successful predation to verify the preceding move receives a neural update. All 30 automated tests pass, including a subprocess SIGTERM shutdown that persists an advancing world. The 200-tick, 250-initial-organism, one-worker benchmark reached 39.14 ticks/s (median 23.94 ms, p95 43.04 ms; 725 final organisms). This is a short run and not a high-population scaling claim.

## Version 0.3.1 seed ecology

All 25 automated tests pass on Python 3.13.11, including version 3 save migration and seed dispersal into bare land while keeping water sterile. Seed banks are included in deterministic save continuation and power state checks. With seed 42, 250 initial organisms, 200 ticks and one worker, the run ended with 730 organisms; median tick 23.92 ms, p95 40.18 ms, throughput 41.2 ticks/s. This short run does not establish ecological stability or plant species evolution. No game server remains running after verification.

Environment: Linux, Python 3.13.11, process affinity exposing 16 CPUs; no /dev/dri GPU device or PyTorch installed.

## Full-tick benchmarks

Seed 42, 96×64, 250 initial organisms, 200 ticks, 1,025 final organisms in both runs. Includes inference, online training and world rules; excludes HTTP snapshots/rendering. These are short-run measurements, not ecological stability results.

| CPU workers | Median tick | p95 tick | Throughput |
|---|---:|---:|---:|
| 1 | 13.14 ms | 27.46 ms | 65.57 ticks/s |
| 16 | 15.87 ms | 36.98 ms | 50.53 ticks/s |

Both exceed the initial 8 Hz target on this workload. All-CPU inference is slower here because IPC overhead and serial training dominate. Do not infer linear scaling; use --workers 1 for these small worlds. Vectorized learning and region work are planned before larger scale claims.

## Automated checks

Simulation tests cover deterministic replay, exact save/resume including policies/RNG, rewarded-action learning, mutated inheritance, finite/bounded state over 100 ticks, water spawn/fire-rain behavior, command validation and scalar/multiprocess inference agreement. HTTP integration tests cover bearer authorization, static path allowlisting, cross-origin rejection, pause and save.

## Browser/API checks

Opened the live browser client, observed connected statistics/terrain/settlements, paused via UI and confirmed the server paused, saved through the UI and observed the success notice. Direct API checks verified valid speed/save responses, invalid coordinates (400) and cross-origin command rejection (403). Screenshot delivered separately as wildseed-preview.jpg.

## Not validated

CUDA hardware/backend parity, Docker build/startup, long-term ecological diversity, large client concurrency, production reverse proxy, remote server deployment and mobile touch on physical devices. Browser rendering is a prototype and uses fixed policy actions; sophisticated societies remain roadmap work.

## Version 0.2.0 perception validation

All 14 tests pass, including new prey/threat/material sensing, dead-prey exclusion, periodic seam/occlusion and v1 save migration tests. HTTP tests initially could not bind sockets under the sandbox; they passed after network permission was granted.

Seed 42, one worker, 250 starting organisms:

| Run | Final population | Median tick | p95 tick | Throughput |
|---|---:|---:|---:|---:|
| 200 ticks | 985 | 21.46 ms | 48.24 ms | 41.22 ticks/s |
| 1,000 ticks | 2,498 | 178.87 ms | 220.37 ms | 6.98 ticks/s |

The short run overlapped the longer benchmark, so timings are indicative rather than an isolated apples-to-apples comparison with 0.1.0. At nearly the 2,500 population cap, this single-worker run misses the 8 Hz target. Optimization of training/perception and population-scale profiling remains necessary. Population survival alone does not demonstrate stable diversity or improved hunting; species-level and frozen-policy experiments are still outstanding. No browser assets changed in this version.

## Version 0.3.0 world creation and powers

23 automated tests pass. Coverage includes all 30 catalog powers producing actual state changes under suitable conditions, no-effect feedback for water/population caps, brush boundaries, rain/fire, immediate water cleanup, temperature-dependent growth, version 1/2 migration, random preview uniqueness, exact preview/create agreement, stale replacement protection, and archiving existing saves. All 72 geography/climate combinations were checked at seed 123 for valid bounded fields and land; this is not exhaustive seed testing.

Browser verification: selected Archipelago/Rainforest, created preview seed 479790552, paused the live world and cast Ocean at (48,32). A before/after server comparison confirmed exactly 29 changed tiles and immediate grass/tree removal. Mountain restored elevation; Meteor then altered terrain and killed six organisms. Browser console showed no errors. Desktop and narrow setup layouts were inspected; screenshots are provided with the deliverables. A subsequent browser refresh check was interrupted when the preview process received SIGTERM; server restart was independently confirmed to return setup_required=true despite an existing save. Browser refresh/rejoin is implemented but that final UI rejoin check was not completed.

CPU benchmark: seed 42, 250 starting organisms, 200 ticks, one worker; 919 final organisms; median 23.37 ms, p95 48.78 ms, 39.16 ticks/sec. Changed generation means this is a new workload, not a controlled comparison to prior versions. Full geography/climate stability, fluid rivers/lava and network topology evolution are not claimed. CI now targets Python 3.11 and 3.13; local tests ran on 3.13.11.
