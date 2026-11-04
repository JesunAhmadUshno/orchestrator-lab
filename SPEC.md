# SPEC: orchestrator-lab (P08)

Phase skill: spec-driven-development (house engineering pipeline).
Status: Wave 0 scaffold spec, from Roadmap v2 text and the v3 decision pack. Scope and acceptance criteria below are the v2 section text, kept as the source of truth until the project's wave opens its own spec pass.

Fleet node: BlackBoxV2. Wave: Wave 4.
Hiring evidence: 4 of 5 (agents in 12/56, multi-agent in Amazon duties) [confirmed, fleet and scoring pass 2026-11-04, or the decision pack for P23 to P29].

## Project section text (Roadmap v2, or the v3 candidate text for P23 to P29)

orchestrator-lab: KEEP

Subject: multi-agent orchestration. v1 levels carry over: one supervisor that splits a task and assigns workers; a task graph with parallel workers, retries, timeouts; Deep adds cost and quality routing, human approval gates, full run traces.
Repo note: the archived fork Azure-ai-foundry-erp-swarm is a reading reference for this project, not a seed (Section 8).
Fan-out: Book chapter "Many Hands, One Graph". Paper angle: a cost and quality routing study (small model against large model per step, quality held, cost cut, one table). Course module: P08-orchestrator-lab.

## Acceptance criteria (scaffold level)

- Learn closes when the level-1-learn code runs, its README teaches the idea, and a fresh-eyes reader can follow it.
- Build closes when the system runs end to end, tests pass, and one benchmark or result table with method is in the README.
- Deep closes when the Deep scope in the section text is done, the failure modes are written, and the dossier is updated to ship state.
- No level closes on a claim. Evidence only: code, tests, numbers, links.
