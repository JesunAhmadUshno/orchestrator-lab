# Research review: orchestrator-lab

Date: 2026-11-07. Scope: the three levels as committed, plus the
changes made on the `site/live-dashboard` branch. This review grades
the repo against a PhD-level research rubric. Grades run from 0 to 10.
Each gap is either fixed in this change (with the file that fixes it)
or names the exact compute or data it still needs.

Short verdict: the engineering is careful and fully reproducible, but
the research claim is narrow by construction. The headline (routed 35
cost units against 45 for all_large at 9 of 9 quality passes) is a
property of a hand-set quality table and one designed scenario. This
change measures how fragile that result is to its own assumptions; it
cannot make it a claim about real models.

## Rubric

| Criterion | Grade | Status |
| --- | --- | --- |
| Research question | 7 | Clear, narrow |
| Hypotheses | 5 | Implicit, now partly testable |
| Method | 7 | Sound, deterministic, toy workers |
| Baselines | 7 | all_small and all_large; no external baseline |
| Statistics and uncertainty | 5 | Exhaustive enumeration replaces sampling on the toy model; no real uncertainty yet |
| Reproducibility | 9 | Byte-identical results, CI now runs every test, browser port checked |
| Threats to validity | 7 | Written per level, now quantified for estimation error |
| Related work | 2 | Not surveyed |
| Limitations | 8 | Honest and specific |

## 1. Research question (7)

Implicit question: does routing each task to a cheap or expensive tier
by estimated difficulty, with one escalation on a failed quality
check, keep quality at lower cost than always using the expensive
tier, and how do approval gates interact with a task graph?

- Strength: concrete, operational, and answered with recorded numbers.
- Gap: the question is never stated as a question in SPEC.md, and its
  answer depends entirely on the quality table. Not fixed by code;
  this review states it above. No compute needed.

## 2. Hypotheses (5)

- Gap: no pre-stated hypothesis or falsification rule existed. The
  Deep README asserted, without measuring, that more estimation error
  pushes routed cost "toward, or past" all_large.
- Fixed in this change: that statement is now a tested hypothesis.
  `level-3-deep/sweep_deep.py` enumerates all 512 subsets of
  underestimated executed tasks. Result: at small cost 2 and large
  cost 5 the hypothesis is false for this scenario (worst case 43
  against 45, because the 4 easy tasks still save 3 units each); at
  large cost 4 it holds from 4 underestimated tasks. At a quality
  threshold of 0.95, routed costs 50, more than all_large at 45.
  Recorded in `level-3-deep/results_sweep.json`, tested in
  `tests/test_sweep_deep.py`.
- Remaining: hypotheses about real models (for example "routing keeps
  pass rate within 2 points of all_large at under 80% of its cost")
  need real model workers and a measured quality signal (see 5).

## 3. Method (7)

- Strength: supervisor, waves, approval gates, transitive blocking and
  per-attempt accounting are real code with 75 unit tests (65 before
  this change). No randomness or wall-clock value enters any record.
- Gap: workers are toy functions and quality is a fixed table by true
  difficulty. Needs: two real model tiers (a small and a large open
  model served locally, for example on the assigned BlackBoxV2 node),
  a task set with gold answers, and a checker. Estimated cost: one GPU
  node for a few hours per 1,000 tasks; no paid API is required.
- Gap: Deep runs sequentially, so routing under the Build thread pool
  is not shown. Needs engineering only (the v1.1 "parallel routed
  execution" item); it was not done here because it changes the
  supervisor's core loop and its determinism guarantees, which is
  beyond a cheap upgrade.
- Fixed: the routing cutoff was hardcoded; it is now a parameter
  (default 2, results unchanged, sha256 399d9c659dd12825) so its
  sensitivity can be measured.

## 4. Baselines (7)

- Strength: all_small and all_large bracket the routed strategy on the
  same graph and the same simulated approver.
- Gap: no oracle baseline. Fixed: the sweep's k = 0 row is the oracle
  router (perfect estimates), 33 cost units, so the designed D07
  underestimate costs 2 units over the oracle.
- Remaining: no comparison with a published cascade or learned router.
  Needs real model workers (see 3) and the related-work pass (see 8).

## 5. Statistics and uncertainty (5)

- The system is deterministic, so there is no sampling noise to put an
  interval on. The honest substitute on a toy model is exhaustive
  enumeration, which this change adds: each k reports the minimum,
  mean and maximum routed cost over every subset, not one draw.
- Remaining: real uncertainty comes from real model outputs and real
  estimation error. Needs a labelled task set (several hundred tasks
  with gold difficulty and gold answers) and repeated runs per tier,
  then bootstrap intervals on cost and pass rate per strategy.

## 6. Reproducibility (9)

- Strength: every results file is byte-identical across runs; sha256
  prefixes are recorded in the README.
- Gap: CI ran only the scaffold smoke test. Fixed: `.github/workflows/ci.yml`
  now runs `python -m unittest discover -s tests` on every push.
- Gap: the Deep scenario lived only in code. Fixed: `run_deep.py` now
  writes `level-3-deep/scenario_deep.json`.
- Added: the live dashboard's build (`site/src/router.check.mjs`)
  fails if the browser port of the supervisor disagrees with
  `results_deep.json` (all three strategies, every record and trace
  entry) or with `results_sweep.json`, and it checks the results
  files' sha256 against the README record.
- Remaining: the runs were on a CPU VM, not the assigned fleet node.
  Needs one rerun on BlackBoxV2 (seconds of CPU).

## 7. Threats to validity (7)

- Internal: the single escalation is designed (D07). Now quantified by
  the estimation-error sweep instead of asserted.
- Construct: "quality" is a table lookup, "cost" a unit count. No fix
  without real models and a cost model (tokens or dollars per call).
- External: one designed 11-task graph. Needs a generator of random
  task graphs with difficulty distributions, which is engineering only
  and cheap, but it is a design decision about which distributions are
  realistic; without real difficulty data any chosen distribution would
  be another assumption, so it is left for the real-model study.
- The no-second-escalation path (large tier also failing) was untested.
  Fixed: two unit tests in `tests/test_sweep_deep.py` and the threshold
  sweep, where at 0.90 and above the large tier fails at difficulty 5.

## 8. Related work (2)

- Gap: NOVELTY.md said "NO MEASUREMENT YET" and DOSSIER.md Past has no
  dated sources. Partly fixed: NOVELTY.md now states the measured
  comparison and that the novelty is small (a clean deterministic
  reproduction of cost and quality cascade routing with approval
  gates), per its own honest-size rule.
- Remaining: a literature pass on model cascades and LLM routers with
  every source read and verified before it is cited. No compute is
  needed, only reading time and network access to the sources; no
  citation was added in this change because none could be verified
  here, and an unverified citation would be worse than none.

## 9. Limitations (8)

- Strength: each level README lists specific failure modes and the
  grade deductions they cost. The live dashboard quotes them verbatim
  at build time, so the page cannot drift from the README.
- Updated: the Deep README limit on estimation error now carries the
  measured sweep result.
- Remaining limits that need resources: real models (GPU node), a real
  human approval surface with persistence (engineering), latency and
  dollar cost (real model calls).

## What changed in this branch

- `.github/workflows/ci.yml`: the full unit test suite runs on push.
- `level-3-deep/orchestrator_deep.py`: routing cutoff parameter, default unchanged.
- `level-3-deep/run_deep.py`, `scenario_deep.json`: scenario exported as data.
- `level-3-deep/sweep_deep.py`, `results_sweep.json`: estimation-error, threshold, cost and cutoff sweeps.
- `tests/test_sweep_deep.py`: 10 new tests (75 in total).
- `NOVELTY.md`, `level-3-deep/README.md`: measured, honest updates.
- `site/`: the live dashboard, with its build-time parity check.
