# Lessons from the autonomous worker test and deployment

Scope: review what this session actually tested and how the assistant helped Aki test it. This is a retrospective on achiCore #153 / PR #154, not a completed second code review. The [deployment record](http://100.106.210.38:8999/Code/GitHub/achiCore/docs/issue-153-deployment.md) records the tested head `05cd66c`, deployment `bbb8fb7`, commands and acceptance limits.

## What the evidence supports

The canonical suite passed twice at `05cd66c`, once plainly and once with `ACHICORE_AGENT=aea1`: 1391 passed, 1 existing skip, 2 warnings and 21 subtests in each run. Mutation checks made the checkpoint, reservation, marker/hook and cache regression selections fail with fixes removed and pass after restoration. Some selections tested grouped changes, so this does not establish independent causal coverage of every edit.

The named process-group regression still passed after restoring the old SID condition. It therefore did not detect that regression. A separate real subprocess check with process group distinct from session, and a reused-PID guard check, passed. The separate deleted-virtualenv case failed: a cached successful probe survived deletion. That defect is achiCore #156.

Aki used his real Telegram account to bind Atlas, start jobs and report outcomes. The staging store has five completed jobs and one abandoned job. It also shows review cycles increasing after branch preparation and UNKNOWN mergeability parks. Aki reported stale Atlas progress and wanted separate conflict attempts and a visible merge queue. Those changes are achiCore #155. They are not part of the deployed implementation.

## Lessons to carry forward

| Observation | Lesson | Change in the assisted testing procedure |
|---|---|---|
| The first opus-subagents jobs parked with zero calls because a runner was missing. | Check actual repository prerequisites before asking for phone actions. | Prepare and probe each required worker environment before human acceptance. Preserve a failed baseline. |
| Adding the runner exposed Linux fixture failures; fixing the environment allowed the useful tests to proceed. | Distinguish setup defects, repository failures and candidate regressions. | Record the original failure, authorized fix and rerun, without attributing everything to the PR. |
| Aki could follow commands and report bot replies while the assistant inspected state. | Human guidance works best when paired with observation. | Give one exact action, wait for its result and correlate logs or IDs before continuing. |
| Six jobs existed, but some completed before later jobs started. | Eventual completion does not prove concurrency. | Require overlapping intervals and distinct resources for a concurrency criterion. |
| Flash exercised the product but not the requested three-engine matrix. | A cheaper model changes coverage when the engine is part of the feature. | Record actual engines and leave omitted engine gates open. |
| One mutation test passed with the bug restored. | A green regression may not distinguish the fix. | Use a discriminating trigger and retain the failed mutation check as a limitation. |
| A successful environment receipt survived deletion of the virtualenv. | Receipts have validity conditions beyond their text. | Recheck the environment before paid work and track invalidation defects explicitly. |
| Atlas did not show repair progress or repository merge waiting. | Correct background execution still needs observable progress. | Test status text and waiting states as acceptance behavior, not optional polish. |
| New merge preparation consumed coding review cycles. | Infrastructure repair needs its own bounded budget. | Test a conflict after the coding budget is exhausted, including persisted counters. |
| Aki explicitly chose deployment before every original gate was complete. | A shipping decision and complete acceptance are separate facts. | Record the decision, remaining gates and follow-up issues without rewriting evidence. |

## What should have been better in this session

The assistant should have completed repository and provider preflight before sending the six-job instructions. It should have maintained the concurrency timeline while jobs were active instead of inferring coverage afterwards. The requested independent audit and formal review were not completed before Aki redirected the work to deployment; the result must remain a partial audit. UNKNOWN mergeability was not evidence of a confirmed conflict until later Git or GitHub observations established it.

The first merge command was refused because the PR was still a draft. Checking `isDraft` with head, CI and approval would have avoided that failed operation. The deployment did preserve unrelated edits and stop the idle daemon before backing up state and restarting it. Future rollback preparation should inventory every state and engine-home path the candidate may migrate, rather than assume the job store backup covers them all.

The documentation update also needs precise validation claims: it checked the new references and preserved existing code fences; it was not a full Markdown parser or independent audit of all historical prose.

## Reusable result and next work

The [assisted-live-testing skill](http://100.106.210.38:8999/.config/skillshare/skills/assisted-live-testing/SKILL.md) captures the human/assistant procedure without creating a permanent agent. It produces the interaction record and PR comment Aki requested. The Telegram instructions are one environment-specific reference; CLI and backend testing use the same loop.

The next Astra workstream is the self-learning loop. Start with AIS-OS #13 for stable task/Calendar operations and achiCore #56 for persona/memory precedence, then connect ordinary input through achiCore #148 and correction reuse through AIS-OS #14. Prepare AIS-OS #18's replay fixtures early; its live release gates still depend on the downstream integrations. Keep #155/#156 open alongside this work. This retrospective does not implement learning or automatically publish a learned rule.
