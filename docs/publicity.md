# Publicity log: orchestrator-lab (P08)

Moved from PUBLICITY.md on 2026-11-08. Grades and the publicity rubric
scores were removed (grades are internal).

Publicity log under the documentation and publishing standard,
Section 7. Every finished level produces its written fan-out set.
Drafts are prepared by the loop. Actual social posting follows
the standing platform rules and gates. The loop itself never posts
to social.

Fan-out set date: 2026-11-05. Project state: v1.0, Learn, Build,
and compressed Deep done 2026-11-05, 65 tests passing. Deep detail: one designed 11-task scenario
in 4 waves, 9 tasks executed per strategy: all_small cost 18 with
4 quality passes and 5 fails; all_large cost 45 with 9 passes and
0 fails; routed cost 35 with 9 passes, 0 fails, and 1 escalation
(D07), saves 10 units (22.2 percent of 45) at the same 9 passes;
approvals 2 requested, 1 granted, 1 rejected, 1 task rejected
and 1 blocked. All workers are deterministic toy functions, the
quality scores are a fixed table, scenarios are synthetic, Deep
execution is sequential, and the approver is simulated. No real
LLM was called at any level.

## Channel log (2026-11-05)

| Channel | Outcome on 2026-11-05 |
| --- | --- |
| GitHub releases | Live: v0.1 https://github.com/JesunAhmadUshno/orchestrator-lab/releases/tag/v0.1 , v0.5 https://github.com/JesunAhmadUshno/orchestrator-lab/releases/tag/v0.5 , v1.0 https://github.com/JesunAhmadUshno/orchestrator-lab/releases/tag/v1.0 (verified with gh release list, 2026-11-05). Draft release notes for all three are in fanout/release-notes.md. No new release was created for the fan-out. |
| Portfolio index | Held: fan-out links are ready, the index update is a coordinator step outside this cycle. Named reason: held for coordinator refresh. |
| Website page | Draft in fanout/website-page.md. Held: not published to jesunahmadushno.com. |
| Blog | Draft in fanout/blog-post.md. Held: not posted. |
| Tutorial | In repo: fanout/tutorial.md. Every command in it was run and verified on 2026-11-05 (three runners, full suite at 65 tests, scaffold smoke test). |
| LinkedIn post | Draft in fanout/linkedin-post.md, marked DRAFT NOT POSTED, link carried as the first-comment line per the LinkedIn rule. Held: not posted, loop never posts. |
| X | Draft held: no X copy is shipped in this set beyond the LinkedIn draft source text. Held under the standing social rules; posting is outside the loop. |
| Facebook | Draft held: no Facebook copy posted. Standing rule applies (no link in body or comments, keyword call to action fulfilled by DM). Held: not posted, loop never posts. |
| Instagram | Draft held: no Instagram copy posted. Standing rule applies (no clickable link in caption, link in bio). Held: not posted, loop never posts. |
| Threads | Draft held: no Threads copy posted. Threads waits for Jesun's tap per post, hash-locked on exact text and media. Held: awaiting Jesun's tap. |
| Video | Held: engine queue, January production for lab projects per the December Compression Protocol. No video was produced in this cycle. |
| Book chapter | Draft angle in fanout/blog-post.md and SPEC.md ("Many Hands, One Graph"). Held: chapter draft follows the finished project set; not a published chapter. |
| Paper candidate | Draft brief in fanout/paper-candidate.md (cost and quality routing study, toy-tier form). Submission is Jesun's tap. Nothing submitted, no venue contacted. The publications tracker is updated by the coordinator, not by this cycle. |

## Jev gate (2026-11-05)

claim_check on the blog main results paragraph, extracted
byte-exact from fanout/blog-post.md by script. Spec:
hidden_files/jev-p08-fanout-claim-spec-2026-11-05.json in the goal
workspace. Results:
hidden_files/jev-p08-fanout-claim-results-2026-11-05.json. Model
jev-1.13.0, question id supported, noul 0.68, route REVIEW (clear
at 0.85 or above, block at 0.10 or below, review between), input
tokens 1227, output tokens 20. Arithmetic was pre-computed in the
spec evidence (45 minus 35 is 10; 10 divided by 45 is 22.2
percent; 4 times 2 plus 4 times 5 plus 7 is 35; 19 plus 20 plus
26 is 65). No claim was blocked.
