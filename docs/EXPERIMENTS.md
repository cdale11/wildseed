# Learning experiments

Run paired ecology worlds from the repository root:

```sh
python3 -m wildseed.experiment --seeds 40,41,42,43,44,45,46,47,48,49 --ticks 500 --population 80 --width 48 --height 32 --cap 500 --interval 100 > experiment.json
```

Each pair has the same initial world, organisms, weights and RNG seed. The frozen control still samples actions and inherits mutated weights; it disables only within-lifetime gradient updates. Runs use one CPU worker and no scripted organism replenishment. The JSON contains species counts, biomass, births, deaths, hunts, predator exposure and training steps at 100-tick intervals.

The directional probe asks each surviving predator policy how much more likely it is to move toward a food signal from each of four directions than toward the other three directions. Scores are percentage points; zero means no directional preference. This is a synthetic policy probe, not a replay of observed paths.

## Ten-seed result, version 0.4.0

| Mode | Mean hunts per 1,000 predator-ticks | Mean raw hunts | Mean directional probe |
|---|---:|---:|---:|
| Frozen | 13.06 | 129.4 | -0.010 pp |
| Learning with one-step hunt credit | 14.24 | 162.0 | 0.004 pp |

The exposure-adjusted hunt rate improved in seven of ten paired seeds. The mean improvement was 1.18 hunts per 1,000 predator-ticks (about 9%). The directional probe stayed near zero and varied in sign by seed. This does **not** demonstrate learned tracking or threat avoidance. More hunts can come from population composition, stochastic encounters or policies that favor eating after arrival. A longer controlled experiment with movement trajectories and held-out prey layouts is needed.

In the first uncorrected learning rule, the same ten seeds averaged 14.41 hunts per 1,000 predator-ticks, but the directional probe averaged -0.112 pp. Adding one-step hunt credit changed the trajectories and improved the probe mean toward zero, yet did not establish directional behavior. This is a short 500-tick experiment; neither treatment proves ecological stability at 100,000 ticks.

## Short value-head check, version 0.17.0

Each organism now trains a bounded value head from one-step temporal-difference error. The experiment JSON also reports `critic_updates`. Three paired seed-42/43/44 runs used 200 ticks, 80 starting organisms, a 48×32 map and a 500-organism cap:

| Seed | Frozen hunts / 1,000 predator-ticks | Learned hunts / 1,000 predator-ticks | Value updates |
|---:|---:|---:|---:|
| 42 | 8.350 | 9.289 | 24,933 |
| 43 | 11.321 | 11.126 | 28,257 |
| 44 | 8.615 | 7.175 | 24,648 |

These results are mixed and do not show that the new value head improves tracking. The learned/frozen comparison tests the whole learning system, not the marginal value-head effect; a matched immediate-reward ablation and held-out navigation tasks remain open. Value learning provides a mechanism for future reward estimates to influence an earlier policy action without claiming validated long-horizon planning.

## Save-based causal branches

Use a trusted local save as a fixed starting point. Each command creates a new world save and a neighboring `.experiment.json` manifest; existing outputs are never replaced.

```sh
python3 -m wildseed.branch data/world.json data/control.json --ticks 100
python3 -m wildseed.branch data/world.json data/rain.json --ticks 100 --tool rain --x 24 --y 20 --radius 4 --strength 2
```

Both runs start from the same saved RNG and neural state. The intervention occurs before the first advanced tick. Each manifest records the parent/result SHA-256 hashes, seed, tick interval, immediate power effect and resulting summary metrics. Compare the branch saves and replicate across seeds before drawing causal conclusions; a single difference does not identify its mechanism.

Exact replay also requires the same code revision, Python version and CPU backend. `World.load` accepts only trusted saves. Keep generated saves and manifests outside version control.

## Reproductive-divergence measurements

The active world reports `mate_encounters` and `mate_rejections` in snapshot statistics. An encounter is a directed reproduction attempt with another same-kind, mature, sufficiently energetic adult on the same tile; a rejection means the adult's inherited recognition signal or thermal preference is outside the compatibility threshold. The browser shows rejections divided by encounters as *mating isolation*. This is an interaction-weighted metric, not the fraction of all possible pairs in the world. `mate_types` counts coarse recognition-signal bins and does not identify biological species. A claim of speciation needs persistent multi-generation clusters, low gene flow between them and replicated seed-level evidence; that evaluation remains open.
