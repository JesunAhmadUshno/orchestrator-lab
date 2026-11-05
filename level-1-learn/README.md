# Level 1, Learn: orchestrator-lab

Status: DONE (2026-11-05). A supervisor that splits one job into a
task graph and executes it wave by wave, built with the Python
standard library only.

## Honest scope line

The workers in this level are deterministic toy functions. They are
not LLMs, they are not real agents, they call no API, and they do
not learn. Each worker takes a payload string and returns its word
and character counts. Tasks inside one wave are executed in sorted
order, one after another: the waves show which tasks could run in
parallel, but this level runs no real concurrency. Real workers and
real parallel execution are Build level scope.

## Method

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

## The scenario

One small report-building job, 10 tasks. T05 (analyse_trend) is the
flaky task. T08 (verify_source) needs 3 steps against a budget of 2,
so it fails by design and T09 (appendix) is blocked by it. T10
(assemble_report) does not depend on that branch, so the report
still assembles and the run ends as partial, not complete.

## Run it

    python level-1-learn/run_learn.py
    python -m unittest tests.test_learn_orchestrator -v
    python tests/test_smoke.py

The runner writes level-1-learn/results_learn.json deterministically:
run it twice and the file is identical (verified 2026-11-05:
sha256 b5d85a321496c1987e2624c8c3ecf1e8230eefacdefa50b26cb63db8f42c153a
on both runs).

## Results (measured 2026-11-05, Muse VM, Python 3.12)

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

## Failure modes and limits

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
  BlackBoxV2. That costs a grade deduction, named in the grade.

## Grade

Grade: 8,700 of 10,000 for this Learn level.

Deductions (they sum to 1,300):
- Small synthetic designed scenario, one 10-task graph: minus 500.
- Deterministic toy workers, not real agents or LLMs, and waves
  computed but executed sequentially with no real parallelism:
  minus 400.
- Run on the Muse VM, not the assigned BlackBoxV2 fleet node:
  minus 200.
- Timeout enforced as a simulated step budget only, with no wall
  clock timeout and no concurrency behaviour measured: minus 100.
- Retry policy is minimal (one retry, flaky failures only, no
  backoff) and there are no human approval gates and no cost or
  quality routing at this level: minus 100.

## What Build adds next

Real workers behind the same graph and supervisor (a real LLM
worker pool), true parallel execution inside a wave with measured
timing, wall clock timeouts beside the step budget, and a wider set
of job graphs. See the root README level map.
