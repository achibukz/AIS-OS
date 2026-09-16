# Asta and calendar roadmap, September 17, 2026

This roadmap covers all 59 open issues in achibukz/achiCore and achibukz/AIS-OS observed after publication: 19 new issues from the [Asta and calendar discussion](asta-and-calendar-discussion-2026-09-17.md) and 40 existing issues. Existing issues were not edited. Their statuses come from GitHub state and declared blockers, not a fresh implementation audit; the [Astra roadmap](astra-roadmap-2026-09-11.md) remains their detailed plan.

Priority is Aki's delivery preference. Blocked by is a hard dispatch constraint. AFK means unattended implementation, never merge authority. Parallel lanes still need separate worktrees and sequential landing where files overlap.

## Start here

- [AIS-OS #63](https://github.com/achibukz/AIS-OS/issues/63), the `asta.py` foundation, has no blockers and starts the Asta nutrition lane.
- [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13) must finish through PR #59 before the calendar client [AIS-OS #60](https://github.com/achibukz/AIS-OS/issues/60) starts, by Aki's decision.
- [achiCore #220](https://github.com/achibukz/achiCore/pull/220) already shipped the Asta persona prototype at prompt `asta-0.1.3`.

## New lanes and joins

| Lane | Sequence | Can run alongside | Landing caution |
|---|---|---|---|
| Asta nutrition | #63, then #64, then #65, then #66 | Calendar lane, backups, Apple ingest | #64 to #66 all edit `asta.py`; land in order |
| Asta operations | #63, then #67 | Nutrition after #63 | Timer units only |
| Calendar client | #13 via PR #59, then #60 | Asta nutrition | Keep the transport compatible with cohesion |
| Calendar consumers | #60, then #61; #60 and #13, then #62, then achiCore #221 | Asta nutrition | #61 and #62 both touch gws helpers; land #61 first |
| Asta scheduling | #60, then achiCore #222 | Nutrition | Prompt version bump; coordinate with any other `asta.md` edit |
| Asta summary (join) | #65 and #60, then #68 | Scheduling | Changes shared `telegram_notify.send()`; keep default behaviour unchanged |
| Asta review UI | #65, then achiCore #223 | Summary | Telegram command registration overlaps other achiCore command work |
| Wearables | #63, then #69, then tracking #73 and #74 | All Asta lanes | Network-facing listener; tailnet bind only |
| Tracking | #70 after #65 and #66; #71 after #66; #72 after #63 | Not dispatchable | Split into tickets when data exists |

The new dependency graph has no cycles. Every blocker reference resolves to an open issue or to AIS-OS #13. [AIS-OS #75](https://github.com/achibukz/AIS-OS/issues/75) is the epic and blocks nothing.

## New issues

| Status | Ticket | Priority | Deliverable | Hard blockers | Verification gate |
|---|---|---|---|---|---|
| Blocked | [AIS-OS #60](https://github.com/achibukz/AIS-OS/issues/60) | high | Build gcal.py, one Google Calendar client for every agent and script | AIS-OS #13 | Automated + HITL |
| Queued | [AIS-OS #63](https://github.com/achibukz/AIS-OS/issues/63) | high | Build the asta.py foundation: store, status, profile, targets and weight | None | Automated + HITL |
| Blocked | [AIS-OS #64](https://github.com/achibukz/AIS-OS/issues/64) | high | Resolve foods for Asta from templates, Filipino staples and USDA | AIS-OS #63 | Automated + HITL |
| Blocked | [AIS-OS #65](https://github.com/achibukz/AIS-OS/issues/65) | high | Log meals through asta.py with grams, confidence tiers and immutable corrections | AIS-OS #64 | Automated + HITL |
| Blocked | [AIS-OS #66](https://github.com/achibukz/AIS-OS/issues/66) | high | Log food photos through asta.py and keep them under training/asta | AIS-OS #65 | Automated + HITL |
| Epic | [AIS-OS #75](https://github.com/achibukz/AIS-OS/issues/75) | high | Asta health vertical and shared Google Calendar client | None | Context only |
| Blocked | [AIS-OS #61](https://github.com/achibukz/AIS-OS/issues/61) | med | Move the briefs, auth health check and email digest onto the shared gws client | AIS-OS #60 | Automated + HITL |
| Blocked | [AIS-OS #62](https://github.com/achibukz/AIS-OS/issues/62) | med | Move cohesion onto the shared calendar client and retire gcal_add.py | AIS-OS #13, AIS-OS #60 | Automated + HITL |
| Blocked | [AIS-OS #67](https://github.com/achibukz/AIS-OS/issues/67) | med | Back up the Asta database nightly | AIS-OS #63 | Automated |
| Blocked | [AIS-OS #68](https://github.com/achibukz/AIS-OS/issues/68) | med | Post the 21:00 Asta daily summary into the Asta topic | AIS-OS #65, AIS-OS #60 | Automated + HITL |
| Blocked | [achiCore #221](https://github.com/achibukz/achiCore/issues/221) | med | Point Asa at gcal.py for calendar reads and writes | AIS-OS #62 | Automated + HITL |
| Blocked | [achiCore #222](https://github.com/achibukz/achiCore/issues/222) | med | Let Asta read Aki's schedule and book workouts through gcal.py | AIS-OS #60 | Automated + HITL |
| Blocked | [AIS-OS #69](https://github.com/achibukz/AIS-OS/issues/69) | low | Ingest Apple Health workouts for Asta over Tailscale | AIS-OS #63 | Automated + HITL |
| Blocked | [AIS-OS #70](https://github.com/achibukz/AIS-OS/issues/70) | low | Track second-wave Asta nutrition: Open Food Facts, weekly review and calibration | AIS-OS #65, AIS-OS #66 | Tracking |
| Blocked | [AIS-OS #71](https://github.com/achibukz/AIS-OS/issues/71) | low | Track a weighed Filipino meal benchmark for Asta | AIS-OS #66 | Tracking |
| Blocked | [AIS-OS #72](https://github.com/achibukz/AIS-OS/issues/72) | low | Track manual lifting logs and training plans for Asta | AIS-OS #63 | Tracking |
| Blocked | [AIS-OS #73](https://github.com/achibukz/AIS-OS/issues/73) | low | Track Fitbit and Google Health ingest for Asta | AIS-OS #69 | Tracking |
| Blocked | [AIS-OS #74](https://github.com/achibukz/AIS-OS/issues/74) | low | Track Hevy integration for Asta | AIS-OS #69 | Tracking |
| Blocked | [achiCore #223](https://github.com/achibukz/achiCore/issues/223) | low | Add /mealcheck to list flagged Asta meals | AIS-OS #65 | Automated + HITL |

## Existing open issues

| Status | Ticket | Priority | Deliverable | Hard blockers | Verification gate |
|---|---|---|---|---|---|
| Open, blocked | [AIS-OS #11](https://github.com/achibukz/AIS-OS/issues/11) | high | Reconcile verified GitHub and personal completions into tasks and debriefs | AIS-OS #13, achiCore #148 | Automated + HITL |
| Ongoing, PR #59 | [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13) | high | Reconcile task and Calendar intents with stable IDs and durable receipts | AIS-OS #6 | Automated |
| Open, blocked | [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14) | high | Learn scoped semantic preferences immediately and consolidate daily at 3 AM Manila | achiCore #148, AIS-OS #13 | Automated |
| Open, blocked | [AIS-OS #15](https://github.com/achibukz/AIS-OS/issues/15) | high | Apply linked task outcomes and sourced notes through permitted Sciel vault operations | AIS-OS #14, AIS-OS #45 | Automated |
| Open, blocked | [AIS-OS #16](https://github.com/achibukz/AIS-OS/issues/16) | high | Deliver daily learning receipts and weekly evidence debriefs in achiNouncements | AIS-OS #14, AIS-OS #11 | Automated |
| Open, blocked | [AIS-OS #18](https://github.com/achibukz/AIS-OS/issues/18) | high | Verify semantic learning with held-out requests and a recoverable Telegram pilot | achiCore #149, AIS-OS #11, AIS-OS #16, AIS-OS #47 | Automated |
| Open | [AIS-OS #20](https://github.com/achibukz/AIS-OS/issues/20) | high | Prepare copy-paste live-test checklists with expected results and resumable evidence | None | Automated + HITL |
| Open | [AIS-OS #44](https://github.com/achibukz/AIS-OS/issues/44) | high | Compute tomorrow weekday in the morning brief from the Manila report date | None | Automated |
| Open, blocked | [AIS-OS #45](https://github.com/achibukz/AIS-OS/issues/45) | high | Commit and push owned task, log, note and writing updates automatically | AIS-OS #13 | Automated + HITL |
| Open, blocked | [AIS-OS #47](https://github.com/achibukz/AIS-OS/issues/47) | high | Turn Canvas assignment events into linked tasks and reconcile later changes | AIS-OS #13, achiCore #148 | Automated |
| Open | [AIS-OS #49](https://github.com/achibukz/AIS-OS/issues/49) | high | Run AIS-OS regression tests in reproducible GitHub Actions CI | None | Automated |
| Open | [AIS-OS #57](https://github.com/achibukz/AIS-OS/issues/57) | high | Remove per-message and per-account Gmail links from email_digest.py | None | Automated |
| Open, blocked | [AIS-OS #58](https://github.com/achibukz/AIS-OS/issues/58) | high | Turn ingested meeting proposals into linked tasks and Calendar deadlines | AIS-OS #13, schoolMem #2 | Automated + HITL |
| Open | [achiCore #9](https://github.com/achibukz/achiCore/issues/9) | high | Correct the Atlas persona: query system state instead of reciting it | None | Automated |
| Open, blocked | [achiCore #148](https://github.com/achibukz/achiCore/issues/148) | high | Apply sourced reconciliation to ordinary Telegram requests and corrections | achiCore #197, AIS-OS #13, achiCore #56 | Automated |
| Open, blocked | [achiCore #149](https://github.com/achibukz/achiCore/issues/149) | high | Use current semantic preferences in warm turns and retire conflicting memory writers | AIS-OS #14, AIS-OS #15, achiCore #56 | Automated |
| Open | [achiCore #171](https://github.com/achibukz/achiCore/issues/171) | high | Retry transient git fetch failures instead of stranding a worker pair at release_pending | None | Automated |
| Open, blocked | [achiCore #199](https://github.com/achibukz/achiCore/issues/199) | high | Manage independent Testing Grounds cards and one isolated PR testing slot | AIS-OS #20 | Automated |
| Open, blocked | [achiCore #200](https://github.com/achibukz/achiCore/issues/200) | high | Wait for Testing Grounds after Luna SHIP and route live-test results back to /ToWork | achiCore #199 | Automated + HITL |
| Open | [achiCore #207](https://github.com/achibukz/achiCore/issues/207) | high | Audit CI for deterministic, zero-skip verification across worktrees | None | Automated |
| Open | [achiCore #208](https://github.com/achibukz/achiCore/issues/208) | high | /usage Codex section fails almost every call: missing originator/chatgpt-account-id headers | None | Automated |
| Open | [achiCore #209](https://github.com/achibukz/achiCore/issues/209) | high | Discuss a shared voice-calibration skill for Ara | None | Automated + HITL |
| Open | [achiCore #215](https://github.com/achibukz/achiCore/issues/215) | high | Make /syncres commit-first and restart only after a successful sync | None | Automated + HITL |
| Open | [AIS-OS #8](https://github.com/achibukz/AIS-OS/issues/8) | med | Keep Calendar and email digest failures visible through shared Google health checks | None | Automated |
| Open, blocked | [AIS-OS #17](https://github.com/achibukz/AIS-OS/issues/17) | med | Publish verified procedures through reviewed skill PRs and scoped discovery | achiCore #149, achiCore #198 | Automated |
| Open | [AIS-OS #34](https://github.com/achibukz/AIS-OS/issues/34) | med | Fix shared Telegram splitter dropping tails and duplicating long messages | None | Automated |
| Open | [AIS-OS #46](https://github.com/achibukz/AIS-OS/issues/46) | med | Group captured failures and automatically file actionable bug tickets with evidence | achiCore #197 | Automated |
| Open, blocked | [AIS-OS #48](https://github.com/achibukz/AIS-OS/issues/48) | med | Make daily briefs concise, truthful and consistent with Manila reporting windows | AIS-OS #6, AIS-OS #11, AIS-OS #46, AIS-OS #44, AIS-OS #8 | Automated |
| Open | [achiCore #62](https://github.com/achibukz/achiCore/issues/62) | med | Finish transactional binding and session rollback for /bind and /unbind | None | Automated |
| Open | [achiCore #91](https://github.com/achibukz/achiCore/issues/91) | med | Discuss and spike Immich integration for Telegram photo delivery | None | Automated |
| Open | [achiCore #195](https://github.com/achibukz/achiCore/issues/195) | med | Change writer and reviewer models on a safely paused /ToWork job | None | Automated |
| Open | [achiCore #196](https://github.com/achibukz/achiCore/issues/196) | med | Abandon jobs without losing dirty work and resume the same ticket through a new attempt | None | Automated + HITL |
| Open | [achiCore #198](https://github.com/achibukz/achiCore/issues/198) | med | Load installed skills per conversation while keeping topic base skills scoped | achiCore #56 | Automated |
| Open | [achiCore #210](https://github.com/achibukz/achiCore/issues/210) | med | Calibrate Ara correspondence with context and reply examples | None | Automated + HITL |
| Open | [achiCore #211](https://github.com/achibukz/achiCore/issues/211) | med | Calibrate Ara spoken scripts from confirmed speech samples | None | Automated + HITL |
| Open | [achiCore #212](https://github.com/achibukz/achiCore/issues/212) | low | Calibrate Ara public posts without importing private-message habits | None | Automated + HITL |
| Open | [AIS-OS #24](https://github.com/achibukz/AIS-OS/issues/24) | - | Canvas: first Telegram release with current-term queries and phone reauthentication | None | Automated |
| Open | [AIS-OS #31](https://github.com/achibukz/AIS-OS/issues/31) | - | Canvas: follow-up course materials, file cache and FTS search | None | Automated |
| Open | [achiCore #155](https://github.com/achibukz/achiCore/issues/155) | - | Separate merge-conflict retries from coding cycles and show Atlas repair and merge-queue progress | None | Automated |
| Open | [achiCore #156](https://github.com/achibukz/achiCore/issues/156) | - | Invalidate successful worker probes when the worker virtualenv disappears or changes | None | Automated |

