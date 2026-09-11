# Astra plan for Telegram cohesion

Updated September 11, 2026 from Aki's approved grilling session. This plan supersedes conflicting ordering and workflow statements in the [September 5 plan](history/astra-plan-2026-09-05.md), preserved as history. The [discussion record](telegram-cohesion-discussion-2026-09-11.md) holds the decisions and proposed reconciliation prompt. The [roadmap](astra-roadmap-2026-09-11.md) lists all current open tickets, including unrelated existing work.

This is an implementation plan. Publishing issues and updating the ticket skill does not deploy personas, learning, timers or Testing Grounds automation.

## Delivery order

1. Ship Asa and Sciel through [achiCore #56](https://github.com/achibukz/achiCore/issues/56). Keep General's topic identity and existing delegation receipts. Remove Agi after references migrate. Resolve prompt precedence and current routing without waiting for the future learning platform.
2. Establish the task and evidence foundations through [AIS-OS #6](https://github.com/achibukz/AIS-OS/issues/6), [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13) and [achiCore #197](https://github.com/achibukz/achiCore/issues/197). The renderer and task/Calendar CLI can progress alongside persona work; capture lands after persona changes to reduce shared-pipeline conflicts.
3. Connect normal requests through [achiCore #148](https://github.com/achibukz/achiCore/issues/148), semantic preference learning through [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14), and completion/Canvas reconciliation through [AIS-OS #11](https://github.com/achibukz/AIS-OS/issues/11) and [AIS-OS #47](https://github.com/achibukz/AIS-OS/issues/47). This makes recorded notifications lead to tracked work.
4. Add verified Git persistence, permitted vault updates and full warm recall through [AIS-OS #45](https://github.com/achibukz/AIS-OS/issues/45), [AIS-OS #15](https://github.com/achibukz/AIS-OS/issues/15) and [achiCore #149](https://github.com/achibukz/achiCore/issues/149). Daily learning receipts and weekly summaries use [AIS-OS #16](https://github.com/achibukz/AIS-OS/issues/16).
5. Prove the result with [AIS-OS #18](https://github.com/achibukz/AIS-OS/issues/18). Prepare its corpus early, but run final acceptance after the relevant integrations ship. Shared skill publication through [AIS-OS #17](https://github.com/achibukz/AIS-OS/issues/17) is a later extension and no longer blocks proving the core semantic-learning path.

Testing checklists and coordinator controls form a separate lane: [AIS-OS #20](https://github.com/achibukz/AIS-OS/issues/20) then [achiCore #199](https://github.com/achibukz/achiCore/issues/199) then [achiCore #200](https://github.com/achibukz/achiCore/issues/200). Pause/model changes and abandonment are independent specifications, but coordinator changes should land sequentially. The first persona acceptance can use existing isolated staging instead of waiting for the future queue.

[AIS-OS #49](https://github.com/achibukz/AIS-OS/issues/49) establishes regression CI and a reproducible shared test command. It is high priority and can run alongside Asa and Sciel. Only the ticket is created in this planning task.

## Ownership and behavior

| Concern | Owner |
|---|---|
| General conversation and delegation judgment | Asa in achiCore |
| schoolMem and achiMem operations | Sciel in each separate topic |
| Writing and email drafts | Ara |
| Task register and task/Calendar relationships | AIS-OS cohesion writer and tasks.md |
| Appointments | Google Calendar, linked by account/calendar/event identity |
| Canvas cache, observed transitions and notification delivery | Existing AIS-OS Canvas pipeline |
| Telegram source capture and engine context | achiCore common pipeline |
| Accepted preferences, source lineage and retries | Governed AIS-OS coordination records |
| PR testing queue and /ToWork job state | achiCore coordinator |
| Final merge decision | Aki |

Use the shared reconciliation mixin for judgment and typed tools for mutation. It inspects affected destinations, applies current preferences, asks about ambiguity, preserves identities and verifies partial results. It does not scan every system on every message or bypass vault boundaries.

tasks.md remains the canonical register with school, projects, personal, career and systems as primary areas. Existing backlog files require deliberate migration into it. Full /tasks output is lossless; scheduled summaries are concise and linked. Calendar-only social plans, tasks-only quick work and linked school deadlines remain editable preferences.

Source identity separates an announcement, a notification attempt and a task operation. Canvas assignment creation, changed dates and supported submission outcomes reconcile through stable links. A notice being delivered is not evidence that a task was created. Read-only imported calendars cannot be treated as owned writable events.

Current explicit instructions outrank learned preferences. "Show me the file" defaults to its viewer link. "Paste the contents" overrides it. "This one" does not establish a category rule. Missing values and unclear matches ask or remain pending.

## Evidence and daily learning

Capture original user messages, revisions, assistant claims and observed results before governed mutations. Session logs remain readable summaries, not the only source. Legacy TGDB export stays off while the durable capture replacement ships.

Explicit corrections are immediately available through scoped context. Daily consolidation runs at 03:00 Asia/Manila using Gemini 3.8 Flash and posts a short receipt in achiNouncements. Process only new/pending records with a checkpoint. Keep the existing 24-call daily review ceiling, retries included, single inference-only reviewer and bounded inputs/time. Idle review uses zero model calls. No premium fallback silently consumes a different allowance.

Each lesson retains source, scope, exceptions and revision. Validate proposals before activation. Shared skills and agent rules still require reviewed changes. Record retrieval and actual application separately so the weekly achiNouncements report can show whether a lesson helped. Its weekly time remains configurable; Sunday 20:00 Manila is a proposed default.

Use Terra medium as the foreground trial and Flash for background review. Record actual model and effort. Retain the held-out corpus, explicit-case pass requirement, 90 percent paraphrase threshold, no-unauthorized-write gate, staged activation, recovery checks and seven-day/ten-opportunity reuse evidence from the earlier plan. A smarter model or a stricter prompt alone is not a correctness guarantee.

## Reliable completion and persistence

A verified completed issue or directly linked merged PR can complete its task. SHIP, HITL Pass/Skip and abandoned drafts cannot. Explicit user completion applies to the identified item and established related records. Multiple observations produce one debrief entry. Reopened work and concurrent human edits require supported reconciliation or a conflict.

Task/log/Sciel/Ara updates commit and push automatically within authorized repositories. Preserve unrelated files and hunks, run required checks, respect branch rules and verify remote commit identity. Saved, committed and pushed remain distinct. No force-push or deletion of someone else's work is implied.

## Human testing and job control

Only Luna SHIP auto-queues required HITL after current CI. SHIP WITH FIXES always repairs, with an explicit nits-only bypass to testing. One Testing Grounds slot owns an isolated daemon; cards for standalone PRs and /ToWork jobs share its queue. Preparation must verify the exact revision, startup, bindings and isolated Calendar/vault/cache destinations before reporting ready.

Every required human test has a copy-paste checklist and expected/actual fields. Pass reaches Aki merge readiness. Failure returns to writer, CI and Luna. Skip records skipped evidence. New commits invalidate old acceptance. No testing result merges automatically.

Paused jobs can change both role models and efforts without changing topic defaults. Abandon stops execution, preserves dirty work, drafts the PR and tracks cleanup separately. New attempts can continue saved work or start fresh without deleting the old attempt. Confirm stopped ownership and preservation before reusing workers.

## Notifications and incident handling

Keep 08:00 morning and midnight debriefs, existing task checkpoint times and existing email routes. Use explicit Manila windows. Checkpoints send changes/newly due reminders rather than an unchanged list. Every email entry carries its original source link. Fix the weekday literal independently before the broader digest work.

Capture and group runtime failures, check existing tickets and automatically file supported defects. Rate-limit duplicates and separate unknown causes, workarounds, merged fixes, deployment and verification. No ticket auto-starts a worker. Health claims require evidence; missing logs are not proof of health.

## Verification and remaining decisions

The roadmap names ticket-level tests and live gates. Implementation uses repository-supported commands and preserves independent automated, live and deployed receipts. This planning PR does not satisfy runtime acceptance.

The weekly report's exact day/time remains an operator configuration choice. Cross-engine skill loading and the inference-only Flash transport require implementation verification. Future additional simultaneous Testing Grounds slots and a control-board frontend are deferred. No broad permission expansion is approved.
