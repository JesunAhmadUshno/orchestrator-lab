# Level 2, Build: orchestrator-lab

Status: DONE (2026-11-05). A task graph executed end to end by a
real thread pool, with wall clock timeouts, retries with
exponential backoff, cost and step accounting, and a full trace.
Python standard library only.

## Main claim

Build ran one deterministic 12-task parallel report pipeline in
4 waves with a 4-worker thread pool on the Muse VM: 8 tasks
succeeded, 2 failed (B07 wall clock timeout after 3 attempts,
B08 step budget), 2 were blocked (B09 by B07, B11 by B08), total
cost 34 units over 13 attempts with 3 retries and 3 timeout
attempts, 13 steps used, backoff delays totalling 0.04 seconds,
and a 15-entry trace, with 20 new Build unit tests passing for
39 tests in total plus the scaffold smoke test.

## Honest scope line

The workers are deterministic toy functions, not LLMs and not
real agents. Each worker sleeps for a set duration to simulate
work, then returns word and character counts for its payload.
The parallelism, the timeouts, the retries, and the accounting
are real; the work inside each task is not.

## BUILD-SPEC

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

## The scenario

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

## Run it

    python level-2-build/run_build.py
    python -m unittest tests.test_build_orchestrator -v
    python -m unittest discover -s tests
    python tests/test_smoke.py

The runner writes level-2-build/results_build.json
deterministically: run it twice and the file is identical
(verified 2026-11-05: sha256
3896acf5b5f9babe3454eec17c2e0cf785816326397a92810692dbb5dc744c41
on both runs).

## Results (measured 2026-11-05, Muse VM, Python 3.12)

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

## Failure modes and limits

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
  node BlackBoxV2. That costs a grade deduction, named in the
  grade.

## Grade

Grade: 8,600 of 10,000 for this Build level.

Deductions (they sum to 1,400):
- Deterministic toy workers, not real agents or LLMs: minus 500.
- One designed 12-task scenario only, with small hand-built
  graphs in the tests on top of it: minus 400.
- Run on the Muse VM, not the assigned BlackBoxV2 fleet node:
  minus 200.
- A timed out thread cannot be killed, only abandoned, so the
  timeout guarantee is at the supervisor level, not at the
  worker level: minus 200.
- No cost or quality routing and no human approval gates at
  this level (Deep scope): minus 100.

## What Deep adds next

Cost and quality routing per step, human approval gates, and
the full run trace study from the project section text in
SPEC.md. See the root README level map.
