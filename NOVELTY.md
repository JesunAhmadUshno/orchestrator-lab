# NOVELTY: orchestrator-lab (P08)

Status: DRAFT, PROPOSED. Not verified. This text does not move into any public post, paper, or profile until the Jev claim_check gate passes on the exact text.

## Proposed claim

Against workflow engines and framework multi-agent demos: this project aims to differ in the way its SPEC.md section text defines (a from-zero or self-hosted build, measured in public, on a named home fleet, with the failure modes written down). The exact difference is stated at the project's wave, after the prior art is re-read.

## Prior art table

| Prior art | What it does | What this project does differently | Measured difference |
| --- | --- | --- | --- |
| workflow engines and framework multi-agent demos | See DOSSIER.md, Past | A dependency-free, deterministic supervisor whose cost, quality, approval and blocking decisions are all recorded in a byte-identical trace | Measured on the toy table only (level-3-deep/results_deep.json): routed 35 cost units with 9 of 9 quality passes, all_large 45 with 9, all_small 18 with 4. Sensitivity in level-3-deep/results_sweep.json. No comparison against any other system was run. |
| cost-quality cascades and model routers (try a cheap model, escalate on a quality check) | Not yet surveyed with dated sources; DOSSIER.md Past has none | Same cascade idea, reproduced without models: an estimate-based router, one escalation, and approval gates with transitive blocking | NONE: no real models, so no comparison with published cascade or router results is possible here |

## Honest size

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
