# 0001: Keep the stage folders instead of src/, experiments/ and results/

Date: 2026-11-08. Status: accepted. Decided by: Jesun Ahmad Ushno.

## Context

The portfolio standard v2 lays a repo out as src/ (code), experiments/
(raw evidence) and results/ (scored results). This repo grew as three
stages, each a folder holding its own supervisor, its runner and the
results file the runner writes: level-1-learn/, level-2-build/ and
level-3-deep/. The live dashboard, the tests and the browser parity
check all import those paths.

## Decision

Keep the three stage folders under their names; the README layout table
maps each to its role. The scenarios are defined in the runners (stage
3 also exports level-3-deep/scenario_deep.json); the runs are
deterministic, so the results files are the evidence and are regenerated
byte for byte by one command, which CI checks. There is no separate
experiments/ folder, because there is no external raw evidence to keep.
The stage write-ups moved into REPORT.md.

## Consequences

No path breaks for the tests, the dashboard or the old release notes.
A reader finds code, scenario and result side by side per stage. If a
future cycle adds real model runs with non-deterministic output, their
raw records go into a new dated experiments/ folder and this decision
is revisited.
