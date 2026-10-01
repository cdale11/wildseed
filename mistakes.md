# Development mistakes

## 2026-10-02 — Rare seeds initially failed to establish plant cohorts
- Mistake: dispersal placed a small positive seed bank in bare land, but integer rounding made its target population zero on the next update.
- Cause: the cohort target used `int(capacity * seed * fitness)` without a minimum for viable seeds.
- Resolution: any positive seed can establish one founding plant; population growth still depends on climate fit and competition.
- Prevention: test colonization starting from both empty seed banks and zero plant counts, including sparse one-step transfers.
- Verification: focused dispersal and inherited-trait tests pass; water and destructive powers still clear cohorts.

## 2026-10-01 — Immediate reward obscured navigation learning
- Mistake: the initial policy update rewarded a successful eat action but gave no credit to the movement that put a predator on the prey tile.
- Cause: only the current action's immediate energy change was used as training reward.
- Resolution: successful hunts also update the preceding movement policy; added a frozen-policy control and a directional prey-cue probe.
- Prevention: measure the intended behavior against paired controls, including exposure-adjusted rates and held-out directional probes, before claiming adaptation.
- Verification: ten paired 500-tick seeds improved mean hunts per predator exposure by about 9%, but the directional probe remained near zero. Learned tracking is still unproven.

## 2026-10-01 — Browser permission troubleshooting was overconfident
- Mistake: repeated settings/restart suggestions did not resolve the original task's saved GitHub denial.
- Cause: inferring a fix without evidence about the persisted permission layer.
- Resolution: the user requested a fresh task; it opened GitHub successfully and created the repository after sign-in.
- Prevention: state uncertainty; report contradictions between visible settings and tool behavior; do not bypass a denial.
- Verification: fresh task confirmed public cdale11/wildseed created with README on main.

## 2026-10-01 — Test creation used a path relative to the wrong working directory
- Mistake: used outputs/wildseed/tests while already executing inside outputs/wildseed; test command discovered zero tests.
- Resolution: wrote tests/test_world.py from the repository root and reran discovery.
- Prevention: use explicit command working directories and check the discovered test count; zero tests is not a pass.
- Verification: eight meaningful simulation tests passed after correction.

## 2026-10-01 — Predators originally observed grass instead of prey
- Mistake: the initial shared observation vector exposed plant food to carnivores and no directional threat/material channels.
- Consequence: policies lacked the information needed to learn directed hunting or hazard avoidance.
- Resolution: species-specific food sensing and separate directional threat/material inputs, indexed before each tick.
- Prevention: test ecological meaning of observations, not only policy math and finite state.
- Verification: tests cover live/dead prey, wrapped sight lines, water occlusion and species-specific channels. Learned behavior remains to be evaluated.

## 2026-10-01 — God powers lacked truthful immediate feedback
- Mistake: the initial command API returned success for no-effect casts, and lowered water tiles retained vegetation until a later climate tick.
- Resolution: power results count actual changes, life casts target habitable cells only, and water clears incompatible vegetation/fire immediately.
- Prevention: test every catalog power for real state changes and explicit no-effect cases; verify browser casts against server snapshots.
- Verification: ocean brush changed exactly 29 cells through the UI, with immediate vegetation clearing; meteor removed six organisms and changed terrain. Unit coverage includes all 30 powers.
