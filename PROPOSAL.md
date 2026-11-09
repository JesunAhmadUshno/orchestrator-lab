# PROPOSAL: orchestrator-lab (P08)

Status: NOT PRE-REGISTERED. This file gathers the plans as they were
committed. SPEC.md (2026-11-04, commit c6e43b4) came before any code,
but it holds scope and acceptance criteria only: no hypothesis, no
numeric pass line and no analysis plan. The Build and Deep specs
(BUILD-SPEC and DEEP-SPEC, now in REPORT.md) were committed in the same
commits as the code and results they describe (2e307b9, 11e5ef9). So no
tag proposal-v1 is placed, and the repo is capped at Functional until a
locked confirmatory cycle (see "Next cycle") lifts the cap. Assembled on
2026-11-08 from SPEC.md, NOVELTY.md, DOSSIER.md and ROADMAP.md, whose
text follows unchanged apart from the removal of grades and internal
scores.

## Question

When one supervisor coordinates many workers over a task graph, does
routing each task to a cheap or an expensive tier by estimated
difficulty, with one escalation on a failed quality check, keep quality
at lower cost than always using the expensive tier, and how do approval
gates and failures propagate through the graph? (Stated at migration,
2026-11-08; the research review of 2026-11-07 named it as the implicit
question that was never written down.)

Boundary: P08 is many agents coordinated; P07 is one agent's internals.

## Next cycle (what would lift the cap)

Lock a PROPOSAL with hypotheses and numeric pass lines (for example:
routed keeps the quality pass rate within 2 points of all_large at under
80 percent of its cost) before any run with real model tiers, a
measured quality signal and a labelled task set written before the run.
That needs GPU time on a fleet node or a paid API, so it waits for the
Owner. The open work list follows, moved from ROADMAP.md.

### Open work (moved from ROADMAP.md, v1.1 backlog; nothing here is built)

- Real model workers: replace the deterministic toy workers
  with real small and large model calls behind the same tier
  interface, with license and cost per call recorded.
- Measured quality signal: replace the fixed quality table
  with a measured checker (held out cases, a judge, or human
  labels), with calibration reported before any routing claim
  is made on real data.
- Learned and multi-signal routing: route on more than one
  estimated difficulty field, for example payload size, task
  type, and past per-worker pass rates, and report where the
  learned router beats the single threshold rule.
- Parallel routed execution: combine the Build thread pool
  with Deep routing, escalation, and approval gates, while
  keeping traces deterministic and timing independent.
- Real human approval surface: a persistent approval queue
  with a user interface, an appeal or override path, timeouts
  on pending approvals, and an audit log of who decided what.
- More scenarios and scale: larger graphs, adversarial
  estimation error rates, graphs where the large tier can
  also fail the quality threshold, and a second escalation or
  fallback policy for that case.
- Latency and dollar cost: measure wall clock and real token
  or dollar cost per strategy, not unit counts only.
- Fleet run: repeat the full comparison on BlackBoxV2, the
  assigned fleet node, and record the run there.

### Out of scope until Jesun rules otherwise

- Any paid model API or new credential.
- Any claim about real model quality from the toy table in
  the v1.0 Deep level.

## SPEC (from SPEC.md, 2026-11-04, commit c6e43b4)

Phase skill: spec-driven-development (house engineering pipeline).
Status: Wave 0 scaffold spec, from Roadmap v2 text and the v3 decision pack. Scope and acceptance criteria below are the v2 section text, kept as the source of truth until the project's wave opens its own spec pass.

Fleet node: BlackBoxV2. Wave: Wave 4.
Hiring evidence: agents and multi-agent work appear in the target job descriptions (scored internally, 2026-11-04).

### Project section text (Roadmap v2, or the v3 candidate text for P23 to P29)

orchestrator-lab: KEEP

Subject: multi-agent orchestration. v1 levels carry over: one supervisor that splits a task and assigns workers; a task graph with parallel workers, retries, timeouts; Deep adds cost and quality routing, human approval gates, full run traces.
Repo note: the archived fork Azure-ai-foundry-erp-swarm is a reading reference for this project, not a seed (Section 8).
Fan-out: Book chapter "Many Hands, One Graph". Paper angle: a cost and quality routing study (small model against large model per step, quality held, cost cut, one table). Course module: P08-orchestrator-lab.

### Acceptance criteria (scaffold level)

- Learn closes when the level-1-learn code runs, its README teaches the idea, and a fresh-eyes reader can follow it.
- Build closes when the system runs end to end, tests pass, and one benchmark or result table with method is in the README.
- Deep closes when the Deep scope in the section text is done, the failure modes are written, and the dossier is updated to ship state.
- No level closes on a claim. Evidence only: code, tests, numbers, links.

## Novelty (from NOVELTY.md, last changed 2026-11-07)

Status: DRAFT, PROPOSED. Not verified. This text does not move into any public post, paper, or profile until the Jev claim_check gate passes on the exact text.

### Proposed claim

Against workflow engines and framework multi-agent demos: this project aims to differ in the way its SPEC.md section text defines (a from-zero or self-hosted build, measured in public, on a named home fleet, with the failure modes written down). The exact difference is stated at the project's wave, after the prior art is re-read.

### Prior art table

| Prior art | What it does | What this project does differently | Measured difference |
| --- | --- | --- | --- |
| workflow engines and framework multi-agent demos | See DOSSIER.md, Past | A dependency-free, deterministic supervisor whose cost, quality, approval and blocking decisions are all recorded in a byte-identical trace | Measured on the toy table only (level-3-deep/results_deep.json): routed 35 cost units with 9 of 9 quality passes, all_large 45 with 9, all_small 18 with 4. Sensitivity in level-3-deep/results_sweep.json. No comparison against any other system was run. |
| cost-quality cascades and model routers (try a cheap model, escalate on a quality check) | Not yet surveyed with dated sources; DOSSIER.md Past has none | Same cascade idea, reproduced without models: an estimate-based router, one escalation, and approval gates with transitive blocking | NONE: no real models, so no comparison with published cascade or router results is possible here |

### Honest size

Measured 2026-11-07: the novelty is small. Routing cheap-first with
one escalation on a failed quality check is an established cascade
idea; this repo does not beat or even compare against prior work.
The real value is a clean, standard-library, fully deterministic
reproduction of cost and quality routing with approval gates, a
complete decision trace, an exhaustive estimation-error sweep on its
own scenario, and a browser port checked against the Python results
on every build. No citation is added here until it has been read and
verified.

If the novelty proves small, this file will say so and name the real value instead (a cleaner reproduction, a better benchmark, a first public dataset). No novelty is invented to fill this section.

## Background: past, present, future (from DOSSIER.md, 2026-11-05)

Written under the documentation and publishing standard (past, present, future). Updated at ship time.

### Past

Prior art for this project is named in NOVELTY.md (workflow engines and framework multi-agent demos). The history of the problem, the key papers and systems, and what was tried before are recorded in the Roadmap v2 section text in SPEC.md and will be expanded with dated sources at the project's wave, before Build opens.

### Present

Current demand evidence: agents and multi-agent work appear in the target job descriptions (scored internally, 2026-11-04). The Round 3 research (2026-11-04) found the market centre at post-training, evals, environments, and inference depth [confirmed as the research finding; the report is at ~/workspace/research_notes/roadmap-v3-revaluation-research-20261104-0949/report.md]. Tools and versions are pinned at Build time, not in this v1.

Shipped state (2026-11-05, v1.0): Learn v0.1, Build v0.5, and Deep v1.0 are built, tested, and measured. Learn: a wave supervisor with retries, a step budget, and blocked tasks (19 tests). Build: a 12-task parallel pipeline on a thread pool with retries, wall clock timeouts, and backoff (20 Build tests). Deep: cost and quality routing over two deterministic toy tiers, one escalation on a failed quality check, human approval gates with a simulated approver, full run traces, and a three strategy comparison on an 11-task scenario (26 Deep tests). In the Deep comparison, routed cost 35 units with 9 of 9 executed tasks passing the 0.80 quality threshold and 1 escalation, against all_large at 45 units with 9 passes and all_small at 18 units with 4 passes and 5 quality fails, with 2 approvals requested, 1 granted, and 1 rejected in every strategy. Total tests: 65 plus the scaffold smoke test. All levels were run on the Muse VM, not on the assigned fleet node BlackBoxV2. Workers are deterministic toy functions, not LLMs, at every level.

### Future

The remaining v2 Deep scope is the next cycle below: real model workers, a measured quality signal, learned routing, parallel routed execution, a real human approval surface, more scenarios, latency and dollar cost, and a fleet run on BlackBoxV2. Any forecast about this field is [unverified] unless a dated primary source is added here.
