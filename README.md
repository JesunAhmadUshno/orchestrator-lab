# orchestrator-lab

Multi-agent orchestration: one supervisor, a task graph, parallel workers, cost and quality routing.

Status: Learn, Build, and Deep DONE (2026-11-05, ROADMAP-V3-BATCH). All three levels are built, tested, and measured below. v1.0 shipped.
Project: P08. Fleet node: BlackBoxV2. Wave: Wave 4. All levels were run on the Muse VM (CPU); see the level READMEs for the named deduction.

## Start here

1. Read SPEC.md for scope and acceptance criteria.
2. Read DOSSIER.md for the past, present, and future of this problem (v1).
3. Read NOVELTY.md for the proposed novelty (DRAFT, pending the Jev claim_check gate).
4. Start at level-1-learn/README.md, then level-2-build, then level-3-deep.

## Level map

- Level 1, Learn: the core idea, built small and clean, with a teaching path.
- Level 2, Build: a real working system other people can run.
- Level 3, Deep: benchmarks, optimization, evaluation, hard cases.

## Benchmarks

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
| Deep grade | 8,200 of 10,000 (deductions in level-3-deep/README.md) |

## Deep

Deep adds cost and quality routing, human approval gates, and full run traces. The router sees estimated difficulty only: at most 2 routes to the small tier (cost 2), above 2 routes to the large tier (cost 5). A small tier output below the 0.80 quality threshold escalates once to the large tier, with the escalation recorded. Tasks flagged requires_approval are paused for an approver callback; the runner uses a deterministic simulated approver (labelled simulated, not a real human) that rejects D09 only, so D09 is rejected and its dependent D10 is blocked.

Main claim: Deep ran one deterministic 11-task scenario under three strategies on the Muse VM: routed cost 35 units with 9 of 9 executed tasks passing the 0.80 quality threshold and 1 escalation, against all_large at 45 units with 9 passes and all_small at 18 units with 4 passes and 5 quality fails; in every strategy 2 approvals were requested, 1 granted, 1 rejected, with 1 task rejected and 1 blocked, and 26 new Deep unit tests passing for 65 tests in total plus the scaffold smoke test.

The remaining v2 Deep scope is the v1.1 backlog in ROADMAP.md.

## Novelty

PROPOSED. See NOVELTY.md. The novelty text is a draft until the Jev claim_check gate passes on it.

## Fan-out

Written fan-out set for v1.0, dated 2026-11-05, in fanout/:

- fanout/blog-post.md: "Many Hands, One Graph", the full
  story with the main results claim gated by Jev claim_check
  (model jev-1.13.0, noul 0.68, route REVIEW, no block).
- fanout/tutorial.md: course module P08-orchestrator-lab. Every
  command in it was executed and passed on 2026-11-05 (all three
  runners, full suite at 65 tests).
- fanout/website-page.md: project page copy only, not published.
- fanout/linkedin-post.md: DRAFT NOT POSTED, link as the
  first-comment line per the LinkedIn rule.
- fanout/paper-candidate.md: cost and quality routing study at
  CANDIDATE. Submission is Jesun's tap, nothing submitted.
- fanout/release-notes.md: draft notes for the live releases
  v0.1, v0.5, and v1.0.

Publicity grades and the channel log are in PUBLICITY.md. Overall
fan-out grade: 9,533 of 10,000. The loop never posts to social:
all social channels are held with named reasons in PUBLICITY.md.

## License

Code: Apache-2.0 (see LICENSE). Tutorials: CC BY 4.0. Ruled in D-V3-11, 2026-11-04.
