# Level 3, Deep: orchestrator-lab

Status: DONE (2026-11-05). Cost and quality routing, one
escalation on a failed quality check, human approval gates with
a simulated approver, full run traces, and a three strategy
comparison benchmark on one designed scenario. Python standard
library only.

## Main claim

Deep ran one deterministic 11-task scenario under three
strategies on the Muse VM: routed cost 35 units with 9 of 9
executed tasks passing the 0.80 quality threshold and 1
escalation, against all_large at 45 units with 9 passes and
all_small at 18 units with 4 passes and 5 quality fails; in
every strategy 2 approvals were requested, 1 granted, 1
rejected, with 1 task rejected and 1 blocked, and 26 new Deep
unit tests passing for 65 tests in total plus the scaffold
smoke test.

## Honest scope line

The workers are deterministic toy functions, not LLMs and not
real agents. Quality is a deterministic table by tier and true
difficulty, not a measurement of any real model. The approver
in the runner is a deterministic simulated approver that
rejects D09 only. It is labelled simulated everywhere it
appears and is not a real human. The routing, escalation,
approval, blocking, accounting, and traces are real code; the
work inside each task and the quality scores are a teaching
model.

## DEEP-SPEC

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

## The scenario and the comparison

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

## Run it

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

## Failure modes and limits

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
  node BlackBoxV2. That costs a grade deduction, named in the
  grade.

## Grade

Grade: 8,200 of 10,000 for this Deep level.

Deductions (they sum to 1,800):
- Deterministic toy workers, not real LLMs, and quality from
  a fixed table, not measured model behaviour: minus 700.
- One designed 11-task scenario only, with small hand-built
  graphs in the tests on top of it: minus 400.
- Run on the Muse VM, not the assigned BlackBoxV2 fleet
  node: minus 200.
- Sequential execution in Deep, with no parallel pool, so
  routing is not shown under parallel load: minus 200.
- Simulated approver only, with no real human gate, user
  interface, persistence, or appeal path: minus 200.
- Router uses estimated difficulty alone, with one fixed
  threshold and one escalation, and no learned routing or
  cost forecasting: minus 100.

## Sensitivity sweeps

Run: python level-3-deep/sweep_deep.py (under a second).
Writes results_sweep.json: the estimation-error sweep at large
cost 5 and 4, a quality threshold sweep (0.60 to 0.95), a large
tier cost sweep (3 to 8) and a routing cutoff sweep (1 to 5),
all on the same toy table and simulated approver. The live
dashboard reruns these in the browser and its build fails if
the browser port disagrees with this file.

## What remains

The rest of the v2 Deep scope is the v1.1 backlog in the root
ROADMAP.md: real model workers, a measured quality signal,
learned routing, parallel routed execution, and a real human
approval surface.
