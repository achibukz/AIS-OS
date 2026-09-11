# Astra implementation roadmap, September 11, 2026

This inventory includes all 43 open issues observed after publication in achibukz/achiCore and achibukz/AIS-OS. Existing unrelated tickets remain unchanged. The [plan](astra-plan.md) explains behavior; the [discussion](telegram-cohesion-discussion-2026-09-11.md) records Aki's decisions.

## Start here

[achiCore #56](https://github.com/achibukz/achiCore/issues/56) and [AIS-OS #6](https://github.com/achibukz/AIS-OS/issues/6) are completed. Next, prepare the small weekday and menu fixes ([AIS-OS #44](https://github.com/achibukz/AIS-OS/issues/44), [achiCore #194](https://github.com/achibukz/achiCore/issues/194)). Then complete the stable task/Calendar CLI ([AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13)) and captured-event path ([achiCore #197](https://github.com/achibukz/achiCore/issues/197)) before enabling automatic semantic learning.

Priority is a scheduling preference. Blocked by is a hard dispatch constraint. Parallel means separate owned worktrees and compatible file changes; it does not mean two PRs may replace the same staging daemon.

## Parallel lanes and joins

| Lane | Order | Can progress alongside | Landing caution |
|---|---|---|---|
| Personas | [x] | [achiCore #56](https://github.com/achibukz/achiCore/issues/56) then [achiCore #198](https://github.com/achibukz/achiCore/issues/198) | AIS-OS renderer and checklist work | Coordinate prompt/config edits with [achiCore #197](https://github.com/achibukz/achiCore/issues/197) |
| Task foundation | [x] | [AIS-OS #6](https://github.com/achibukz/AIS-OS/issues/6) then [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13) then [achiCore #148](https://github.com/achibukz/achiCore/issues/148) | Persona work until foreground joins it | Renderer changes also affect digests |
| Evidence | [achiCore #56](https://github.com/achibukz/achiCore/issues/56) then [achiCore #197](https://github.com/achibukz/achiCore/issues/197) | Task CLI work | Foreground waits for capture and CLI |
| Semantics | [ ] | [achiCore #148](https://github.com/achibukz/achiCore/issues/148) then [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14) | Completion and Canvas reconciliation after foreground | Daily learning must not duplicate the old writer |
| Persistence/notes | [ ] | [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13) then [AIS-OS #45](https://github.com/achibukz/AIS-OS/issues/45); notes join learning via [AIS-OS #15](https://github.com/achibukz/AIS-OS/issues/15) | Completion and incident work | Serialize writes by repository; preserve dirty work |
| Completion | [achiCore #148](https://github.com/achibukz/achiCore/issues/148) then [AIS-OS #11](https://github.com/achibukz/AIS-OS/issues/11) and [AIS-OS #47](https://github.com/achibukz/AIS-OS/issues/47) | Semantic preferences | Both use the same stable IDs and partial-operation contract |
| Recall | [ ] | [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14) plus [AIS-OS #15](https://github.com/achibukz/AIS-OS/issues/15) then [achiCore #149](https://github.com/achibukz/achiCore/issues/149) | Report work | Engine prompt changes need coordinated landing |
| Reports | [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14) plus [AIS-OS #11](https://github.com/achibukz/AIS-OS/issues/11) then [AIS-OS #16](https://github.com/achibukz/AIS-OS/issues/16) | Recall and Testing Grounds | Daily receipt at 3 AM; midnight remains separate |
| Incidents | [ ] | [achiCore #197](https://github.com/achibukz/achiCore/issues/197) then [AIS-OS #46](https://github.com/achibukz/AIS-OS/issues/46) | Preference work | Sanitize before public filing; no auto-dispatch |
| Testing | [ ] | [AIS-OS #20](https://github.com/achibukz/AIS-OS/issues/20) then [achiCore #199](https://github.com/achibukz/achiCore/issues/199) then [achiCore #200](https://github.com/achibukz/achiCore/issues/200) | Core learning lane | One live slot; land coordinator changes sequentially |
| Job recovery | [ ] | [achiCore #195](https://github.com/achibukz/achiCore/issues/195) and [achiCore #196](https://github.com/achibukz/achiCore/issues/196) | AIS-OS work | Coordinate with existing achiCore #155/#171 and HITL adapter |
| Daily UX | [ ] | [AIS-OS #44](https://github.com/achibukz/AIS-OS/issues/44), [AIS-OS #41](https://github.com/achibukz/AIS-OS/issues/41), [AIS-OS #42](https://github.com/achibukz/AIS-OS/issues/42), [achiCore #194](https://github.com/achibukz/achiCore/issues/194) | All core lanes | Broad brief redesign [AIS-OS #48](https://github.com/achibukz/AIS-OS/issues/48) waits for outcomes and incidents |
| Proof | Prepare [AIS-OS #18](https://github.com/achibukz/AIS-OS/issues/18) corpus early; run after listed blockers | All implementation lanes | Only observed real results satisfy activation |
| Later extension | [ ] | [AIS-OS #17](https://github.com/achibukz/AIS-OS/issues/17) after recall and conversation skills | Pilot preparation | Shared guidance still goes through review |

## Issue status checklist

Use this checklist to track completed issues as they ship across achiCore and AIS-OS.

### Published and revised implementation tickets (31)

- [x] [achiCore #56](https://github.com/achibukz/achiCore/issues/56): Make General Asa, give Sciel both vault topics, and enforce persona precedence
- [x] [AIS-OS #6](https://github.com/achibukz/AIS-OS/issues/6): Render all tasks by fixed area through one shared deterministic renderer
- [ ] [achiCore #194](https://github.com/achibukz/achiCore/issues/194): Expose existing /sync and /syncres commands in Telegram menus
- [ ] [AIS-OS #20](https://github.com/achibukz/AIS-OS/issues/20): Prepare copy-paste live-test checklists with expected results and resumable evidence
- [ ] [achiCore #195](https://github.com/achibukz/achiCore/issues/195): Change writer and reviewer models on a safely paused /ToWork job
- [ ] [achiCore #196](https://github.com/achibukz/achiCore/issues/196): Abandon jobs without losing dirty work and resume the same ticket through a new attempt
- [ ] [AIS-OS #41](https://github.com/achibukz/AIS-OS/issues/41): Include source links in concise email digests on every rendering path
- [ ] [AIS-OS #42](https://github.com/achibukz/AIS-OS/issues/42): Resolve Obsidian wikilinks natively in the Tailscale web viewer
- [ ] [AIS-OS #43](https://github.com/achibukz/AIS-OS/issues/43): Update agy-tickets for approved grilling decisions, dependency roadmaps and post-review HITL
- [ ] [achiCore #62](https://github.com/achibukz/achiCore/issues/62): Finish transactional binding and session rollback for /bind and /unbind
- [ ] [AIS-OS #44](https://github.com/achibukz/AIS-OS/issues/44): Compute tomorrow weekday in the morning brief from the Manila report date
- [ ] [AIS-OS #8](https://github.com/achibukz/AIS-OS/issues/8): Keep Calendar and email digest failures visible through shared Google health checks
- [ ] [achiCore #57](https://github.com/achibukz/achiCore/issues/57): Serve /tasks area views without a model turn and simplify /status
- [ ] [achiCore #197](https://github.com/achibukz/achiCore/issues/197): Capture Telegram conversations and execution outcomes durably for learning
- [ ] [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13): Reconcile task and Calendar intents with stable IDs and durable receipts
- [ ] [achiCore #198](https://github.com/achibukz/achiCore/issues/198): Load installed skills per conversation while keeping topic base skills scoped
- [ ] [achiCore #199](https://github.com/achibukz/achiCore/issues/199): Manage independent Testing Grounds cards and one isolated PR testing slot
- [ ] [achiCore #148](https://github.com/achibukz/achiCore/issues/148): Apply sourced reconciliation to ordinary Telegram requests and corrections
- [ ] [AIS-OS #45](https://github.com/achibukz/AIS-OS/issues/45): Commit and push owned task, log, note and writing updates automatically
- [ ] [achiCore #200](https://github.com/achibukz/achiCore/issues/200): Wait for Testing Grounds after Luna SHIP and route live-test results back to /ToWork
- [ ] [AIS-OS #46](https://github.com/achibukz/AIS-OS/issues/46): Group captured failures and automatically file actionable bug tickets with evidence
- [ ] [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14): Learn scoped semantic preferences immediately and consolidate daily at 3 AM Manila
- [ ] [AIS-OS #11](https://github.com/achibukz/AIS-OS/issues/11): Reconcile verified GitHub and personal completions into tasks and debriefs
- [ ] [AIS-OS #47](https://github.com/achibukz/AIS-OS/issues/47): Turn Canvas assignment events into linked tasks and reconcile later changes
- [ ] [AIS-OS #15](https://github.com/achibukz/AIS-OS/issues/15): Apply linked task outcomes and sourced notes through permitted Sciel vault operations
- [ ] [AIS-OS #16](https://github.com/achibukz/AIS-OS/issues/16): Deliver daily learning receipts and weekly evidence debriefs in achiNouncements
- [ ] [AIS-OS #48](https://github.com/achibukz/AIS-OS/issues/48): Make daily briefs concise, truthful and consistent with Manila reporting windows
- [ ] [achiCore #149](https://github.com/achibukz/achiCore/issues/149): Use current semantic preferences in warm turns and retire conflicting memory writers
- [ ] [AIS-OS #17](https://github.com/achibukz/AIS-OS/issues/17): Publish verified procedures through reviewed skill PRs and scoped discovery
- [ ] [AIS-OS #18](https://github.com/achibukz/AIS-OS/issues/18): Verify semantic learning with held-out requests and a recoverable Telegram pilot
- [ ] [AIS-OS #49](https://github.com/achibukz/AIS-OS/issues/49): Reproducible GitHub Actions regression CI

### Existing actionable backlog retained (12)

- [ ] [AIS-OS #24](https://github.com/achibukz/AIS-OS/issues/24): Canvas first-release epic
- [ ] [AIS-OS #31](https://github.com/achibukz/AIS-OS/issues/31): Canvas materials/cache/search follow-up
- [ ] [AIS-OS #34](https://github.com/achibukz/AIS-OS/issues/34): Shared sender split corruption
- [ ] [achiCore #9](https://github.com/achibukz/achiCore/issues/9): Atlas schedule and log paths live-discovery
- [ ] [achiCore #91](https://github.com/achibukz/achiCore/issues/91): Immich discussion/spike product investigation
- [ ] [achiCore #155](https://github.com/achibukz/achiCore/issues/155): Separate conflict budgets and merge-queue status
- [ ] [achiCore #156](https://github.com/achibukz/achiCore/issues/156): Worker virtualenv probe cache invalidation
- [ ] [achiCore #171](https://github.com/achibukz/achiCore/issues/171): Transient network fetch retry in standby
- [ ] [achiCore #172](https://github.com/achibukz/achiCore/issues/172): Complete delegated reports truncation-warning handling
- [ ] [achiCore #177](https://github.com/achibukz/achiCore/issues/177): Delegated streaming helper reuse
- [ ] [achiCore #185](https://github.com/achibukz/achiCore/issues/185): Final/live response separation UX defect
- [ ] [achiCore #186](https://github.com/achibukz/achiCore/issues/186): Effective Codex context capacity catalog/launcher defect

## Published and revised implementation tickets

All entries below are tracked with their completion status. AFK means unattended implementation, not permission to merge. Each issue contains explicit test cases and its human acceptance requirements. This batch has 15 revised existing issues and 16 new issues.

| Status | Ticket | Priority | Deliverable | Hard blockers | Verification gate |
|:---:|---|---|---|---|---|
| [achiCore #56](https://github.com/achibukz/achiCore/issues/56) | high | Make General Asa, give Sciel both vault topics, and enforce persona precedence | None | Automated + stated live acceptance |
| [AIS-OS #6](https://github.com/achibukz/AIS-OS/issues/6) | high | Render all tasks by fixed area through one shared deterministic renderer | None | Automated / author checks |
| [ ] | [achiCore #194](https://github.com/achibukz/achiCore/issues/194) | med | Expose existing /sync and /syncres commands in Telegram menus | None | Automated + stated live acceptance |
| [AIS-OS #20](https://github.com/achibukz/AIS-OS/issues/20) | high | Prepare copy-paste live-test checklists with expected results and resumable evidence | None | Automated + stated live acceptance |
| [achiCore #195](https://github.com/achibukz/achiCore/issues/195) | med | Change writer and reviewer models on a safely paused /ToWork job | None | Automated + stated live acceptance |
| [ ] | [achiCore #196](https://github.com/achibukz/achiCore/issues/196) | med | Abandon jobs without losing dirty work and resume the same ticket through a new attempt | None | Automated + stated live acceptance |
| [ ] | [AIS-OS #41](https://github.com/achibukz/AIS-OS/issues/41) | med | Include source links in concise email digests on every rendering path | None | Automated + stated live acceptance |
| [ ] | [AIS-OS #42](https://github.com/achibukz/AIS-OS/issues/42) | med | Resolve Obsidian wikilinks natively in the Tailscale web viewer | None | Automated + stated live acceptance |
| [ ] | [AIS-OS #43](https://github.com/achibukz/AIS-OS/issues/43) | high | Update agy-tickets for approved grilling decisions, dependency roadmaps and post-review HITL | None | Automated / author checks |
| [ ] | [achiCore #62](https://github.com/achibukz/achiCore/issues/62) | med | Finish transactional binding and session rollback for /bind and /unbind | None | Automated + stated live acceptance |
| [AIS-OS #44](https://github.com/achibukz/AIS-OS/issues/44) | high | Compute tomorrow weekday in the morning brief from the Manila report date | None | Automated / author checks |
| [ ] | [AIS-OS #8](https://github.com/achibukz/AIS-OS/issues/8) | med | Keep Calendar and email digest failures visible through shared Google health checks | None | Automated + stated live acceptance |
| [ ] | [achiCore #57](https://github.com/achibukz/achiCore/issues/57) | high | Serve /tasks area views without a model turn and simplify /status | [AIS-OS #6](https://github.com/achibukz/AIS-OS/issues/6) | Automated + stated live acceptance |
| [achiCore #197](https://github.com/achibukz/achiCore/issues/197) | high | Capture Telegram conversations and execution outcomes durably for learning | [achiCore #56](https://github.com/achibukz/achiCore/issues/56) | Automated + stated live acceptance |
| [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13) | high | Reconcile task and Calendar intents with stable IDs and durable receipts | [AIS-OS #6](https://github.com/achibukz/AIS-OS/issues/6) | Automated + stated live acceptance |
| [ ] | [achiCore #198](https://github.com/achibukz/achiCore/issues/198) | med | Load installed skills per conversation while keeping topic base skills scoped | [achiCore #56](https://github.com/achibukz/achiCore/issues/56) | Automated + stated live acceptance |
| [ ] | [achiCore #199](https://github.com/achibukz/achiCore/issues/199) | high | Manage independent Testing Grounds cards and one isolated PR testing slot | [AIS-OS #20](https://github.com/achibukz/AIS-OS/issues/20) | Automated + stated live acceptance |
| [achiCore #148](https://github.com/achibukz/achiCore/issues/148) | high | Apply sourced reconciliation to ordinary Telegram requests and corrections | [achiCore #197](https://github.com/achibukz/achiCore/issues/197), [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13), [achiCore #56](https://github.com/achibukz/achiCore/issues/56) | Automated + stated live acceptance |
| [ ] | [AIS-OS #45](https://github.com/achibukz/AIS-OS/issues/45) | high | Commit and push owned task, log, note and writing updates automatically | [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13) | Automated + stated live acceptance |
| [ ] | [achiCore #200](https://github.com/achibukz/achiCore/issues/200) | high | Wait for Testing Grounds after Luna SHIP and route live-test results back to /ToWork | [achiCore #199](https://github.com/achibukz/achiCore/issues/199) | Automated + stated live acceptance |
| [ ] | [AIS-OS #46](https://github.com/achibukz/AIS-OS/issues/46) | med | Group captured failures and automatically file actionable bug tickets with evidence | [achiCore #197](https://github.com/achibukz/achiCore/issues/197) | Automated + stated live acceptance |
| [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14) | high | Learn scoped semantic preferences immediately and consolidate daily at 3 AM Manila | [achiCore #148](https://github.com/achibukz/achiCore/issues/148), [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13) | Automated + stated live acceptance |
| [ ] | [AIS-OS #11](https://github.com/achibukz/AIS-OS/issues/11) | high | Reconcile verified GitHub and personal completions into tasks and debriefs | [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13), [achiCore #148](https://github.com/achibukz/achiCore/issues/148) | Automated + stated live acceptance |
| [ ] | [AIS-OS #47](https://github.com/achibukz/AIS-OS/issues/47) | high | Turn Canvas assignment events into linked tasks and reconcile later changes | [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13), [achiCore #148](https://github.com/achibukz/achiCore/issues/148) | Automated + stated live acceptance |
| [ ] | [AIS-OS #15](https://github.com/achibukz/AIS-OS/issues/15) | high | Apply linked task outcomes and sourced notes through permitted Sciel vault operations | [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14), [AIS-OS #45](https://github.com/achibukz/AIS-OS/issues/45) | Automated + stated live acceptance |
| [ ] | [AIS-OS #16](https://github.com/achibukz/AIS-OS/issues/16) | high | Deliver daily learning receipts and weekly evidence debriefs in achiNouncements | [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14), [AIS-OS #11](https://github.com/achibukz/AIS-OS/issues/11) | Automated + stated live acceptance |
| [ ] | [AIS-OS #48](https://github.com/achibukz/AIS-OS/issues/48) | med | Make daily briefs concise, truthful and consistent with Manila reporting windows | [AIS-OS #6](https://github.com/achibukz/AIS-OS/issues/6), [AIS-OS #11](https://github.com/achibukz/AIS-OS/issues/11), [AIS-OS #46](https://github.com/achibukz/AIS-OS/issues/46), [AIS-OS #44](https://github.com/achibukz/AIS-OS/issues/44), [AIS-OS #8](https://github.com/achibukz/AIS-OS/issues/8) | Automated + stated live acceptance |
| [ ] | [achiCore #149](https://github.com/achibukz/achiCore/issues/149) | high | Use current semantic preferences in warm turns and retire conflicting memory writers | [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14), [AIS-OS #15](https://github.com/achibukz/AIS-OS/issues/15), [achiCore #56](https://github.com/achibukz/achiCore/issues/56) | Automated + stated live acceptance |
| [AIS-OS #17](https://github.com/achibukz/AIS-OS/issues/17) | med | Publish verified procedures through reviewed skill PRs and scoped discovery | [achiCore #149](https://github.com/achibukz/achiCore/issues/149), [achiCore #198](https://github.com/achibukz/achiCore/issues/198) | Automated + stated live acceptance |
| [ ] | [AIS-OS #18](https://github.com/achibukz/AIS-OS/issues/18) | high | Verify semantic learning with held-out requests and a recoverable Telegram pilot | [achiCore #149](https://github.com/achibukz/achiCore/issues/149), [AIS-OS #11](https://github.com/achibukz/AIS-OS/issues/11), [AIS-OS #16](https://github.com/achibukz/AIS-OS/issues/16), [AIS-OS #47](https://github.com/achibukz/AIS-OS/issues/47) | Automated + stated live acceptance |

| [ ] | [AIS-OS #49](https://github.com/achibukz/AIS-OS/issues/49) | high | Reproducible GitHub Actions regression CI | None | Actual CI run plus local regression checks |

AIS-OS #49 can start alongside Asa and Sciel. It declares the test environment and command so future PR regressions run in CI. This planning change files the ticket only; it does not install CI.

## Existing actionable backlog retained

These tickets were read during the audit and left unchanged. Their current acceptance remains authoritative; inclusion here does not claim their gates passed. Read live bodies again before dispatch.

| Status | Ticket | Priority | Remaining work / audit disposition | Declared dependency | Parallel guidance |
|:---:|---|---|---|---|---|
| [ ] | [AIS-OS #24](https://github.com/achibukz/AIS-OS/issues/24) | unlabelled | Canvas first-release epic has shipped components, but this audit did not establish every live acceptance criterion. Keep open. | Child implementation tickets and release evidence | Inspect current #30/#37 receipts before closure; no new duplicate epic. |
| [ ] | [AIS-OS #31](https://github.com/achibukz/AIS-OS/issues/31) | unlabelled | Canvas materials/cache/search is optional follow-up beyond assignment reconciliation. | [AIS-OS #30](https://github.com/achibukz/AIS-OS/issues/30), closed; confirm release evidence | Independent later lane; preserve its scope. |
| [ ] | [AIS-OS #34](https://github.com/achibukz/AIS-OS/issues/34) | med | Shared sender split corruption remains actionable. | None | Fix before relying on long report output; coordinate email/brief rendering. |
| [ ] | [achiCore #9](https://github.com/achibukz/achiCore/issues/9) | high | Atlas still embeds stale schedules and log paths. Keep the live-discovery correction. | None | Useful early companion to Asa; avoid concurrent persona-file edits. |
| [ ] | [achiCore #91](https://github.com/achibukz/achiCore/issues/91) | med | Immich discussion/spike remains a separate product investigation. | None; spike still requires live comparison | Independent, lower than semantic cohesion. |
| [ ] | [achiCore #155](https://github.com/achibukz/achiCore/issues/155) | unlabelled | Separate conflict budgets and merge-queue status remain open; #153 closure was not proof of these fixes. | Merged PR #154 foundation | Can prepare independently; land apart from pause/abandon/HITL changes. |
| [ ] | [achiCore #156](https://github.com/achibukz/achiCore/issues/156) | unlabelled | Worker virtualenv probe cache still needs invalidation coverage. | Merged PR #154 foundation | Independent environment reliability fix; useful before repeated live tests. |
| [ ] | [achiCore #171](https://github.com/achibukz/achiCore/issues/171) | high | Transient network fetch retry remains a narrow recovery fix. | None | Coordinate standby.py changes with abandonment. |
| [ ] | [achiCore #172](https://github.com/achibukz/achiCore/issues/172) | med | Complete delegated reports still need the specified truncation-warning handling. | None | Coordinate shared bot.py/delegation.py edits. |
| [ ] | [achiCore #177](https://github.com/achibukz/achiCore/issues/177) | med | Delegated streaming helper reuse remains open. | achiCore #175 is closed and merged via #182 | Land with awareness of #185 delivery behavior. |
| [ ] | [achiCore #185](https://github.com/achibukz/achiCore/issues/185) | high | Final/live response separation remains an independent UX defect. | None | Prioritize alongside persona usability; coordinate #177. |
| [ ] | [achiCore #186](https://github.com/achibukz/achiCore/issues/186) | high | Effective Codex context capacity remains an independent catalog/launcher defect. | None | Independent of task semantics; verify installed CLI support. |

## Tracker audit and closure evidence

- Closed achiCore #10 only. Shared mixins shipped in merged PR #94 at d64e77c4. Current composition code and focused regressions satisfy the issue's implementation criteria. The closure comment records the test command and limits.
- Kept achiCore #62 open and narrowed it to the original unfulfilled cross-store rollback criterion. Its existing test deliberately leaves a removed binding and retained session after persistence failure. A passing test did not establish the stronger issue requirement.
- Kept AIS-OS #20 open. Its source PR #21 is still open and the earlier installation does not establish required real acceptance. Its body now requires the approved self-guided checklist.
- Kept AIS-OS #24 open. Merged components and a running timer are insufficient to certify the entire first-release checklist in this audit.
- Existing task/Calendar, learning, note, receipt and completion issues were revised in place. Their implementation remains open. Prior assistant or document statements are not completion evidence.
- Closed blockers achiCore #4/#18/#153/#175 and AIS-OS #5/#7 were fetched and read. #153's closure does not certify deferred #155/#156 gates.

Automated audit command on achiCore ef93ced:

```bash
scripts/run_tests.py -q tests/test_prompt_mixins.py tests/test_unbind_and_binding_uniqueness.py tests/test_orchestration_mixin.py
```

Observed result: 59 passed in 0.90s. This was automated verification, not a new Telegram live run. The test receipt resolved AIS-OS 8adfbe18; achiCore's declared sibling revision remains c51e5b23.

## Scheduling cautions

The first persona ticket may use existing isolated manual staging. Requiring the future automatic Testing Grounds queue first would invert Aki's priority and create unnecessary dependencies. Once shipped, the queue becomes the normal required-HITL route.

The new dependency graph has no cycles. Existing retained tickets still require reading their live blockers before assignment. A merge or revision change invalidates old acceptance where it changes the candidate under review. Parallel preparation does not waive fresh CI, Luna review or the one-slot testing ownership rule.

## Planning delivery

The planning/skill PR references AIS-OS #43 only. It does not close runtime implementation tickets. The installed agy-tickets copy is updated at Aki's request; the tracked source remains reviewable in this PR. No production persona, service, timer or Calendar destination was changed during this planning task.
