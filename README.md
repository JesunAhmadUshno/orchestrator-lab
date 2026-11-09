# orchestrator-lab

**Question.** When one supervisor coordinates many workers over a task
graph, does routing each task to a cheap or an expensive tier by
estimated difficulty, with one escalation on a failed quality check,
keep quality at lower cost than always using the expensive tier?

**Headline.** On one designed 11-task toy scenario, routing by estimated difficulty cost 35 units against 45 for always using the large tier, at the same 9 of 9 quality passes (22.2 percent less); across all 512 patterns of underestimated tasks it stayed between 33 and 43 units, but at a strict 0.95 quality threshold it cost 50, more than always-large. The runs are deterministic, so these are exact counts with no sampling interval, and they say nothing about real models.

**Field.** Software product. **Job family.** AI agent engineering.

**Verdict.** Functional; not pre-registered. Tests pass in CI on Python
3.11 and 3.12, one command re-runs every stage and fails if any results
file changes, and the supervisor has run end to end on all three
recorded scenarios (10, 12 and 11 tasks). No plan with hypotheses and
pass lines was committed before code or results, so the repo is capped
at Functional (METHOD section 7). Workers are deterministic toy
functions, quality is a fixed table, and the approver is simulated.

Scope: this repo is many agents coordinated (supervisor, task graph,
parallel workers, routing, approval gates). One agent's internals is P07.

Live dashboard: https://jesunahmadushno.github.io/orchestrator-lab/
(a live router and estimation-error sweep that rerun the Deep supervisor
in the browser, checked against the Python results on every build;
source in site/).

## Reproduce

```text
python level-1-learn/run_learn.py && python level-2-build/run_build.py && python level-3-deep/run_deep.py && python level-3-deep/sweep_deep.py && git diff --exit-code -- level-1-learn level-2-build level-3-deep
python -m unittest discover -s tests -v
```

Python 3 standard library only, no dependencies, no randomness, no
timestamps in the results files. The first line re-runs every stage
(about two seconds) and fails if any committed result changes; CI runs
the same steps. The headline numbers are in
level-3-deep/results_deep.json ("comparison") and
level-3-deep/results_sweep.json ("estimation_error", "threshold").

## Lifecycle

- Question: DONE 2026-11-08
- Proposal: OPEN 2026-11-08
- Baseline: DONE 2026-11-05
- Build: DONE 2026-11-05
- Evaluate: OPEN 2026-11-08
- Report: DONE 2026-11-08
- Review: OPEN 2026-11-08
- Release: OPEN 2026-11-08

The question was written down at migration (2026-11-08). SPEC.md came
before the code but held scope only, so the proposal is not locked.
Baseline is all_large and all_small on the same scenario. Evaluate stays
open until the Software product profile is met (coverage report,
dependency audit and secret scan) under a locked proposal. The tags
v0.1, v0.5 and v1.0 are the old Learn, Build and Deep releases, not a
v1.0 Released verdict under this standard.

## Layout

| Path | What it holds |
| --- | --- |
| PROPOSAL.md | Question, scope, prior work and novelty, the plans as committed (not pre-registered), and the next cycle |
| REPORT.md | Hypotheses scored with misses, field profile, the method and results of each stage, the 2026-11-07 review notes |
| CHANGELOG.md | Releases v0.1, v0.5, v1.0 and every change since |
| level-1-learn/ | Code: wave supervisor (orchestrator.py, run_learn.py); results: results_learn.json |
| level-2-build/ | Code: parallel task graph (orchestrator_build.py, run_build.py); results: results_build.json |
| level-3-deep/ | Code: routing and approval gates (orchestrator_deep.py, run_deep.py, sweep_deep.py); scenario: scenario_deep.json; results: results_deep.json, results_sweep.json |
| tests/ | Unit tests for every stage and the sweeps, and the layout test (run in CI) |
| docs/decisions/ | Records of hard-to-reverse choices |
| docs/publicity.md | Channel log for the fan-out drafts |
| fanout/ | Dated 2026-11-05 drafts (blog, tutorial, page, post, paper brief, release notes); file references inside them use the pre-v2 layout |
| site/ | The live dashboard, built from the files above; a JavaScript port must reproduce every recorded result before it builds |

The code keeps its stage folder names (decision 0001): code, scenario
and results sit together per stage, so there is no separate src/,
experiments/ or results/ folder. The runs are deterministic, so the
results files are the evidence; the runners regenerate them byte for
byte and CI fails on any difference.

## License

Code: Apache-2.0 (see LICENSE). Tutorials: CC BY 4.0. Ruled in D-V3-11, 2026-11-04.
