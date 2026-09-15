# Meeting ingest cohesion discussion, September 15, 2026

Approved planning decisions from the #General discussion with Aki on September 15, 2026. This records requested behavior and the constraints found while reading the code. It is not a claim that anything shipped. Published issues and their order are in [the roadmap](astra-roadmap-2026-09-11.md). The surrounding cohesion plan is [astra-plan.md](astra-plan.md).

## What Aki asked for

When a Zoom or face-to-face meeting is ingested, the ingest should not stop at a wiki note. It should propose the announcements, tasks and deadlines that fall out of the meeting and route them to `tasks.md`, Google Calendar or wherever else the record belongs. Aki framed this as part of making achiOS cohesive rather than as a schoolMem feature.

He also asked that Sciel be able to delegate to or ask Asa for something, rather than only answering in its own thread.

## Decisions

1. Trigger scope is meetings first. Adviser meetings, group meetings, senior consultations and organisation face-to-face meetings. Ordinary lecture transcripts are excluded in this release because a lecture is full of unowned instructions like "read chapter 4" and would flood `tasks.md`. Class sessions get a narrower filter later, limited to an announced deliverable carrying a date.
2. Announcements split by whether they carry a date. A dated announcement becomes a task and its linked Calendar deadline. An undated announcement becomes a line in the subject's `_overview.md`, which Sciel already owns, so it needs no cross-topic handoff. No new announcements store is created.
3. Dates are never invented. A proposed date exists only when the source states it, or when a relative reference resolves against the meeting date. Unresolvable references ship undated. Resolution is Asia/Manila against an explicit source timestamp, matching [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13).
4. Every proposed record needs approval before it is written. No auto-apply tier in the first release, including for items with an explicit date and owner. Transcripts are noisy and a wrong Calendar entry lands on Aki's phone.
5. The work is split across three repositories: schoolMem for the extraction and the proposal format, AIS-OS for the adapter that submits proposals to the cohesion writer, achiCore for Sciel's ability to hand a request to Asa.

## Constraints found in the code

**Sciel cannot emit a delegate block today, and the failure is silent.** `dispatch_delegate_block` in achiCore `src/bot.py` returns early unless `topic_router.orchestrates(topic_key)` is true, and that reads the `orchestration` mixin from persona frontmatter. `agents/schoolmem.md` declares `[topic-isolation, sciel, communication, tailscale-links, outbound-media, reconciliation]`. The early return logs one TUI line and posts nothing, so the block disappears from the reply with no notice in the thread. The comment at that check states the intent: #achiMem, #schoolMem and #Ara execute rather than orchestrate. Aki typing `/delegate` himself is unaffected, because that path is authorized by the user.

**A returning hop is refused as circular.** `authorize_delegation` rejects a target already in the task's chain. If Asa delegates an ingest to Sciel, Sciel delegating back to Asa cannot run whatever its frontmatter says. Aki approved giving Sciel delegation anyway, so the two paths are specified separately: a Sciel turn Aki started delegates to Asa normally, and a Sciel turn Asa delegated returns its proposal in the receipt, which already reaches Asa through `summarize_outcome`.

**A rejected block loses its payload.** `format_delegate_rejection` renders the error only, and `strip_delegate_blocks` has already removed the block from the prose. A Sciel proposal that trips the cycle guard or the hop limit is therefore destroyed rather than surfaced. This is folded into the achiCore slice.

## Reuse, not a parallel mechanism

The extraction half already exists, scoped narrow. schoolMem's `CLAUDE.md` THESIS MEETING INGEST pulls new tasks, completed tasks, decisions, new blockers and resolved blockers, proposes a diff and waits for approval. It fires only for `raw/<Term>/THSST*/` and writes only the three `thesis/` files. This work generalises that routine and widens its destinations.

The writing half is [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13), which owns stable task identity, Calendar relationships and applied-versus-pending receipts. [AIS-OS #47](https://github.com/achibukz/AIS-OS/issues/47) is the same shape with Canvas assignments as the source, and [achiCore #148](https://github.com/achibukz/achiCore/issues/148) already carries context to Sciel and preserves return receipts. A meeting source is a sibling adapter on that writer, not a second reconciliation path.

## Audit findings not acted on

The September 11 batch recommends `gpt-5.6-terra` in its Recommended model sections. That key is not in achiCore's current `MODEL_REGISTRY` in `src/config.py`; the registered Codex key is `gpt-6-astra`. The stale key was left in place on those tickets rather than mass-edited during this planning turn. It needs a decision from Aki.

schoolMem had no `ready-for-agent` or `priority:*` labels before this batch.
