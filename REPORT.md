# REPORT: orchestrator-lab (P08)

Status: not pre-registered. Every hypothesis below was written after the
code and results it scores, so it is a description, not a confirmatory
test. Assembled on 2026-11-08 from the three level READMEs, the root
README's benchmark table and docs/research-review.md; their text follows
unchanged apart from the removal of grades (grades are internal).

## Question

When one supervisor coordinates many workers over a task graph, does
routing each task to a cheap or an expensive tier by estimated
difficulty, with one escalation on a failed quality check, keep quality
at lower cost than always using the expensive tier, and how do approval
gates and failures propagate through the graph?

Boundary: this repo is many agents coordinated (supervisor, task graph,
parallel workers, routing, approval gates). One agent's internals is P07.

## Current state (2026-11-08)

- Built and run end to end, three times over: a wave supervisor (stage
  1), a parallel task graph on a thread pool with wall clock timeouts
  and retries (stage 2), and cost and quality routing with approval
  gates (stage 3). Every run writes a deterministic results file; one
  command re-runs all four runners and CI fails if any committed file
  changes.
- The workers are deterministic toy functions, quality is a fixed table
  by true difficulty, the approver is simulated, and every run was on a
  CPU VM (the Muse VM), not the assigned fleet node. No language model
  was called anywhere.
- Verdict: Functional; not pre-registered (see README).

## Hypotheses, scored (post hoc)

None of these had a numeric pass line committed before the run. They
are stated here so each result can be read as a hit or a miss.

| ID | Statement | When it was written | Result | Evidence |
| --- | --- | --- | --- | --- |
| H1 | On the Deep scenario, routed matches all_large's quality passes at lower cost | At migration, 2026-11-08, from the 2026-11-05 main claim | Holds: 9 of 9 passes at 35 units against 9 of 9 at 45 (22.2 percent less); all_small costs 18 but passes only 4 of 9 | level-3-deep/results_deep.json, "comparison" |
| H2 | More estimation error pushes routed cost "toward, or past" all_large | Deep README, 2026-11-05, before the sweep existed | Partly missed. "Toward" holds: mean routed cost rises from 33 (no error) to 43 (all 9 executed tasks underestimated). "Past" is refuted at the scenario's costs (small 2, large 5): the worst of all 512 subsets is 43, below 45. At large cost 4 it holds: worst case reaches all_large (36) from 4 underestimated tasks and exceeds it (38) from 5 | level-3-deep/results_sweep.json, "estimation_error" and "estimation_error_large_cost_4" |
| H3 | Routed stays cheaper than all_large across quality thresholds | At migration, 2026-11-08 | Missed at the strictest threshold: at 0.95 routed costs 50 against 45, with the same 6 passes, because 4 tasks escalate and pay both tiers. Holds from 0.60 to 0.90 (30 to 35 against 45) | level-3-deep/results_sweep.json, "threshold" |
| H4 | The routing cutoff of 2 is the cheapest cutoff on this scenario | At migration, 2026-11-08 | Holds: cutoff 1 costs 44, 2 costs 35, 3 costs 37, 4 costs 41, 5 costs 43, all at 9 passes | level-3-deep/results_sweep.json, "routing_cutoff" |
| H5 | A thread pool runs independent tasks in parallel and enforces a wall clock timeout | Build README, 2026-11-05, with the code | Holds as test assertions with wide margins, not as a benchmark: four 0.30 s tasks finish under 0.75 s with 4 workers; a 0.50 s task is failed by a 0.05 s timeout in under 0.40 s | tests/test_build_orchestrator.py |

No interval is given on any number: the system is deterministic, so
there is no sampling noise. The honest substitute, used for H2, is
exhaustive enumeration of every underestimation subset. None of these
numbers says anything about real models.

## Field profile (Software product): not yet met

| Item | State |
| --- | --- |
| Tests through the public interface | Met: 75 unit tests call the supervisors and runners through their module functions; plus the layout test |
| Coverage reported | Not met: no coverage report yet |
| Dependency audit | Partly: the Python code has no third-party dependencies; the dashboard's npm packages are pinned and watched by Dependabot; no audit report is kept |
| Secret scan | Not met in the repo: no scan step in CI |
| Input validation | Met: bad graphs (duplicate ids, unknown dependencies, cycles, bad fields) raise OrchestratorError before anything runs, with tests |
| Release notes and upgrade path | Partly: release notes for v0.1, v0.5 and v1.0 exist (fanout/release-notes.md, GitHub releases); no upgrade path is written |

## Misses and threats

- H2 "past" and H3 above are misses, shown as measured.
- Construct: "quality" is a table lookup and "cost" a unit count.
- Internal: the one escalation in the main scenario (D07) is designed,
  not discovered.
- External: one designed graph per stage; other shapes appear only in
  small unit test graphs.
- Machine: every run was on the Muse VM, not the assigned fleet node
  BlackBoxV2.
- Not pre-registered: the scenario, the costs and the quality table
  were chosen by the author with the code, so the main comparison could
  have been tuned to look good. The sweeps measure how much it depends
  on those choices; they do not remove the risk.

## Conclusion

The orchestration machinery is real and reproducible: graph validation,
waves, retries, timeouts, transitive blocking, approval gates, routing,
escalation and complete traces, all recomputed byte for byte by one
command. The routing result is a property of one hand-built scenario and
quality table: cheap-first with one escalation saves cost there, loses
its advantage at a strict quality threshold, and survives every
underestimation pattern only because four easy tasks save 3 units each.
A claim about real models needs the next cycle in PROPOSAL.md.

## Results summary (moved from the root README)


Measured 2026-11-05 with level-1-learn/run_learn.py on the Muse VM, Python 3.12. The workers are deterministic toy functions, not LLMs.

| Test | Result |
| --- | --- |
| Learn scenario tasks | 10 tasks in 4 waves (wave sizes 3, 3, 2, 2) |
| Tasks succeeded | 8 of 10 (T05 succeeded after 1 retry) |
| Tasks failed | 1 (T08, step budget exceeded: needs 3 steps, budget 2) |
| Tasks blocked | 1 (T09, blocked by T08) |
| Total cost | 28 units over 10 attempts (1 retry used) |
| Steps used / trace | 13 steps used, 11 trace entries, run status partial |
| Unit tests | 19 passed, plus the scaffold smoke test |
| Determinism | results_learn.json identical across two runs (hash verified) |
| Build scenario tasks | 12 tasks in 4 waves (wave sizes 3, 4, 3, 2), 4-worker thread pool |
| Build tasks succeeded | 8 of 12 (B05 succeeded after 1 retry) |
| Build tasks failed | 2 (B07 wall clock timeout after 3 attempts, B08 step budget) |
| Build tasks blocked | 2 (B09 blocked by B07, B11 blocked by B08) |
| Build total cost | 34 units over 13 attempts (3 retries, 3 timeout attempts) |
| Build steps / trace | 13 steps used, 15 trace entries, backoff delays 0.04 seconds in total, run status partial |
| Build unit tests | 39 passed in total (20 new Build tests plus 19 Learn tests), plus the scaffold smoke test |
| Build determinism | results_build.json identical across two runs (sha256 3896acf5b5f9babe) |
| Deep scenario tasks | 11 tasks in 4 waves, three strategies compared |
| Deep routed | cost 35 units, 9 of 9 executed tasks pass quality, 1 escalation |
| Deep all_large | cost 45 units, 9 quality passes, 0 escalations |
| Deep all_small | cost 18 units, 4 quality passes, 5 quality fails, 0 escalations |
| Deep approvals | 2 requested, 1 granted, 1 rejected in every strategy; 1 task rejected, 1 blocked |
| Deep unit tests | 65 passed in total (26 new Deep tests plus 39 earlier tests), plus the scaffold smoke test |
| Deep determinism | results_deep.json identical across two runs (sha256 399d9c659dd12825) |
| Deep sweeps (2026-11-07) | level-3-deep/sweep_deep.py over all 512 underestimation subsets: oracle routed 33; worst case 43, below all_large 45, at costs 2 and 5; at large cost 4 the worst case reaches all_large from 4 underestimated tasks; at threshold 0.95 routed costs 50 |
| Unit tests (2026-11-07) | 75 passed (10 new sweep and large-tier-fail tests), now run in CI on every push |


### Deep in one paragraph

Deep adds cost and quality routing, human approval gates, and full run traces. The router sees estimated difficulty only: at most 2 routes to the small tier (cost 2), above 2 routes to the large tier (cost 5). A small tier output below the 0.80 quality threshold escalates once to the large tier, with the escalation recorded. Tasks flagged requires_approval are paused for an approver callback; the runner uses a deterministic simulated approver (labelled simulated, not a real human) that rejects D09 only, so D09 is rejected and its dependent D10 is blocked.

Main claim: Deep ran one deterministic 11-task scenario under three strategies on the Muse VM: routed cost 35 units with 9 of 9 executed tasks passing the 0.80 quality threshold and 1 escalation, against all_large at 45 units with 9 passes and all_small at 18 units with 4 passes and 5 quality fails; in every strategy 2 approvals were requested, 1 granted, 1 rejected, with 1 task rejected and 1 blocked, and 26 new Deep unit tests passing for 65 tests in total plus the scaffold smoke test.


## Stage 1, Learn: supervisor and waves (level-1-learn/)

Status: DONE (2026-11-05). A supervisor that splits one job into a
task graph and executes it wave by wave, built with the Python
standard library only.

### Honest scope line

The workers in this level are deterministic toy functions. They are
not LLMs, they are not real agents, they call no API, and they do
not learn. Each worker takes a payload string and returns its word
and character counts. Tasks inside one wave are executed in sorted
order, one after another: the waves show which tasks could run in
parallel, but this level runs no real concurrency. Real workers and
real parallel execution are Build level scope.

### Method

1. Task graph. One supervisor holds the job as a list of tasks.
   Each task has an id, a name, a named worker, explicit
   dependencies, a cost in units charged per attempt, a work step
   count, a step budget, and a payload. The graph is validated
   first: duplicate ids, unknown dependencies, and bad fields raise
   a named OrchestratorError.
2. Waves. The wave of a task is its topological level: 0 with no
   dependencies, else one plus the maximum wave of its
   dependencies. A dependency cycle raises OrchestratorError. The
   flattened wave order is a valid topological order.
3. Execution. The supervisor runs wave by wave, in sorted task id
   order inside a wave, and records every attempt in a run trace.
4. Retries. A task marked flaky fails its first attempt with a
   deterministic FlakyError and is retried once. It succeeds on the
   retry. Only the flaky failure is retried.
5. Step budget (the timeout). A task that needs more steps than its
   step budget fails with a BudgetError and is not retried. The
   budget is a step count, not a wall clock time, so runs stay
   deterministic and no timing number is claimed.
6. Blocking. A task with a dependency that failed or was blocked is
   marked blocked, is never attempted, and costs 0. A failure in one
   branch does not stop tasks that do not depend on it.
7. Cost. Cost is charged per attempt, so the retried task costs
   twice its per-attempt cost. Blocked tasks cost 0.

### The scenario

One small report-building job, 10 tasks. T05 (analyse_trend) is the
flaky task. T08 (verify_source) needs 3 steps against a budget of 2,
so it fails by design and T09 (appendix) is blocked by it. T10
(assemble_report) does not depend on that branch, so the report
still assembles and the run ends as partial, not complete.

### Run it

    python level-1-learn/run_learn.py
    python -m unittest tests.test_learn_orchestrator -v
    python tests/test_smoke.py

The runner writes level-1-learn/results_learn.json deterministically:
run it twice and the file is identical (verified 2026-11-05:
sha256 b5d85a321496c1987e2624c8c3ecf1e8230eefacdefa50b26cb63db8f42c153a
on both runs).

### Results (measured 2026-11-05, Muse VM, Python 3.12)

Waves: wave 0 is T01, T02, T03. Wave 1 is T04, T05, T06. Wave 2 is
T07, T08. Wave 3 is T09, T10.

| Task | Name | Worker | Wave | Depends on | Attempts | Cost | Steps used | Status | Output (words, chars) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T01 | outline | Planner | 0 | none | 1 | 2 | 1 | succeeded | 3, 20 |
| T02 | gather_numbers | Researcher | 0 | none | 1 | 3 | 2 | succeeded | 6, 30 |
| T03 | gather_quotes | Researcher | 0 | none | 1 | 2 | 1 | succeeded | 3, 18 |
| T04 | draft_intro | Writer | 1 | T01 | 1 | 3 | 2 | succeeded | 5, 32 |
| T05 | analyse_trend | Analyst | 1 | T01, T02 | 2 | 8 | 2 | succeeded (after 1 retry) | 5, 27 |
| T06 | chart_spec | Analyst | 1 | T02 | 1 | 3 | 1 | succeeded | 5, 28 |
| T07 | fact_check | Reviewer | 2 | T04, T05 | 1 | 2 | 1 | succeeded | 4, 22 |
| T08 | verify_source | Reviewer | 2 | T03, T06 | 1 | 2 | 2 | failed (step budget) | none |
| T09 | appendix | Writer | 3 | T08 | 0 | 0 | 0 | blocked (by T08) | none |
| T10 | assemble_report | Assembler | 3 | T04, T05, T06, T07 | 1 | 3 | 1 | succeeded | 4, 30 |

Summary: Learn ran one deterministic 10-task report-building
scenario in 4 waves on the Muse VM: 8 tasks succeeded, 1 failed
(T08, step budget), 1 was blocked (T09), total cost 28 units over
10 attempts with 1 retry, 13 steps used, and an 11-entry trace,
with 19 unit tests passing plus the scaffold smoke test. The run
status is partial, because one branch failed by design.

Hand checks: cost is 2 + 3 + 2 + 3 + (4 x 2 attempts) + 3 + 2 + 2 +
0 + 3 = 28. Steps are 1 + 2 + 1 + 2 + 2 + 1 + 1 + 2 (T08 cut at its
budget) + 0 + 1 = 13. Attempts are 9 executed tasks plus 1 extra
attempt for the T05 retry = 10. Trace entries are 10 attempt entries
plus 1 blocked entry for T09 = 11. The T03 payload "data beats
opinion" has 3 words and 18 characters: 4 + 1 + 5 + 1 + 7 = 18.

### Failure modes and limits

- One designed scenario only: a single 10-task graph with fixed
  payloads. No other graph shapes are measured in the runner; the
  unit tests cover only small hand-built graphs on top of it.
- Toy workers: the work itself is word and character counting. No
  claim is made about real agent quality, real task content, or
  LLM behaviour.
- No real parallelism: waves are computed and reported, but tasks
  run one after another inside a wave. No speedup is measured or
  claimed, and no wall clock timing appears anywhere in the results.
- The timeout is a step budget, not elapsed time. A task that hangs
  in real life is out of scope for this level; only the step count
  is enforced.
- Retry is narrow: one retry, only for the deterministic flaky
  failure. Budget failures are never retried, there is no backoff,
  and a flaky task that also exceeded its budget would still fail.
- Blocking is all-or-nothing per task: one failed dependency blocks
  the task even if its other dependencies succeeded, and there is
  no partial-input mode.
- Cost is a unit count on a fixed price list, not money and not
  tokens. Cost and quality routing is Deep level scope.
- This level was run on the Muse VM (CPU), not on its fleet node
  BlackBoxV2.


### What Build adds next

Real workers behind the same graph and supervisor (a real LLM
worker pool), true parallel execution inside a wave with measured
timing, wall clock timeouts beside the step budget, and a wider set
of job graphs. See the root README level map.

## Stage 2, Build: parallel task graph (level-2-build/)

Status: DONE (2026-11-05). A task graph executed end to end by a
real thread pool, with wall clock timeouts, retries with
exponential backoff, cost and step accounting, and a full trace.
Python standard library only.

### Main claim

Build ran one deterministic 12-task parallel report pipeline in
4 waves with a 4-worker thread pool on the Muse VM: 8 tasks
succeeded, 2 failed (B07 wall clock timeout after 3 attempts,
B08 step budget), 2 were blocked (B09 by B07, B11 by B08), total
cost 34 units over 13 attempts with 3 retries and 3 timeout
attempts, 13 steps used, backoff delays totalling 0.04 seconds,
and a 15-entry trace, with 20 new Build unit tests passing for
39 tests in total plus the scaffold smoke test.

### Honest scope line

The workers are deterministic toy functions, not LLMs and not
real agents. Each worker sleeps for a set duration to simulate
work, then returns word and character counts for its payload.
The parallelism, the timeouts, the retries, and the accounting
are real; the work inside each task is not.

### BUILD-SPEC

1. Task graph. Same validated graph model as Learn, plus three
   Build fields per task: sleep_seconds (simulated work
   duration, non-negative), timeout_seconds (wall clock limit
   per attempt, positive), and fail_times (the task fails
   transiently on that many first attempts). Bad values raise
   OrchestratorError before anything runs.
2. Waves. Dependency waves are the topological levels from
   Learn. A wave starts only after the previous wave finishes,
   so a task never starts before all of its dependencies have
   succeeded.
3. Parallel execution. Inside a wave, one attempt round submits
   every pending task to a ThreadPoolExecutor with 4 workers at
   the same time. Records come back in topological order, not in
   finishing order, so results do not depend on which worker
   finishes first.
4. Wall clock timeout, per attempt. Each attempt is collected
   with future.result(timeout), with the deadline counted from
   its submit time. An attempt that passes its deadline is
   recorded as attempt_timeout. Python threads cannot be
   killed, so the timed out thread is abandoned, its late
   result is discarded, and that pool is shut down without
   waiting for it.
5. Retries with backoff. Transient failures and timeouts are
   retried up to 2 times. Before retry round 1 the supervisor
   sleeps 0.01 seconds, before round 2 it sleeps 0.02 seconds
   (base 0.01 times 2 to the power retry minus 1). The delays
   are recorded per task. A step budget failure is never
   retried, because the same work against the same budget
   cannot succeed.
6. Blocking. A task whose dependency failed or was blocked is
   marked blocked, is never attempted, costs 0, and uses
   0 steps. Blocking is transitive. A failure in one branch
   does not stop tasks that do not depend on it.
7. Accounting. Cost is charged per attempt, so a retried task
   costs once per try. Steps used are the work steps of a
   succeeded task, the budget of a budget-failed task, and 0
   for timed out, transiently failed, and blocked tasks.
8. Trace. Every attempt and every blocked task adds one trace
   entry. Entries are merged in topological task order with
   sequence numbers 1 to N, so the trace is deterministic even
   though execution is parallel.
9. Determinism. No elapsed wall clock value, timestamp, or
   random value is written to the results file. The console
   prints one observed wall clock line for the run; it is not
   stored.

### The scenario

One parallel report pipeline, 12 tasks. Wave 0 has three
gathering tasks that each sleep 0.20 seconds, so the wave takes
about one sleep, not three. B05 (analyse_trend) fails
transiently on attempt 1 and succeeds on its first retry. B07
(slow_source) sleeps 0.50 seconds against a 0.10 second
timeout, times out on all 3 attempts, and fails; B09 is blocked
by it. B08 (verify_source) needs 3 steps against a budget of 2,
fails with no retry, and B11 is blocked by it. B12
(assemble_report) does not depend on either failed branch, so
the report still assembles and the run ends as partial.

### Run it

    python level-2-build/run_build.py
    python -m unittest tests.test_build_orchestrator -v
    python -m unittest discover -s tests
    python tests/test_smoke.py

The runner writes level-2-build/results_build.json
deterministically: run it twice and the file is identical
(verified 2026-11-05: sha256
3896acf5b5f9babe3454eec17c2e0cf785816326397a92810692dbb5dc744c41
on both runs).

### Results (measured 2026-11-05, Muse VM, Python 3.12)

Waves: wave 0 is B01, B02, B03. Wave 1 is B04, B05, B06, B07.
Wave 2 is B08, B09, B10. Wave 3 is B11, B12.

| Task | Name | Worker | Wave | Depends on | Attempts | Cost | Steps used | Status | Output (words, chars) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B01 | outline | Planner | 0 | none | 1 | 2 | 1 | succeeded | 3, 20 |
| B02 | gather_numbers | Researcher | 0 | none | 1 | 3 | 2 | succeeded | 6, 30 |
| B03 | gather_quotes | Researcher | 0 | none | 1 | 2 | 1 | succeeded | 3, 18 |
| B04 | draft_intro | Writer | 1 | B01 | 1 | 3 | 2 | succeeded | 5, 32 |
| B05 | analyse_trend | Analyst | 1 | B01, B02 | 2 | 8 | 2 | succeeded (after 1 retry) | 5, 27 |
| B06 | chart_spec | Analyst | 1 | B02 | 1 | 3 | 1 | succeeded | 5, 28 |
| B07 | slow_source | Reviewer | 1 | B03 | 3 | 6 | 0 | failed (timeout, 3 timeout attempts) | none |
| B08 | verify_source | Reviewer | 2 | B03, B06 | 1 | 2 | 2 | failed (step budget) | none |
| B09 | appendix | Writer | 2 | B07 | 0 | 0 | 0 | blocked (by B07) | none |
| B10 | fact_check | Reviewer | 2 | B04, B05 | 1 | 2 | 1 | succeeded | 4, 22 |
| B11 | source_appendix | Writer | 3 | B08 | 0 | 0 | 0 | blocked (by B08) | none |
| B12 | assemble_report | Assembler | 3 | B04, B05, B06, B10 | 1 | 3 | 1 | succeeded | 4, 30 |

Hand checks: cost is 2 + 3 + 2 + 3 + (4 x 2 attempts) + 3 +
(2 x 3 attempts) + 2 + 0 + 2 + 0 + 3 = 34. Steps are the
succeeded tasks 1 + 2 + 1 + 2 + 2 + 1 + 1 + 1 = 11, plus B08
cut at its budget of 2, plus 0 for B07, B09, and B11 = 13.
Attempts are 1 + 1 + 1 + 1 + 2 + 1 + 3 + 1 + 0 + 1 + 0 + 1 =
13. Trace entries are 13 attempt entries plus 2 blocked
entries = 15. Retries are B05 with 1 plus B07 with 2 = 3.
Backoff delays are B05 with 0.01 plus B07 with 0.01 and 0.02 =
0.04 seconds in total.

Parallel evidence, from the unit tests, not from the results
file: four independent tasks that each sleep 0.30 seconds
finish in under 0.75 seconds of wall clock with 4 workers
(sequential execution would take about 1.20 seconds), and a
task that sleeps 0.50 seconds against a 0.05 second timeout is
reported failed in under 0.40 seconds. These are test
assertions with wide margins, not benchmark claims.

Tests: 39 passed in total (20 new Build tests in
tests/test_build_orchestrator.py covering parallel speedup,
order independence, timeout firing, timeout retry, retry
success, retry exhaustion, budget no-retry, blocked and
transitive blocking, cost accounting, the exact scenario, and
validation; plus the 19 Learn tests), and the scaffold smoke
test passes.

### Failure modes and limits

- Toy workers: the work itself is sleeping plus word and
  character counting. No claim is made about real agent
  quality, real task content, or LLM behaviour.
- One designed scenario only: a single 12-task graph with fixed
  payloads and fixed durations. Other graph shapes are covered
  only by small hand-built unit test graphs.
- A timed out thread cannot be killed in Python. It keeps
  running until its sleep ends, its result is discarded, and
  it holds no lock on the run. Non-cooperative or blocking
  native code would be a worse case and is out of scope here.
- Thread pool only: parallelism is threads inside one process,
  good for sleep and IO shaped work. CPU-bound Python work
  would be limited by the GIL; processes are out of scope.
- Retries are fixed policy: at most 2, transient failures and
  timeouts only, with a short fixed backoff base of 0.01
  seconds chosen so test and runner runs stay fast. Production
  backoff would be longer and jittered; jitter would break
  determinism and is not used.
- Cost is a unit count on a fixed price list, not money and
  not tokens. Cost and quality routing, and human approval
  gates, are Deep level scope.
- This level was run on the Muse VM (CPU), not on its fleet
  node BlackBoxV2.


### What Deep adds next

Cost and quality routing per step, human approval gates, and
the full run trace study from the project section text in
SPEC.md. See the root README level map.

## Stage 3, Deep: cost and quality routing with approval gates (level-3-deep/)

Status: DONE (2026-11-05). Cost and quality routing, one
escalation on a failed quality check, human approval gates with
a simulated approver, full run traces, and a three strategy
comparison benchmark on one designed scenario. Python standard
library only.

### Main claim

Deep ran one deterministic 11-task scenario under three
strategies on the Muse VM: routed cost 35 units with 9 of 9
executed tasks passing the 0.80 quality threshold and 1
escalation, against all_large at 45 units with 9 passes and
all_small at 18 units with 4 passes and 5 quality fails; in
every strategy 2 approvals were requested, 1 granted, 1
rejected, with 1 task rejected and 1 blocked, and 26 new Deep
unit tests passing for 65 tests in total plus the scaffold
smoke test.

### Honest scope line

The workers are deterministic toy functions, not LLMs and not
real agents. Quality is a deterministic table by tier and true
difficulty, not a measurement of any real model. The approver
in the runner is a deterministic simulated approver that
rejects D09 only. It is labelled simulated everywhere it
appears and is not a real human. The routing, escalation,
approval, blocking, accounting, and traces are real code; the
work inside each task and the quality scores are a teaching
model.

### DEEP-SPEC

1. Tiers. Small costs 2 units and scores 0.95, 0.90, 0.70,
   0.55, 0.40 at true difficulty 1 to 5. Large costs 5 units
   and scores 0.98, 0.97, 0.95, 0.92, 0.88. The quality
   threshold is 0.80, so small passes only at difficulty 1
   and 2 and large passes at every difficulty.
2. Routing. The routed strategy sees only estimated
   difficulty: at most 2 routes to small, above 2 routes to
   large. The all_small and all_large strategies force one
   tier for every executed task.
3. Quality check and escalation. In the routed strategy only,
   a small tier output below 0.80 escalates once to the large
   tier. The large cost is charged on top of the small cost,
   the large output replaces the small output, and the
   escalation is recorded in the task record and the trace.
   There is no second escalation.
4. Approval gates. A task flagged requires_approval is paused
   before routing and the approver callback decides. Approved
   tasks run. Rejected tasks are marked rejected, cost 0, are
   never attempted, and their dependents are blocked, with
   blocking transitive through the graph.
5. Execution and trace. Tasks run wave by wave in topological
   order, sequentially inside a wave in sorted order, so the
   results do not depend on thread timing. Every routing,
   approval, attempt, quality check, escalation, success,
   rejection, and blocked step adds a trace entry. Entries are
   merged in topological order with sequence numbers.
6. Determinism. No timestamp, random value, or wall clock
   value is written to any record.

### The scenario and the comparison

One report pipeline, 11 tasks in 4 waves: wave 0 is D01, D02,
D09; wave 1 is D03, D06, D07, D10; wave 2 is D04, D05, D08;
wave 3 is D11. D07 is underestimated on purpose (estimated 1,
true 3), so routed starts it on small, fails the quality check
at 0.70, and escalates it once to large, where it passes at
0.95 for a total cost of 7. D08 and D09 require approval. The
simulated approver grants D08 and rejects D09, so D09 is
rejected and D10, which depends on D09, is blocked. The other
9 tasks execute in every strategy.

| Strategy | Cost units | Quality pass | Quality fail | Escalations | Succeeded | Rejected | Blocked | Trace entries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_small | 18 | 4 | 5 | 0 | 9 | 1 | 1 | 39 |
| all_large | 45 | 9 | 0 | 0 | 9 | 1 | 1 | 39 |
| routed | 35 | 9 | 0 | 1 | 9 | 1 | 1 | 42 |

Hand checks. Executed tasks are 9 in every strategy (11 minus
1 rejected minus 1 blocked). all_small costs 9 x 2 = 18 and
passes only the truly easy executed tasks D01, D02, D06, D11,
so 4 passes and 5 fails. all_large costs 9 x 5 = 45 and passes
all 9. Routed costs 4 small tasks (D01, D02, D06, D11) at 2
each, plus 4 large tasks (D03, D04, D05, D08) at 5 each, plus
the escalated D07 at 2 + 5 = 7, for 8 + 20 + 7 = 35. Routed
saves 45 - 35 = 10 units against all_large (22.2 percent of
45) at the same 9 quality passes. Approvals are the same in
every strategy: 2 requested, 1 granted, 1 rejected.

Routed task detail:

| Task | Name | Difficulty (true, estimated) | Initial tier | Final tier | Cost | Quality | Pass | Status | Approval |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D01 | outline | 1, 1 | small | small | 2 | 0.95 | yes | succeeded | not required |
| D02 | gather_numbers | 2, 2 | small | small | 2 | 0.90 | yes | succeeded | not required |
| D09 | publish_external_summary | 1, 1 | none | none | 0 | none | no | rejected | rejected |
| D03 | deep_analysis | 3, 3 | large | large | 5 | 0.95 | yes | succeeded | not required |
| D06 | chart_spec | 2, 2 | small | small | 2 | 0.90 | yes | succeeded | not required |
| D07 | subtle_fact_check | 3, 1 | small | large | 7 | 0.95 | yes | succeeded | not required |
| D10 | external_appendix | 2, 2 | none | none | 0 | none | no | blocked | not required |
| D04 | risk_model | 4, 4 | large | large | 5 | 0.92 | yes | succeeded | not required |
| D05 | hard_proof | 5, 5 | large | large | 5 | 0.88 | yes | succeeded | not required |
| D08 | release_review | 4, 4 | large | large | 5 | 0.92 | yes | succeeded | approved |
| D11 | assemble_report | 2, 2 | small | small | 2 | 0.90 | yes | succeeded | not required |

### Run it

    python level-3-deep/run_deep.py
    python -m unittest tests.test_deep_orchestrator -v
    python -m unittest discover -s tests
    python tests/test_smoke.py

The runner writes level-3-deep/results_deep.json
deterministically: run it twice and the file is identical
(verified 2026-11-05: sha256
399d9c659dd12825efe42597f729056585cd2fef25985a452f776fd5cdc20a6b
on both runs).

Tests: 65 passed in total (26 new Deep tests in
tests/test_deep_orchestrator.py covering the quality table,
routing choice by estimate, escalation once and its cost,
no escalation outside routed, approval approve and reject
paths with transitive blocking, the exact comparison
arithmetic for all three strategies, cost recomputation from
task records, determinism, and validation; plus the 19 Learn
tests and the 20 Build tests), and the scaffold smoke test
passes.

### Failure modes and limits

- Toy workers, table quality: the work is word and character
  counting and the quality scores come from a fixed table by
  difficulty. No claim is made about real LLM quality, real
  model routing, or real task content. A real router would
  need a measured quality signal, not a table.
- Underestimation is designed, not discovered: the single
  escalation comes from D07, whose estimate was set low on
  purpose. Real estimation error rates are unknown here, and
  a higher error rate would push routed cost toward, or past,
  all_large cost, because an escalated task costs 7, more
  than the 5 of going large directly. Measured since in
  results_sweep.json (sweep_deep.py, all 512 underestimation
  subsets): at small cost 2 and large cost 5 routed stays
  below all_large even with all 9 executed tasks
  underestimated (worst case 43 against 45), because the 4
  easy tasks still save 3 each; at large cost 4 the worst
  case reaches all_large from 4 underestimated tasks. At a
  quality threshold of 0.95 routed costs 50, more than
  all_large at 45.
- One escalation only: if the large tier also failed the
  threshold, the task would stand as a quality fail with no
  further retry, appeal, or fallback. In this table large
  never fails at the 0.80 threshold, so the scenario does not
  reach that path. It is now covered by two unit tests in
  tests/test_sweep_deep.py and by the threshold sweep, where
  at 0.90 and above the large tier fails at difficulty 5.
- Simulated approver: the gate callback is real, but the
  decider is a deterministic reject list, not a human, not a
  user interface, and not a persistent approval queue. A
  rejected task has no appeal or override path.
- Sequential execution: Deep runs waves sequentially for
  determinism and does not reuse the Build thread pool, so
  Deep makes no parallelism claim. Combining routed parallel
  execution with timing independent traces is v1.1 work.
- One designed scenario only: a single 11-task graph with
  fixed difficulties, estimates, and costs. Other shapes are
  covered only by small hand-built unit test graphs.
- Cost is a unit count on a fixed two price list, not money
  and not tokens. No latency, throughput, or dollar figure is
  claimed.
- This level was run on the Muse VM (CPU), not on its fleet
  node BlackBoxV2.


### Sensitivity sweeps

Run: python level-3-deep/sweep_deep.py (under a second).
Writes results_sweep.json: the estimation-error sweep at large
cost 5 and 4, a quality threshold sweep (0.60 to 0.95), a large
tier cost sweep (3 to 8) and a routing cutoff sweep (1 to 5),
all on the same toy table and simulated approver. The live
dashboard reruns these in the browser and its build fails if
the browser port disagrees with this file.

### What remains

The rest of the v2 Deep scope is the v1.1 backlog in
PROPOSAL.md ("Next cycle"): real model workers, a measured quality signal,
learned routing, parallel routed execution, and a real human
approval surface.

## Review notes (2026-11-07, moved from docs/research-review.md)

Date: 2026-11-07. Scope: the three levels as committed, plus the
changes made on the `site/live-dashboard` branch.
Each gap is either fixed in this change (with the file that fixes it)
or names the exact compute or data it still needs.

Short verdict: the engineering is careful and fully reproducible, but
the research claim is narrow by construction. The headline (routed 35
cost units against 45 for all_large at 9 of 9 quality passes) is a
property of a hand-set quality table and one designed scenario. This
change measures how fragile that result is to its own assumptions; it
cannot make it a claim about real models.

### 1. Research question

Implicit question: does routing each task to a cheap or expensive tier
by estimated difficulty, with one escalation on a failed quality
check, keep quality at lower cost than always using the expensive
tier, and how do approval gates interact with a task graph?

- Strength: concrete, operational, and answered with recorded numbers.
- Gap: the question is never stated as a question in SPEC.md, and its
  answer depends entirely on the quality table. Not fixed by code;
  this review states it above. No compute needed.

### 2. Hypotheses

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

### 3. Method

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

### 4. Baselines

- Strength: all_small and all_large bracket the routed strategy on the
  same graph and the same simulated approver.
- Gap: no oracle baseline. Fixed: the sweep's k = 0 row is the oracle
  router (perfect estimates), 33 cost units, so the designed D07
  underestimate costs 2 units over the oracle.
- Remaining: no comparison with a published cascade or learned router.
  Needs real model workers (see 3) and the related-work pass (see 8).

### 5. Statistics and uncertainty

- The system is deterministic, so there is no sampling noise to put an
  interval on. The honest substitute on a toy model is exhaustive
  enumeration, which this change adds: each k reports the minimum,
  mean and maximum routed cost over every subset, not one draw.
- Remaining: real uncertainty comes from real model outputs and real
  estimation error. Needs a labelled task set (several hundred tasks
  with gold difficulty and gold answers) and repeated runs per tier,
  then bootstrap intervals on cost and pass rate per strategy.

### 6. Reproducibility

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

### 7. Threats to validity

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

### 8. Related work

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

### 9. Limitations

- Strength: each level README listed specific failure modes (now the
  stage sections of REPORT.md). The live dashboard quotes them verbatim
  at build time, so the page cannot drift from the report.
- Updated: the Deep README limit on estimation error now carries the
  measured sweep result.
- Remaining limits that need resources: real models (GPU node), a real
  human approval surface with persistence (engineering), latency and
  dollar cost (real model calls).

### What changed in this branch

- `.github/workflows/ci.yml`: the full unit test suite runs on push.
- `level-3-deep/orchestrator_deep.py`: routing cutoff parameter, default unchanged.
- `level-3-deep/run_deep.py`, `scenario_deep.json`: scenario exported as data.
- `level-3-deep/sweep_deep.py`, `results_sweep.json`: estimation-error, threshold, cost and cutoff sweeps.
- `tests/test_sweep_deep.py`: 10 new tests (75 in total).
- `NOVELTY.md`, `level-3-deep/README.md`: measured, honest updates.
- `site/`: the live dashboard, with its build-time parity check.
