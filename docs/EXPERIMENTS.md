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
