# ROADMAP: orchestrator-lab (P08)

Status: v1.0 shipped 2026-11-05 (Learn, Build, and compressed
Deep). This file names the remaining v2 Deep scope as the
v1.1 backlog. Nothing below is built or claimed as done.

## v1.1 backlog (remaining v2 Deep scope)

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

## Out of scope until Jesun rules otherwise

- Any paid model API or new credential.
- Any claim about real model quality from the toy table in
  the v1.0 Deep level.
