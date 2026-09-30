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
