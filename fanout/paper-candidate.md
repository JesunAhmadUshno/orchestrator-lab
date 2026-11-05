# Paper candidate brief: cost and quality routing in a task graph supervisor

Project: P08 orchestrator-lab
Status: CANDIDATE, brief written 2026-11-05
Submission note: submission is Jesun's tap. Nothing is submitted by
this brief, and no venue has been contacted. The publications
tracker is updated by the coordinator, not by this file.

## Working title

Cost and quality routing in a task graph supervisor: routed cost
35 against all-large 45 at the same 9 quality passes on one
designed scenario, with a designed estimation error

## Abstract draft

Based only on the measured v1.0 results recorded in the repo.
Numbers below are from synthetic designed scenarios with
deterministic toy workers and are stated as such. No real model
was called, quality is a fixed table, and the approver is
simulated.

Multi-agent supervisors must decide, per task, how much worker
capacity to buy and when to stop for approval, while a failed
dependency should block its dependents rather than let them run
on missing input. This work presents an open, dependency-free
task graph supervisor and measures its routing rule. At Learn
level, a validated graph executed in dependency waves ran a
10-task scenario with 8 succeeded, 1 failed on a step budget,
and 1 blocked, at cost 28 over 10 attempts and 19 unit tests. At
Build level, a 4-worker thread pool with wall clock timeouts and
backoff ran a 12-task scenario with 8 succeeded, 2 failed, and
2 blocked, at cost 34 over 13 attempts and 39 tests in total. At
Deep level, on one designed 11-task scenario in 4 waves with 9
tasks executed per strategy, all_small cost 18 units with 4
quality passes and 5 fails, all_large cost 45 units with 9
passes and 0 fails, and routed cost 35 units with 9 passes, 0
fails, and 1 escalation, saving 10 units (22.2 percent of 45) at
the same pass count as all_large. Approvals were 2 requested, 1
granted, and 1 rejected in every strategy, with 1 task rejected
and 1 blocked. The stack ships with 65 unit tests. The scenario
is synthetic, the workers are toy functions, quality is a table,
and the single escalation comes from one task underestimated on
purpose; the paper claims the routing and escalation method and
its measured arithmetic on this scenario, including the cost
condition under which routing stops saving, not performance on
real models.

## Method outline

1. Graph layer: tasks with id, dependencies, cost, step count,
   and step budget, validated before any run (duplicate ids,
   unknown dependencies, and bad fields raise a named error).
   Waves are topological levels.
2. Learn execution: wave by wave in sorted order, one retry for
   a deterministic flaky failure, step budget failures never
   retried, and transitive blocking for dependents of a failed
   or blocked task.
3. Build execution: one attempt round per wave on a
   ThreadPoolExecutor with 4 workers, a wall clock timeout per
   attempt counted from submit time, retries with backoff (0.01
   seconds, then 0.02 seconds) for transient failures and
   timeouts only, and a trace merged in topological order.
4. Tiers and quality table: small costs 2 and scores 0.95, 0.90,
   0.70, 0.55, 0.40 at true difficulty 1 to 5; large costs 5 and
   scores 0.98, 0.97, 0.95, 0.92, 0.88. The threshold is 0.80.
5. Routing: the routed strategy sees estimated difficulty only.
   At most 2 routes to small, above 2 routes to large. A small
   output below 0.80 escalates once to large, charged on top.
6. Approval gates: a task flagged requires_approval pauses for
   the approver callback before routing. The runner approver is
   simulated and rejects D09 only, so D09 is rejected and its
   dependent D10 is blocked.
7. Designed scenario: 11 tasks in 4 waves, with D07
   underestimated on purpose (estimated 1, true 3) as the single
   designed estimation error, and D08 and D09 as approval tasks.
8. Scoring: cost, quality passes and fails, escalations,
   approvals, and blocked counts per strategy, checked against
   hand arithmetic in the Deep README.

## Results table

Measured 2026-11-05, synthetic data only, from the level READMEs
in the repo.

| Level | Set | Headline result | Cost and steps | Tests |
| --- | --- | --- | --- | --- |
| Learn | 10 tasks, 4 waves | 8 succeeded, 1 failed, 1 blocked | Cost 28, 13 steps, 11 trace entries | 19 |
| Build | 12 tasks, 4 waves, 4 workers | 8 succeeded, 2 failed, 2 blocked | Cost 34, 13 steps, backoff 0.04 seconds | 20 (39 total) |
| Deep, all_small | 11 tasks, 9 executed | 4 quality passes, 5 fails, 0 escalations | Cost 18 | 26 Deep (65 total) |
| Deep, all_large | 11 tasks, 9 executed | 9 quality passes, 0 fails, 0 escalations | Cost 45 | 26 Deep (65 total) |
| Deep, routed | 11 tasks, 9 executed | 9 quality passes, 0 fails, 1 escalation (D07) | Cost 35, saves 10 (22.2 percent of 45) | 26 Deep (65 total) |

## Venue class note

Per SPEC.md, the paper angle for P08 is a cost and quality
routing study (small model against large model per step, quality
held, cost cut, one table). This brief is the toy-tier form of
that study, stated as such: the tiers are deterministic toy
functions, not small and large models, and that gap is the first
limit the paper must carry. Venue class is a workshop or
conference in ML systems or agent engineering, or a journal of
the AJSE class, per the publications pipeline tracker rules.
One venue at a time. No venue is named as submitted, accepted,
or contacted in this brief. Fees, if any, arise only after
acceptance and remain Jesun's call under the free-only rule.

## Limits the paper must carry

- Toy workers only. No real model, real agent, or real task
  content was measured at any level.
- Quality is a fixed table by tier and true difficulty, not a
  measured signal. A real router needs calibration first.
- One designed scenario per level. The Deep saving is measured
  on one 11-task graph with one designed estimation error.
- The escalation is designed, not discovered. A higher error
  rate pushes routed cost toward or past all_large, because an
  escalated task costs 7 against 5 direct to large.
- The approver is simulated, with no human, interface,
  persistence, or appeal path.
- Deep execution is sequential, so routing under parallel load
  is unmeasured. Cost is a unit count, not money or tokens.
- Compressed Deep only. The v1.1 backlog (real model workers,
  measured quality, learned routing, parallel routed execution,
  a real approval surface) is future work, named in ROADMAP.md.

## Submission gate

Submission is Jesun's tap and nothing is submitted. This brief is
the candidate only.
