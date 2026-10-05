# Development mistakes

## 2026-10-05 — Schema bump initially omitted the prior save version
- Mistake: the first focused v29-to-v30 migration test failed because the accepted-version list included v28 and the new current version but skipped v29.
- Cause: the loader uses an explicit version tuple, and the schema bump changed `VERSION` before updating that tuple.
- Resolution: include v29 and verify v29 aid counters default to zero.
- Prevention: whenever bumping save schema, add the old current version to the loader's accepted-version list and run a prior-version fixture.

## 2026-10-05 — Emergency aid initially could not emerge in ordinary worlds
- Mistake: the first aid rule required 25 donor food and a positive trade relation; three 800-tick worlds had hungry towns but no relations or such surplus, so no aid was sent.
- Cause: thresholds were chosen from a controlled fixture instead of observed settlement food distributions.
- Resolution: permit same-culture aid, lower the donor threshold while retaining a food floor, and keep cross-culture aid dependent on trade trust.
- Prevention: run unforced seed-level simulations for a new emergence mechanic in addition to controlled unit tests.
- Verification: three unforced 800-tick worlds sent 6, 2 and 1 aid caravans, respectively.

## 2026-10-03 — Lake brush drained after the next watershed refresh
- Mistake: the first lake brush reported 29 changed tiles, but an inspected center tile had zero stored lake water 50 ticks later.
- Cause: the brush painted equal-elevation flooded tiles without a retaining rim, so lowest-spill routing reduced their basin capacity to zero.
- Resolution: carve a sloped depression with a raised rim; a controlled test and the exact browser seed retain lake water after 64 ticks and drainage refreshes.
- Prevention: test powers for persistence after the next relevant simulation phase, not only immediate effect counts.
- Verification: the same seed and coordinate retained 0.119 lake depth after 64 ticks; full tests include brush persistence.

## 2026-10-03 — Strong temporal-value correction hurt predator hunting
- Mistake: the initial value-policy correction was treated as a promising learning mechanism without a direct immediate-reward ablation.
- Cause: future-value estimates were applied to prior policy actions at rate 0.006 with a 0.05 threshold; a ten-seed comparison found lower exposure-adjusted hunts in nine pairs.
- Resolution: add a reproducible ablation mode and reduce the correction to rate 0.001 with a 0.10 threshold. The reduced setting remains below the immediate-reward control and is not claimed as a gain.
- Prevention: require a matched ablation and held-out behavioral probe before marking learning benefits complete.
- Verification: the documented ten-seed comparison and save-replay ablation test reproduce the negative finding.

## 2026-10-03 — Power test fixture left lake storage behind
- Mistake: the lake power caused subsequent power subtests to fail while spawning a creature at the fixed test coordinate.
- Cause: the fixture reset elevation and vegetation but not the new lake and capacity fields, so the coordinate remained uninhabitable.
- Resolution: reset both lake fields with the other tile fields before each power subtest.
- Prevention: when adding habitat state, update reusable fixtures to establish all passability preconditions explicitly.
- Verification: all power effect tests pass, including the lake power.

## 2026-10-02 — Neural-mutation test assumed a fixed tile was land
- Mistake: the new value-head mutation test dereferenced a failed organism spawn.
- Cause: its chosen seed placed the test coordinate underwater, and the fixture did not establish passable land first.
- Resolution: set the target tile to land before spawning and reran the focused tests.
- Prevention: make habitat preconditions explicit in organism tests rather than assuming a generated tile is land.
- Verification: value-learning and god-power tests pass, including mutation of both neural components.

## 2026-10-02 — Save schema bump exposed hardcoded migration-test versions
- Mistake: the first full-suite run after adding migration failed seven legacy-save tests, and an initial patch placed a food-capacity assertion inside the route-cancellation test.
- Cause: legacy tests asserted the previous current-version literal instead of `World.VERSION`; the test edit was inserted before the earlier test's final assertions.
- Resolution: current-version assertions now use `World.VERSION`, and the food-capacity assertions are back in their intended test.
- Prevention: search migration fixtures for hardcoded current-version assertions after each schema bump; inspect the surrounding test method before inserting cases.
- Verification: all 77 tests pass, including v14 migration and in-progress route replay.

## 2026-10-02 — New watershed module landed outside its package
- Mistake: the first patch created `watershed.py` at the repository root, so focused tests could not import `wildseed.watershed`.
- Cause: the new-file patch target did not land at the intended package path; I did not verify placement before the first test run.
- Resolution: moved the module into `wildseed/` and reran the routing tests.
- Prevention: check `rg --files` or `ls` for newly created modules before running tests and review untracked paths before commit.
- Verification: focused watershed tests and all 71 automated tests pass.

## 2026-10-02 — Nutrient fields initially broke preview and no-effect contracts
- Mistake: the first nutrient implementation added two fields to active snapshots but not world previews, and cleared stale underwater nutrient state during unrelated no-effect nature casts.
- Cause: schema and power changes were reviewed in isolation rather than against the exact-preview and truthful-effect contracts.
- Resolution: preview and live serialization now share `geography.client_tiles`; underwater nutrient clearing occurs when land is submerged or a terrain-changing power acts.
- Prevention: run setup-preview and no-effect power tests immediately after adding tile fields, before the full suite.
- Verification: both focused regressions and all 60 tests pass; browser JavaScript syntax checks pass.

## 2026-10-02 — Experiment guide replacement dropped prior results
- Mistake: an edit to document save branches initially replaced the existing paired-learning experiment guide and its published measurements.
- Cause: treating an existing documentation path as a new file without inspecting its contents first.
- Resolution: restored the original guide from the current commit and appended the branching section.
- Prevention: inspect a documentation file before editing it, and review the diff for removed evidence.
- Verification: `git diff` shows the historical result table retained alongside the new branch instructions.

## 2026-10-02 — Legacy-save tests initially used new policy shapes
- Mistake: several migration fixtures changed only the save version number while retaining the new 28-input neural weights.
- Cause: the fixtures had represented older tile schemas but did not also reconstruct the older policy layout.
- Resolution: fixtures now remove the eight recurrent input weights per hidden unit and the new memory field before loading.
- Prevention: migration tests must build the complete source-version schema, including network dimensions and pending training traces.
- Verification: all 50 tests pass, including version 1, 2, 6, 7 and 9 migration paths.

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
# 2026-10-03 — Catchment visualization created water
- Mistake: periodic river-channel refresh added surface water from a dimensionless catchment-strength estimate; local runoff also increased surface water without reducing soil moisture.
- Cause: visual hydrology and water storage were coupled without a transfer invariant.
- Resolution: channel strength now remains diagnostic, local runoff transfers from soil moisture, and basin overflow is retained when surface storage is full.
- Prevention: test the sum of represented water stores around each transfer, while keeping atmospheric fluxes explicit in future budget work.
- Verification: focused watershed and lake tests pass. A closed full-cycle water and nutrient budget is still open.
# 2026-10-03 — Strong navigation shaping failed its ablation
- Mistake: a larger predator/grazer movement reward was initially treated as a plausible default improvement before paired evaluation.
- Cause: a locally sensible cue can change encounter dynamics and reward behavior in ways the designer did not anticipate.
- Resolution: compared ten matched seeds at two strengths, removed the grazer term and kept the predator term opt-in after no reliable gain emerged.
- Prevention: keep experimental neural rewards behind a saved ablation flag and require exposure-adjusted outcomes plus held-out directional probes before enabling them by default.
- Verification: the weaker predator-only trial improved five of ten seeds, mean +0.483 hunts per 1,000 predator-ticks with paired SE 1.163; the directional probe shifted only +0.109 percentage points.
# 2026-10-03 — Longer hunt credit reinforced ineffective paths
- Mistake: a four-move discounted predator trace seemed likely to improve delayed hunt credit.
- Cause: successful hunts can follow incidental wandering, so reinforcing every recent movement can amplify irrelevant actions.
- Resolution: removed the trace after a ten-seed matched ablation showed lower exposure-adjusted hunting; retained the previous one-move credit.
- Prevention: evaluate delayed-credit schemes against the existing policy before adding permanent save state or declaring progress.
- Verification: ten 200-tick seeds averaged −1.579 hunts per 1,000 predator-ticks (paired SE 0.541); only one seed improved. The experimental code is not shipped.
# 2026-10-03 — Inventor test ignored scarcity-based job priorities
- Mistake: the first controlled tool test expected an inventor while the town still lacked wood, so the occupation model correctly assigned a woodcutter.
- Cause: the fixture met the bare experimentation threshold but not the larger resource-surplus threshold implied by job demand scores.
- Resolution: tested invention with an actual food, wood and ore surplus; retained scarcity-first job assignment.
- Prevention: exercise new occupations through the real assignment function with both scarce and surplus inventories.
- Verification: the corrected test assigns an inventor, consumes materials and records a trial; ordinary 500-tick worlds also perform experiments.
# 2026-10-03 — Current-version town normalization broke exact replay
- Mistake: the first v26 loader added tool fields to every town, including same-version saves made from sparse controlled fixtures.
- Cause: treating a migration default as an unconditional load normalization changed snapshot shape after reload.
- Resolution: add empty tool fields only while migrating pre-v26 towns; new game-founded towns carry the fields from creation, while current-version sparse fixtures retain their exact state.
- Prevention: version-gate new schema defaults and run save/continue comparisons with both ordinary and deliberately sparse settlement records.
- Verification: granary, migration and tool save/replay tests pass after the loader change.
# 2026-10-03 — Recasting plague could inflate incident cases
- Mistake: the first plague implementation incremented the cumulative case counter whenever an existing infection was strengthened.
- Cause: it treated every state change as a new transmission event.
- Resolution: count a new case only when the organism was previously uninfected; a recast can still restore infection intensity.
- Prevention: distinguish incidence from current prevalence in epidemiological counters and test repeated interventions.
- Verification: the focused plague test recasts on an ill organism without raising the case total.
# 2026-10-03 — First raid threshold never fired in ordinary worlds
- Mistake: the initial conflict rule required a town with more than twelve food units, but sampled 500-tick worlds rarely held that much after household rationing.
- Cause: thresholds were chosen from an imagined resource scale rather than observed settlement inventories.
- Resolution: set scarcity/abundance thresholds relative to population and lowered the minimum raiding party to two; theft is capped to half the target's current stock.
- Prevention: run a few natural seeded worlds before declaring a new settlement rule reachable, while retaining controlled tests for exact resource transfer.
- Verification: three 500-tick seeds produced two, one and two unforced raid launches; route, food conservation, relations and save replay have focused tests.
