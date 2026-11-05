# orchestrator-lab

Multi-agent orchestration: one supervisor, a task graph, parallel workers, cost and quality routing.

Status: Learn and Build DONE (2026-11-05, ROADMAP-V3-BATCH). Levels 1 and 2 are built, tested, and measured below. Deep is not started.
Project: P08. Fleet node: BlackBoxV2. Wave: Wave 4. Learn was run on the Muse VM (CPU); see the level README for the named deduction.

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

## Novelty

PROPOSED. See NOVELTY.md. The novelty text is a draft until the Jev claim_check gate passes on it.

## License

Code: Apache-2.0 (see LICENSE). Tutorials: CC BY 4.0. Ruled in D-V3-11, 2026-11-04.
