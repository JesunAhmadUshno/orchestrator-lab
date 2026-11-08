# LinkedIn post draft: P08 orchestrator-lab v1.0

Status: DRAFT NOT POSTED
Date drafted: 2026-11-05
Author: Jesun Ahmad Ushno
Rule for this platform: the link goes in the first comment, not in the
post body. The first comment line is at the end of this file.

## Post body

One supervisor, one task graph, and a routing rule you can check
by hand. I built orchestrator-lab in the open, and labelled every
toy and simulated part as what it is.

orchestrator-lab v1.0 is done: Learn, Build, and a compressed
Deep, Python standard library only. The workers are deterministic
toy functions at every level, not LLMs and not real agents.

Learn: a validated task graph in dependency waves, one retry for
a flaky task, a step budget, and blocking. On a 10-task scenario:
8 succeeded, 1 failed on the step budget, 1 blocked, cost 28 over
10 attempts, 13 steps. 19 tests.

Build: the same graph on a 4-worker thread pool, with a wall
clock timeout per attempt and backoff. On a 12-task scenario:
8 succeeded, 2 failed (one timeout after 3 attempts, one step
budget), 2 blocked, cost 34 over 13 attempts, backoff 0.04
seconds in total. 39 tests in total.

Deep (compressed): routing by estimated difficulty, one
escalation on a failed quality check, and approval gates. On one
designed 11-task scenario with 9 tasks executed per strategy:
all_small cost 18 with 4 quality passes and 5 fails; all_large
cost 45 with 9 passes; routed cost 35 with 9 passes, 0 fails,
and 1 escalation. Routed saves 10 units, 22.2 percent of 45, at
the same 9 passes. Approvals: 2 requested, 1 granted, 1
rejected, with 1 task rejected and 1 blocked. 65 tests in total.
Limits named in the repo.

The honest limits, in the post and not in a footnote: toy
workers only; synthetic designed scenarios only; Deep quality
is a fixed table, not measured model behaviour; the single
escalation was designed by underestimating one task on purpose;
the approver is simulated, not a real human; Deep runs
sequentially; and cost is a unit count, not money or tokens.
The rest of the Deep scope is named as the v1.1 backlog in the
repo, not claimed as done.

If you run multi-agent systems: where does your routing rule
fail first, on a bad estimate, a bad quality signal, or a gate
nobody answers?

## First comment (post this as the first comment, per the standing rule)

Repo, releases v0.1, v0.5, and v1.0, and the full tutorial: https://github.com/JesunAhmadUshno/orchestrator-lab
