# Website project page copy: orchestrator-lab

Site: jesunahmadushno.com
Status: COPY ONLY, draft for the project page. Dated 2026-11-05.
Nothing on any website was changed by this file.

## Headline

orchestrator-lab: one supervisor, a task graph, parallel workers, cost and quality routing, built in the open

## Summary

orchestrator-lab is an open multi-agent orchestration project
built by Jesun Ahmad Ushno as project P08 in Roadmap v3. It
builds the supervisor in three levels: a validated task graph
executed wave by wave with retries, a step budget, and blocked
tasks; a parallel pipeline on a 4-worker thread pool with wall
clock timeouts and backoff; and cost and quality routing over
two tiers with one escalation and approval gates. It runs on the
Python standard library only. The workers are deterministic toy
functions at every level, not LLMs and not real agents. Deep
quality is a fixed table, and the Deep approver is simulated.

Status: v1.0, 2026-11-05. Learn, Build, and compressed Deep are
done. Total tests: 65, all passing at v1.0. Level grades: Learn
8,700 of 10,000, Build 8,600 of 10,000, Deep 8,200 of 10,000.

## Results

All results below are measured runs on synthetic designed
scenarios, recorded in the level READMEs in the GitHub repo.
They prove the orchestration machinery, not real model quality.

| Level | Set | Headline result | Notes |
| --- | --- | --- | --- |
| Learn | 10 tasks in 4 waves | 8 succeeded, 1 failed, 1 blocked, cost 28 | T05 after 1 retry, T08 step budget, T09 blocked; 19 tests |
| Build | 12 tasks in 4 waves, 4-worker pool | 8 succeeded, 2 failed, 2 blocked, cost 34 | B07 timeout after 3 attempts, B08 step budget; backoff 0.04 seconds; 39 tests total |
| Deep (compressed) | 11 tasks in 4 waves, 9 executed per strategy | Routed cost 35 with 9 passes and 1 escalation, against all_large 45 with 9 passes and all_small 18 with 4 passes and 5 fails | Approvals 2 requested, 1 granted, 1 rejected; 1 rejected, 1 blocked; 65 tests total |

## Honest limits

- Toy workers and synthetic scenarios only, at every level.
- Deep quality is a fixed table, not measured model behaviour,
  and the Deep approver is simulated, not a real human.
- Deep execution is sequential. Only Build uses a thread pool.
- Cost is a unit count, not money and not tokens.
- Compressed Deep is not the full v2 Deep scope. The remainder
  is the v1.1 backlog in the repo ROADMAP.md.

## Links

- GitHub repo: https://github.com/JesunAhmadUshno/orchestrator-lab
- Release v0.1 (Learn): https://github.com/JesunAhmadUshno/orchestrator-lab/releases/tag/v0.1
- Release v0.5 (Build): https://github.com/JesunAhmadUshno/orchestrator-lab/releases/tag/v0.5
- Release v1.0 (Learn, Build, compressed Deep): https://github.com/JesunAhmadUshno/orchestrator-lab/releases/tag/v1.0
- Tutorial: fanout/tutorial.md in the GitHub repo
- Blog post draft: fanout/blog-post.md in the GitHub repo

## License note

Code: Apache-2.0. Tutorials: CC BY 4.0.
