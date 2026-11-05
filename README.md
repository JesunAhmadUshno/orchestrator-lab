# orchestrator-lab

Multi-agent orchestration: one supervisor, a task graph, parallel workers, cost and quality routing.

Status: Learn DONE (2026-11-05, ROADMAP-V3-BATCH). Level 1 is built, tested, and measured below. Build and Deep are not started.
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

## Novelty

PROPOSED. See NOVELTY.md. The novelty text is a draft until the Jev claim_check gate passes on it.

## License

Code: Apache-2.0 (see LICENSE). Tutorials: CC BY 4.0. Ruled in D-V3-11, 2026-11-04.
