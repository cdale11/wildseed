# Validation — 2026-10-01

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
