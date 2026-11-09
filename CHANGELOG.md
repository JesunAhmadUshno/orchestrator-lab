# Changelog

All notable changes to this project. Format: Keep a Changelog 1.1.
Versions follow Semantic Versioning. The tags v0.1, v0.5 and v1.0 are
the Learn, Build and Deep releases of 2026-11-05, made before the
portfolio standard v2; they are not a "v1.0 Released" verdict under it.

## [Unreleased]

### Changed
- 2026-11-08: Adopted the portfolio standard v2. README is the abstract
  (question, headline, field, job family, verdict: Functional, not
  pre-registered). PROPOSAL.md gathers SPEC.md, NOVELTY.md, DOSSIER.md
  and the ROADMAP.md backlog; REPORT.md gathers the three level READMEs,
  the benchmark table and the research review, and scores five post hoc
  hypotheses with the misses shown. PUBLICITY.md moved to
  docs/publicity.md. Grades left every public file, including the fan-out
  drafts and the dashboard. Stage folders kept (decision 0001).
- 2026-11-08: CI runs on Python 3.11 and 3.12 with read-only
  permissions, checks the repo layout and that no grade is public, and
  re-runs every runner, failing if any committed results file changes.
  CodeQL (Python, JavaScript) and Dependabot (GitHub Actions, npm) added.
- 2026-11-08: The dashboard reads REPORT.md, PROPOSAL.md and the README
  verdict instead of the removed files, and shows the verdict in place
  of the self-assessed grade.

## [1.0] - 2026-11-05 (tag v1.0), with additions to 2026-11-07

### Added
- 2026-11-07: Graph task, wave and strategy counts derived from the
  recorded run data on the dashboard; vite pinned to 6.4.5.
- 2026-11-07: Live dashboard on GitHub Pages with an in-browser router
  and sweep, held to the Python results by a build-time parity check.
- 2026-11-07: Estimation-error, quality threshold, large tier cost and
  routing cutoff sweeps (level-3-deep/sweep_deep.py,
  results_sweep.json); the routing cutoff became a parameter (default
  unchanged); the Deep scenario exported as scenario_deep.json; 10 new
  tests (75 in total).
- 2026-11-07: CI runs the full unit test suite on every push.
- 2026-11-07: Research review and an honest-size statement of the
  novelty.
- 2026-11-05: Written fan-out set (blog, tutorial, page, post, paper
  brief, release notes) in fanout/.
- 2026-11-05: Deep: cost and quality routing over two toy tiers, one
  escalation on a failed quality check, approval gates with a simulated
  approver, full traces, a three-strategy comparison (26 tests, 65 in
  total).

## [0.5] - 2026-11-05 (tag v0.5)

### Added
- Build: a 12-task parallel task graph on a 4-worker thread pool with
  wall clock timeouts, retries with backoff and transitive blocking
  (20 tests, 39 in total).

## [0.1] - 2026-11-05 (tag v0.1)

### Added
- Learn: a wave supervisor with retries, a step budget, blocked tasks
  and a full trace (19 tests).
- 2026-11-04: Scaffold: SPEC.md, DOSSIER.md, NOVELTY.md, level folders,
  smoke test, CI.
