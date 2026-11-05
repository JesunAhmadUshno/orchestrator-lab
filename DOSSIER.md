# DOSSIER: orchestrator-lab (P08) ship state, 2026-11-05

Written under the documentation and publishing standard (past, present, future). Updated at ship time.

## Past

Prior art for this project is named in NOVELTY.md (workflow engines and framework multi-agent demos). The history of the problem, the key papers and systems, and what was tried before are recorded in the Roadmap v2 section text in SPEC.md and will be expanded with dated sources at the project's wave, before Build opens.

## Present

Current demand evidence: hiring value 4 of 5 (agents in 12/56, multi-agent in Amazon duties) [confirmed, fleet and scoring pass 2026-11-04; for P23 to P29, the decision pack 2026-11-04]. The Round 3 research (2026-11-04) found the market centre at post-training, evals, environments, and inference depth [confirmed as the research finding; the report is at ~/workspace/research_notes/roadmap-v3-revaluation-research-20261104-0949/report.md]. Tools and versions are pinned at Build time, not in this v1.

Shipped state (2026-11-05, v1.0): Learn v0.1, Build v0.5, and Deep v1.0 are built, tested, and measured. Learn: a wave supervisor with retries, a step budget, and blocked tasks (19 tests). Build: a 12-task parallel pipeline on a thread pool with retries, wall clock timeouts, and backoff (20 Build tests, grade 8,600 of 10,000). Deep: cost and quality routing over two deterministic toy tiers, one escalation on a failed quality check, human approval gates with a simulated approver, full run traces, and a three strategy comparison on an 11-task scenario (26 Deep tests, grade 8,200 of 10,000). In the Deep comparison, routed cost 35 units with 9 of 9 executed tasks passing the 0.80 quality threshold and 1 escalation, against all_large at 45 units with 9 passes and all_small at 18 units with 4 passes and 5 quality fails, with 2 approvals requested, 1 granted, and 1 rejected in every strategy. Total tests: 65 plus the scaffold smoke test. All levels were run on the Muse VM, not on the assigned fleet node BlackBoxV2; that deduction is named in each level grade. Workers are deterministic toy functions, not LLMs, at every level.

## Future

The remaining v2 Deep scope is the v1.1 backlog in ROADMAP.md: real model workers, a measured quality signal, learned routing, parallel routed execution, a real human approval surface, more scenarios, latency and dollar cost, and a fleet run on BlackBoxV2. Any forecast about this field is [unverified] unless a dated primary source is added here.
