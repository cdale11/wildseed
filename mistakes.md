# Development mistakes

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
