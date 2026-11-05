# Many Hands, One Graph: Building orchestrator-lab in the Open

By Jesun Ahmad Ushno
Date: 2026-11-05
Status: DRAFT, written fan-out for P08 orchestrator-lab v1.0. Not posted.

## The problem

A multi-agent job fails in ways a single call does not. One task
fails and its dependents should block, not run on missing input.
A cheap worker is enough for an easy step and wasteful to replace
with a large one, while a hard step sent to a cheap worker fails
quality. A step that changes the outside world should wait for
approval. This project builds that supervisor in the open, small
enough to read and check by hand.

This project, P08 in Roadmap v3, builds multi-agent orchestration
in three levels: a supervisor with a task graph executed wave by
wave; then parallel execution with retries and timeouts; then
cost and quality routing with approval gates. All code runs with
the Python standard library only. The workers are deterministic
toy functions at every level. They are not LLMs and not real
agents, and nothing here claims otherwise. Deep quality comes
from a fixed table, and the Deep approver is simulated.

Repository: https://github.com/JesunAhmadUshno/orchestrator-lab

## Past, present, future (the dossier, condensed)

Past: workflow engines and framework multi-agent demos already
exist. The prior art and the problem history are recorded in
DOSSIER.md and NOVELTY.md in the repo. The novelty claim there
stays marked PROPOSED. This post makes no novelty claim beyond
the measured work below.

Present: v1.0 closes three levels on 2026-11-05. Learn built a
wave supervisor with retries, a step budget, and blocked tasks
on a 10-task scenario (grade 8,700 of 10,000). Build added a
12-task parallel pipeline on a 4-worker thread pool with wall
clock timeouts and backoff (grade 8,600 of 10,000). Compressed
Deep added cost and quality routing over two toy tiers, one
escalation, and approval gates on an 11-task scenario (grade
8,200 of 10,000).

Future: the rest of the v2 Deep scope is named in ROADMAP.md in
the repo as the v1.1 backlog. It includes real model workers, a
measured quality signal, learned routing, parallel routed
execution, a real human approval surface, more scenarios,
latency and dollar cost, and a fleet run. None of that is done,
and none of it is claimed here.

## Main results claim

At v1.0, with deterministic toy workers, a fixed quality table, and a simulated approver in Deep: Learn ran one 10-task scenario in 4 waves with 8 succeeded, 1 failed (T08, step budget), and 1 blocked (T09), at total cost 28 units over 10 attempts with 1 retry, 13 steps used, and 19 tests; Build ran one 12-task scenario in 4 waves with a 4-worker thread pool, with 8 succeeded, 2 failed (B07 wall clock timeout after 3 attempts, B08 step budget), and 2 blocked, at total cost 34 units over 13 attempts with 3 retries, 13 steps used, backoff delays totalling 0.04 seconds, and 39 tests in total; Deep ran one designed 11-task scenario in 4 waves with 9 tasks executed per strategy, where all_small cost 18 units with 4 quality passes and 5 fails, all_large cost 45 units with 9 passes and 0 fails, and routed cost 35 units with 9 passes, 0 fails, and 1 escalation (D07), so routed saves 10 units, which is 22.2 percent of 45, at the same 9 passes as all_large, with approvals at 2 requested, 1 granted, and 1 rejected, 1 task rejected and 1 blocked, and 65 tests in total.

Every number in that claim comes from a run recorded in the
level READMEs and results files in the repo, with toy workers.
Read the limits section below before quoting any of it.

## Results by level

### Level 1, Learn (release v0.1)

Learn holds a job as a validated task graph, computes dependency
waves as topological levels, and runs wave by wave in sorted
order. A flaky task is retried once. A task over its step budget
fails and is not retried. A task whose dependency failed is
blocked and costs 0.

| Measure | Result |
| --- | --- |
| Scenario | 10 tasks in 4 waves (sizes 3, 3, 2, 2) |
| Succeeded | 8 of 10 (T05 after 1 retry) |
| Failed | 1 (T08, step budget: needs 3, budget 2) |
| Blocked | 1 (T09, blocked by T08) |
| Total cost | 28 units over 10 attempts |
| Steps and trace | 13 steps used, 11 trace entries, status partial |
| Tests | 19, plus the scaffold smoke test |
| Determinism | results_learn.json identical across two runs |

Grade: 8,700 of 10,000, deductions itemized in the Learn README.

### Level 2, Build (release v0.5)

Build runs each wave on a ThreadPoolExecutor with 4 workers,
with a wall clock timeout per attempt, retries with exponential
backoff for transient failures and timeouts, and a deterministic
trace merged in topological order.

| Measure | Result |
| --- | --- |
| Scenario | 12 tasks in 4 waves (sizes 3, 4, 3, 2) |
| Succeeded | 8 of 12 (B05 after 1 retry) |
| Failed | 2 (B07 timeout after 3 attempts, B08 step budget) |
| Blocked | 2 (B09 by B07, B11 by B08) |
| Total cost | 34 units over 13 attempts |
| Steps and trace | 13 steps used, 15 trace entries |
| Backoff | 0.04 seconds in total |
| Tests | 20 Build, 39 in total, plus the smoke test |
| Determinism | results_build.json identical across two runs |

Grade: 8,600 of 10,000, deductions itemized in the Build README.

### Level 3, Deep, compressed (release v1.0)

Deep routes by estimated difficulty only: at most 2 goes to the
small tier (cost 2), above 2 goes to the large tier (cost 5). A
small output below the 0.80 quality threshold escalates once to
large. Tasks flagged requires_approval wait for an approver
callback. The runner approver is simulated and rejects D09 only,
so D09 is rejected and D10 is blocked. Execution in Deep is
sequential, in sorted wave order, for determinism.

| Strategy | Cost | Quality pass | Quality fail | Escalations | Succeeded | Rejected | Blocked |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all_small | 18 | 4 | 5 | 0 | 9 | 1 | 1 |
| all_large | 45 | 9 | 0 | 0 | 9 | 1 | 1 |
| routed | 35 | 9 | 0 | 1 | 9 | 1 | 1 |

Routed detail: 4 small tasks at 2 each, plus 4 large tasks at 5
each, plus the escalated D07 at 2 plus 5 equals 7, for 8 plus 20
plus 7 equals 35. The saving against all_large is 45 minus 35
equals 10 units, 22.2 percent of 45, at the same 9 passes.

Tests: 26 Deep tests, 65 in total with Learn and Build.
Determinism: results_deep.json identical across two runs.

Grade: 8,200 of 10,000. Deductions are itemized in the Deep
README: minus 700 for toy workers and table quality, minus 400
for one designed scenario, minus 200 for running on the Muse VM
instead of BlackBoxV2, minus 200 for sequential execution, minus
200 for a simulated approver only, and minus 100 for a router
that uses estimated difficulty alone. Total deductions 1,800,
and 10,000 minus 1,800 is 8,200.

## Honest limits

- Toy workers, at every level: the work is word and character
  counting, plus sleeping in Build to simulate duration. No claim
  is made about real agent quality or LLM behaviour.
- Synthetic and designed scenarios only: one graph per level,
  with fixed payloads, difficulties, and costs. Other shapes are
  covered only by small hand-built unit test graphs.
- Fixed quality table in Deep: quality scores are a table by
  tier and true difficulty, not measured model behaviour. A real
  router needs a measured quality signal.
- The single Deep escalation is designed: D07 was underestimated
  on purpose (estimated 1, true 3). A higher real error rate
  would push routed cost toward or past all_large, because an
  escalated task costs 7, more than 5 direct to large.
- Simulated approver in Deep: the gate callback is real code,
  but the decider rejects D09 from a fixed list. It is not a
  human, not a user interface, and has no appeal path.
- Sequential execution in Learn and Deep: waves show what could
  run in parallel. Only Build runs a real thread pool, and Deep
  makes no parallelism claim.
- Cost is a unit count on fixed price lists, not money and not
  tokens. No latency or dollar figure is claimed for Deep.
- Compressed Deep is not the full v2 Deep scope. The remainder
  is the named v1.1 backlog in ROADMAP.md.
- All levels ran on the Muse VM, not the assigned BlackBoxV2
  node. That deduction is named in each level grade.

## Where to go next

- Tutorial: fanout/tutorial.md in the repo, a step-by-step module
  that runs all three levels and the full test suite.
- Releases: v0.1 (Learn), v0.5 (Build), v1.0 (Learn, Build,
  compressed Deep) on the GitHub repo linked above.
- Book chapter: "Many Hands, One Graph" per SPEC.md, held as a
  draft angle in this fan-out set.
- License: code Apache-2.0, tutorials CC BY 4.0.
