# Release notes draft: orchestrator-lab

Status: DRAFT notes for releases that already exist. Dated 2026-11-05.
These notes summarise the existing GitHub releases. No new release is
created by this file.

Releases verified with gh release list on 2026-11-05:
v0.1, v0.5, and v1.0, at the URLs below.

## v0.1, Learn: supervisor and task graph

URL: https://github.com/JesunAhmadUshno/orchestrator-lab/releases/tag/v0.1

- A supervisor that holds a job as a validated task graph,
  computes dependency waves, and runs wave by wave in sorted
  order, with one retry for a flaky task, a step budget, and
  blocking for dependents of a failed task. Python standard
  library only. Workers are deterministic toy functions.
- Measured run: one 10-task scenario in 4 waves, 8 succeeded,
  1 failed (T08, step budget), 1 blocked (T09), total cost 28
  units over 10 attempts with 1 retry, 13 steps used, 11 trace
  entries, run status partial.
- Tests: 19 unit tests in tests/test_learn_orchestrator.py, plus
  the scaffold smoke test.
- Limits carried in the release: toy workers, one designed
  scenario, sequential execution inside waves, step budget only
  with no wall clock timeout, no routing and no approval gates.

## v0.5, Build: parallel task graph

URL: https://github.com/JesunAhmadUshno/orchestrator-lab/releases/tag/v0.5

- A real thread pool execution of the graph: a 4-worker
  ThreadPoolExecutor per wave, a wall clock timeout per attempt,
  retries with exponential backoff for transient failures and
  timeouts, and a deterministic trace merged in topological
  order. Workers sleep to simulate duration, then count words
  and characters. They are toy functions, not LLMs.
- Measured run: one 12-task scenario in 4 waves, 8 succeeded,
  2 failed (B07 wall clock timeout after 3 attempts, B08 step
  budget), 2 blocked, total cost 34 units over 13 attempts with
  3 retries and 3 timeout attempts, 13 steps used, backoff
  delays totalling 0.04 seconds, 15 trace entries.
- Tests: 20 Build unit tests, 39 in total with Learn, plus the
  scaffold smoke test.
- Limits carried in the release: toy workers, one designed
  scenario, a timed out thread can be abandoned but not killed,
  thread pool only, no routing and no approval gates.

## v1.0, Deep: cost and quality routing with approval gates

URL: https://github.com/JesunAhmadUshno/orchestrator-lab/releases/tag/v1.0

- Compressed Deep under the December Compression Protocol: cost
  and quality routing over two toy tiers (small cost 2, large
  cost 5), routing by estimated difficulty only, one escalation
  when a small output falls below the 0.80 quality threshold,
  approval gates with a simulated approver, and full run traces.
  Quality is a fixed table, execution is sequential, and the
  approver is simulated and labelled as such.
- Measured run: one designed 11-task scenario in 4 waves, 9
  tasks executed per strategy. all_small cost 18 with 4 quality
  passes and 5 fails; all_large cost 45 with 9 passes and 0
  fails; routed cost 35 with 9 passes, 0 fails, and 1 escalation
  (D07). Routed saves 10 units (22.2 percent of 45) at the same
  9 passes. Approvals in every strategy: 2 requested, 1 granted,
  1 rejected, with 1 task rejected and 1 blocked.
- Tests: 26 Deep unit tests, 65 in total with Learn and Build,
  plus the scaffold smoke test.
- The rest of the v2 Deep scope is the v1.1 backlog in ROADMAP.md.
  It is not part of v1.0 and is not claimed by these notes.
