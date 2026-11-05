# Tutorial: P08 orchestrator-lab, course module

Module: P08-orchestrator-lab
By Jesun Ahmad Ushno
Date: 2026-11-05
License for this tutorial: CC BY 4.0. Code in the repo: Apache-2.0.

## What you will do

You will clone the orchestrator-lab repo, run all three levels,
run the test suite for each level, and read your own results
against the recorded v1.0 numbers. Every command below exists in
the repo as shipped at v1.0 and was run by the author of this
module on 2026-11-05 to verify it. The project needs Python 3.11
or 3.12 and uses the standard library only. No model, no API, and
no credential are needed.

All workers are deterministic toy functions. They are not LLMs
and not real agents. In Deep, quality is a fixed table and the
approver is simulated. The numbers prove the graph, routing,
escalation, approval, and accounting machinery, not real model
quality.

## Step 0: Clone and enter the repo

```text
git clone https://github.com/JesunAhmadUshno/orchestrator-lab.git
cd orchestrator-lab
```

## Step 1: Level 1, Learn, supervisor and task graph

Read level-1-learn/README.md first. It explains the validated
task graph, dependency waves, one retry for a flaky task, the
step budget, and blocking.

Run the Learn runner:

```text
python3 level-1-learn/run_learn.py
```

Run the Learn tests:

```text
python3 -m unittest tests.test_learn_orchestrator -v
```

Run the scaffold smoke test:

```text
python3 tests/test_smoke.py
```

Read your results:

- Expected summary: 8 succeeded, 1 failed, 1 blocked of 10 tasks
  in 4 waves; cost 28, attempts 10, retries 1, steps 13, trace 11,
  status partial.
- Expected tests: 19 tests, all passing.
- Expected smoke test line: scaffold smoke test PASS.

## Step 2: Level 2, Build, parallel task graph

Read level-2-build/README.md. Build adds a 4-worker thread pool,
a wall clock timeout per attempt, retries with backoff, and a
deterministic trace.

Run the Build runner:

```text
python3 level-2-build/run_build.py
```

Run the Build tests:

```text
python3 -m unittest tests.test_build_orchestrator -v
```

Read your results:

- Expected summary: 8 succeeded, 2 failed, 2 blocked of 12 tasks
  in 4 waves; cost 34, attempts 13, retries 3, timeout attempts
  3, steps 13, trace 15, status partial.
- The console prints one observed wall clock line. It is not
  stored in the results file.
- Expected tests: 20 Build tests, all passing, 39 in total.

## Step 3: Level 3, Deep, routing and approval gates

Read level-3-deep/README.md. The router sees estimated
difficulty only. A small output below the 0.80 threshold
escalates once to large in the routed strategy only. Approval
tasks wait for the approver callback. The runner approver is
simulated and rejects D09 only.

Run the Deep runner:

```text
python3 level-3-deep/run_deep.py
```

Run the Deep tests:

```text
python3 -m unittest tests.test_deep_orchestrator -v
```

Read your results:

- Expected all_small: cost 18, quality pass 4, quality fail 5,
  escalations 0, succeeded 9, rejected 1, blocked 1.
- Expected all_large: cost 45, quality pass 9, quality fail 0,
  escalations 0, succeeded 9, rejected 1, blocked 1.
- Expected routed: cost 35, quality pass 9, quality fail 0,
  escalations 1, succeeded 9, rejected 1, blocked 1.
- Routed saves 10 units against all_large (45 to 35) at the same
  9 quality passes. That is 22.2 percent of 45.
- Expected tests: 26 Deep tests, all passing, 65 in total.

## Step 4: Run the full test suite

```text
python3 -m unittest discover -s tests -v
```

Expected: 65 tests in total (19 Learn, 20 Build, 26 Deep), all
passing, plus the scaffold smoke test.

## Step 5: Check your understanding

1. Why does a blocked task cost 0? (Answer: it is never attempted.
   Cost is charged per attempt, so no attempt means no cost, no
   steps, and one blocked entry in the trace.)
2. Why is D07 the only escalation in routed? (Answer: its
   estimate was set low on purpose, estimated 1 and true 3, so it
   starts on small, scores 0.70 below the 0.80 threshold, and
   escalates once to large, where it passes at 0.95 for a total
   cost of 7.)
3. Why does routed not always beat all_large? (Answer: an
   escalated task costs 7, more than 5 direct to large. A higher
   estimation error rate pushes routed cost toward or past
   all_large. The saving here is measured on one designed
   scenario with one designed error, not a general guarantee.)

## Limits to keep with the numbers

- Toy workers at every level, synthetic designed scenarios only.
- Deep quality is a fixed table, not measured model behaviour.
- The Deep approver is simulated, not a real human.
- Deep execution is sequential. Only Build uses a thread pool.
- Cost is a unit count, not money and not tokens.
