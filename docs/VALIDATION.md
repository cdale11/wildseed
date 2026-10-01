# Validation — 2026-10-01

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
