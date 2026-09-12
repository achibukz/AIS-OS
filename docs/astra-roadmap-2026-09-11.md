# Astra implementation roadmap, September 11, 2026

This inventory includes all 43 open issues observed after publication in achibukz/achiCore and achibukz/AIS-OS. Existing unrelated tickets remain unchanged. The [plan](astra-plan.md) explains behavior; the [discussion](telegram-cohesion-discussion-2026-09-11.md) records Aki's decisions.

## Status audit, September 12, 2026

The old table cells used bare `[ ]`, which are plain text rather than reliable task-list controls. The checklists below are real Markdown task items. Tables use explicit states so a partial lane cannot look finished.

Completed:

- [x] achiCore #56, persona precedence
- [x] AIS-OS #6, #41, #42, #43 and #55
- [x] Canvas #25 through #30, plus #37
- [x] achiCore #172, #177 and #185

Ongoing:

- [ ] AIS-OS #13 has two committed changes in its dedicated worktree, but no pull request yet.
- [ ] achiCore #57 has uncommitted implementation work and is now unblocked by AIS-OS #55.
- [ ] achiCore #194 has a small uncommitted Telegram-menu change.
- [ ] AIS-OS #44 and #8 are part of the current AIS-OS worktree batch. Keep their changes isolated from blocked #48.
- [ ] AIS-OS #20 remains in open PR #21 and still needs its stated live acceptance.

Queued work remains open without an observed implementation checkout. Blocked work has unmet issue dependencies and must not be started as though it were ready.

## Start here

The persona and deterministic task-rendering foundations are done: [achiCore #56](https://github.com/achibukz/achiCore/issues/56), [AIS-OS #6](https://github.com/achibukz/AIS-OS/issues/6) and [AIS-OS #55](https://github.com/achibukz/AIS-OS/issues/55). Finish the active [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13), [achiCore #57](https://github.com/achibukz/achiCore/issues/57), [achiCore #194](https://github.com/achibukz/achiCore/issues/194), and the small AIS-OS #44/#8 work before starting dependent semantic work. Then complete the captured-event path before enabling automatic semantic learning.

Priority is a scheduling preference. Blocked by is a hard dispatch constraint. Parallel means separate owned worktrees and compatible file changes; it does not mean two PRs may replace the same staging daemon.

## Parallel lanes and joins

| Lane | Status | Can progress alongside | Landing caution |
|---|---|---|---|
| Personas | Ongoing | [achiCore #56](https://github.com/achibukz/achiCore/issues/56) done, then [achiCore #198](https://github.com/achibukz/achiCore/issues/198) | AIS-OS renderer and checklist work | Coordinate prompt/config edits with [achiCore #197](https://github.com/achibukz/achiCore/issues/197) |
| Task foundation | Ongoing | [AIS-OS #6](https://github.com/achibukz/AIS-OS/issues/6) and [AIS-OS #55](https://github.com/achibukz/AIS-OS/issues/55) done, then [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13) then [achiCore #148](https://github.com/achibukz/achiCore/issues/148) | Persona work until foreground joins it | Renderer changes also affect digests |
| Evidence | Ongoing | [achiCore #56](https://github.com/achibukz/achiCore/issues/56) done, then [achiCore #197](https://github.com/achibukz/achiCore/issues/197) | Task CLI work | Foreground waits for capture and CLI |
| Semantics | Blocked | [achiCore #148](https://github.com/achibukz/achiCore/issues/148) then [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14) | Completion and Canvas reconciliation after foreground | Daily learning must not duplicate the old writer |
| Persistence/notes | Blocked | [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13) then [AIS-OS #45](https://github.com/achibukz/AIS-OS/issues/45); notes join learning via [AIS-OS #15](https://github.com/achibukz/AIS-OS/issues/15) | Completion and incident work | Serialize writes by repository; preserve dirty work |
| Completion | Blocked | [achiCore #148](https://github.com/achibukz/achiCore/issues/148) then [AIS-OS #11](https://github.com/achibukz/AIS-OS/issues/11) and [AIS-OS #47](https://github.com/achibukz/AIS-OS/issues/47) | Semantic preferences | Both use the same stable IDs and partial-operation contract |
| Recall | Blocked | [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14) plus [AIS-OS #15](https://github.com/achibukz/AIS-OS/issues/15) then [achiCore #149](https://github.com/achibukz/achiCore/issues/149) | Report work | Engine prompt changes need coordinated landing |
| Reports | Blocked | [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14) plus [AIS-OS #11](https://github.com/achibukz/AIS-OS/issues/11) then [AIS-OS #16](https://github.com/achibukz/AIS-OS/issues/16) | Recall and Testing Grounds | Daily receipt at 3 AM; midnight remains separate |
| Incidents | Blocked | [achiCore #197](https://github.com/achibukz/achiCore/issues/197) then [AIS-OS #46](https://github.com/achibukz/AIS-OS/issues/46) | Preference work | Sanitize before public filing; no auto-dispatch |
| Testing | Ongoing | [AIS-OS #20](https://github.com/achibukz/AIS-OS/issues/20) then [achiCore #199](https://github.com/achibukz/achiCore/issues/199) then [achiCore #200](https://github.com/achibukz/achiCore/issues/200) | Core learning lane | One live slot; land coordinator changes sequentially |
| Job recovery | Queued | [achiCore #195](https://github.com/achibukz/achiCore/issues/195) and [achiCore #196](https://github.com/achibukz/achiCore/issues/196) | AIS-OS work | Coordinate with existing achiCore #155/#171 and HITL adapter |
| Daily UX | Ongoing | [AIS-OS #41](https://github.com/achibukz/AIS-OS/issues/41) and [AIS-OS #42](https://github.com/achibukz/AIS-OS/issues/42) done; [AIS-OS #44](https://github.com/achibukz/AIS-OS/issues/44) and [achiCore #194](https://github.com/achibukz/achiCore/issues/194) ongoing | All core lanes | Broad brief redesign [AIS-OS #48](https://github.com/achibukz/AIS-OS/issues/48) waits for outcomes and incidents |
| Proof | Blocked | Prepare [AIS-OS #18](https://github.com/achibukz/AIS-OS/issues/18) corpus early; run after listed blockers | All implementation lanes | Only observed real results satisfy activation |
| Later extension | Blocked | [AIS-OS #17](https://github.com/achibukz/AIS-OS/issues/17) after recall and conversation skills | Pilot preparation | Shared guidance still goes through review |

## Published and revised implementation tickets

The status column was refreshed from GitHub and observed worktrees on September 12. AFK means unattended implementation, not permission to merge. Each issue contains explicit test cases and its human acceptance requirements.

| Status | Ticket | Priority | Deliverable | Hard blockers | Verification gate |
|:---:|---|---|---|---|---|
| Done | [achiCore #56](https://github.com/achibukz/achiCore/issues/56) | high | Make General Asa, give Sciel both vault topics, and enforce persona precedence | None | Automated + stated live acceptance |
| Done | [AIS-OS #6](https://github.com/achibukz/AIS-OS/issues/6) | high | Render all tasks by fixed area through one shared deterministic renderer | None | Automated / author checks |
| Done | [AIS-OS #55](https://github.com/achibukz/AIS-OS/issues/55) | high | Filter systems and project research from default /tasks and support all and backlog views | None | Automated / author checks |
| Ongoing | [achiCore #194](https://github.com/achibukz/achiCore/issues/194) | med | Expose existing /sync and /syncres commands in Telegram menus | None | Automated + stated live acceptance |
| Ongoing | [AIS-OS #20](https://github.com/achibukz/AIS-OS/issues/20) | high | Prepare copy-paste live-test checklists with expected results and resumable evidence | None | Automated + stated live acceptance |
| Queued | [achiCore #195](https://github.com/achibukz/achiCore/issues/195) | med | Change writer and reviewer models on a safely paused /ToWork job | None | Automated + stated live acceptance |
| Queued | [achiCore #196](https://github.com/achibukz/achiCore/issues/196) | med | Abandon jobs without losing dirty work and resume the same ticket through a new attempt | None | Automated + stated live acceptance |
| Done | [AIS-OS #41](https://github.com/achibukz/AIS-OS/issues/41) | med | Include source links in concise email digests on every rendering path | None | Automated + stated live acceptance |
| Done | [AIS-OS #42](https://github.com/achibukz/AIS-OS/issues/42) | med | Resolve Obsidian wikilinks natively in the Tailscale web viewer | None | Automated + stated live acceptance |
| Done | [AIS-OS #43](https://github.com/achibukz/AIS-OS/issues/43) | high | Update agy-tickets for approved grilling decisions, dependency roadmaps and post-review HITL | None | Automated / author checks |
| Queued | [achiCore #62](https://github.com/achibukz/achiCore/issues/62) | med | Finish transactional binding and session rollback for /bind and /unbind | None | Automated + stated live acceptance |
| Ongoing | [AIS-OS #44](https://github.com/achibukz/AIS-OS/issues/44) | high | Compute tomorrow weekday in the morning brief from the Manila report date | None | Automated / author checks |
| Ongoing | [AIS-OS #8](https://github.com/achibukz/AIS-OS/issues/8) | med | Keep Calendar and email digest failures visible through shared Google health checks | None | Automated + stated live acceptance |
| Ongoing | [achiCore #57](https://github.com/achibukz/achiCore/issues/57) | high | Serve /tasks area views without a model turn and simplify /status | [AIS-OS #55](https://github.com/achibukz/AIS-OS/issues/55), done | Automated + stated live acceptance |
| Queued | [achiCore #197](https://github.com/achibukz/achiCore/issues/197) | high | Capture Telegram conversations and execution outcomes durably for learning | [achiCore #56](https://github.com/achibukz/achiCore/issues/56), done | Automated + stated live acceptance |
| Ongoing | [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13) | high | Reconcile task and Calendar intents with stable IDs and durable receipts | [AIS-OS #6](https://github.com/achibukz/AIS-OS/issues/6), done | Automated + stated live acceptance |
| Queued | [achiCore #198](https://github.com/achibukz/achiCore/issues/198) | med | Load installed skills per conversation while keeping topic base skills scoped | [achiCore #56](https://github.com/achibukz/achiCore/issues/56), done | Automated + stated live acceptance |
| Blocked | [achiCore #199](https://github.com/achibukz/achiCore/issues/199) | high | Manage independent Testing Grounds cards and one isolated PR testing slot | [AIS-OS #20](https://github.com/achibukz/AIS-OS/issues/20) | Automated + stated live acceptance |
| Blocked | [achiCore #148](https://github.com/achibukz/achiCore/issues/148) | high | Apply sourced reconciliation to ordinary Telegram requests and corrections | [achiCore #197](https://github.com/achibukz/achiCore/issues/197), [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13), [achiCore #56](https://github.com/achibukz/achiCore/issues/56), done | Automated + stated live acceptance |
| Blocked | [AIS-OS #45](https://github.com/achibukz/AIS-OS/issues/45) | high | Commit and push owned task, log, note and writing updates automatically | [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13) | Automated + stated live acceptance |
| Blocked | [achiCore #200](https://github.com/achibukz/achiCore/issues/200) | high | Wait for Testing Grounds after Luna SHIP and route live-test results back to /ToWork | [achiCore #199](https://github.com/achibukz/achiCore/issues/199) | Automated + stated live acceptance |
| Blocked | [AIS-OS #46](https://github.com/achibukz/AIS-OS/issues/46) | med | Group captured failures and automatically file actionable bug tickets with evidence | [achiCore #197](https://github.com/achibukz/achiCore/issues/197) | Automated + stated live acceptance |
| Blocked | [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14) | high | Learn scoped semantic preferences immediately and consolidate daily at 3 AM Manila | [achiCore #148](https://github.com/achibukz/achiCore/issues/148), [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13) | Automated + stated live acceptance |
| Blocked | [AIS-OS #11](https://github.com/achibukz/AIS-OS/issues/11) | high | Reconcile verified GitHub and personal completions into tasks and debriefs | [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13), [achiCore #148](https://github.com/achibukz/achiCore/issues/148) | Automated + stated live acceptance |
| Blocked | [AIS-OS #47](https://github.com/achibukz/AIS-OS/issues/47) | high | Turn Canvas assignment events into linked tasks and reconcile later changes | [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13), [achiCore #148](https://github.com/achibukz/achiCore/issues/148) | Automated + stated live acceptance |
| Blocked | [AIS-OS #15](https://github.com/achibukz/AIS-OS/issues/15) | high | Apply linked task outcomes and sourced notes through permitted Sciel vault operations | [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14), [AIS-OS #45](https://github.com/achibukz/AIS-OS/issues/45) | Automated + stated live acceptance |
| Blocked | [AIS-OS #16](https://github.com/achibukz/AIS-OS/issues/16) | high | Deliver daily learning receipts and weekly evidence debriefs in achiNouncements | [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14), [AIS-OS #11](https://github.com/achibukz/AIS-OS/issues/11) | Automated + stated live acceptance |
| Blocked | [AIS-OS #48](https://github.com/achibukz/AIS-OS/issues/48) | med | Make daily briefs concise, truthful and consistent with Manila reporting windows | [AIS-OS #6](https://github.com/achibukz/AIS-OS/issues/6), [AIS-OS #11](https://github.com/achibukz/AIS-OS/issues/11), [AIS-OS #46](https://github.com/achibukz/AIS-OS/issues/46), [AIS-OS #44](https://github.com/achibukz/AIS-OS/issues/44), [AIS-OS #8](https://github.com/achibukz/AIS-OS/issues/8) | Automated + stated live acceptance |
| Blocked | [achiCore #149](https://github.com/achibukz/achiCore/issues/149) | high | Use current semantic preferences in warm turns and retire conflicting memory writers | [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14), [AIS-OS #15](https://github.com/achibukz/AIS-OS/issues/15), [achiCore #56](https://github.com/achibukz/achiCore/issues/56), done | Automated + stated live acceptance |
| Blocked | [AIS-OS #17](https://github.com/achibukz/AIS-OS/issues/17) | med | Publish verified procedures through reviewed skill PRs and scoped discovery | [achiCore #149](https://github.com/achibukz/achiCore/issues/149), [achiCore #198](https://github.com/achibukz/achiCore/issues/198) | Automated + stated live acceptance |
| Blocked | [AIS-OS #18](https://github.com/achibukz/AIS-OS/issues/18) | high | Verify semantic learning with held-out requests and a recoverable Telegram pilot | [achiCore #149](https://github.com/achibukz/achiCore/issues/149), [AIS-OS #11](https://github.com/achibukz/AIS-OS/issues/11), [AIS-OS #16](https://github.com/achibukz/AIS-OS/issues/16), [AIS-OS #47](https://github.com/achibukz/AIS-OS/issues/47) | Automated + stated live acceptance |

| Queued | [AIS-OS #49](https://github.com/achibukz/AIS-OS/issues/49) | high | Reproducible GitHub Actions regression CI | None | Actual CI run plus local regression checks |

AIS-OS #49 can start alongside Asa and Sciel. It declares the test environment and command so future PR regressions run in CI. This planning change files the ticket only; it does not install CI.

## Existing actionable backlog retained

These tickets were read during the audit and left unchanged. Their current acceptance remains authoritative; inclusion here does not claim their gates passed. Read live bodies again before dispatch.

| Status | Ticket | Priority | Remaining work / audit disposition | Declared dependency | Parallel guidance |
|:---:|---|---|---|---|---|
| Ongoing | [AIS-OS #24](https://github.com/achibukz/AIS-OS/issues/24) | unlabelled | Canvas first-release epic has shipped components, but this audit did not establish every live acceptance criterion. Keep open. | Child implementation tickets and release evidence | Inspect current #30/#37 receipts before closure; no new duplicate epic. |
| Queued | [AIS-OS #31](https://github.com/achibukz/AIS-OS/issues/31) | unlabelled | Canvas materials/cache/search is optional follow-up beyond assignment reconciliation. | [AIS-OS #30](https://github.com/achibukz/AIS-OS/issues/30), closed; confirm release evidence | Independent later lane; preserve its scope. |
| Queued | [AIS-OS #34](https://github.com/achibukz/AIS-OS/issues/34) | med | Shared sender split corruption remains actionable. | None | Fix before relying on long report output; coordinate email/brief rendering. |
| Queued | [achiCore #9](https://github.com/achibukz/achiCore/issues/9) | high | Atlas still embeds stale schedules and log paths. Keep the live-discovery correction. | None | Useful early companion to Asa; avoid concurrent persona-file edits. |
| Queued | [achiCore #91](https://github.com/achibukz/achiCore/issues/91) | med | Immich discussion/spike remains a separate product investigation. | None; spike still requires live comparison | Independent, lower than semantic cohesion. |
| Queued | [achiCore #155](https://github.com/achibukz/achiCore/issues/155) | unlabelled | Separate conflict budgets and merge-queue status remain open; #153 closure was not proof of these fixes. | Merged PR #154 foundation | Can prepare independently; land apart from pause/abandon/HITL changes. |
| Queued | [achiCore #156](https://github.com/achibukz/achiCore/issues/156) | unlabelled | Worker virtualenv probe cache still needs invalidation coverage. | Merged PR #154 foundation | Independent environment reliability fix; useful before repeated live tests. |
| Queued | [achiCore #171](https://github.com/achibukz/achiCore/issues/171) | high | Transient network fetch retry remains a narrow recovery fix. | None | Coordinate standby.py changes with abandonment. |
| Queued | [achiCore #186](https://github.com/achibukz/achiCore/issues/186) | high | Effective Codex context capacity remains an independent catalog/launcher defect. | None | Independent of task semantics; verify installed CLI support. |

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
