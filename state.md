# State

_Updated 2026-08-21 02:05 Manila. Previous state (server buildout Phase 8, 2026-08-17) is summarised
under "Carried forward" — the still-open items were preserved, the completed ones dropped._

## Current Goal

Self-learning loop v2: **all 8 tasks implemented and committed.** Live on the box.
Remaining: Task 8 steps 2-4 (a real Telegram turn test) need Aki at his phone.

## Plan Status

Plan: `docs/superpowers/plans/2026-08-20-self-learning-loop-v2.md` — Tasks 1-8 done.
Commits: `add9695` ledger, `603ec71` prefilter, `bc1c1ba` gate, `e997a25` v1 deleted,
`e7a3238` archive+purge, `8521a9a` audit scheduled (AIS-OS); `93a206a` review
orchestration, `d28a413` turn wiring (achiAgy).

Tests: AIS-OS 209 passed / 44 pre-existing failures. achiAgy 59 passed.
`achi-agy.service` restarted and polling.

**Open verification:** Task 8 steps 2-4 — send ~10 messages to `@achiAgyOSBot`
including one real preference, then check `learning_ledger.stats()` and
`~/.config/achios/MEMORY.md`. Substituted a sandboxed end-to-end run against the
real agy gate, which passed; the live-turn path itself is still unexercised.

## Evidence

- `agy --json-schema` works. Verified: gemini-3.7-flash-high correctly returned `one_off` for
  "can you make it less formal like this:", "buy google ai pro on october 14", and the
  recursive `"Voice register adjustment: Voice register adjustment: …"` line, and `durable`
  for "never use the word leverage in my emails".
- Cost of one gate call: 20,836 input tokens, ~7s. agy's own system prompt dominates, so cost
  is per-call not per-candidate.
- `prompt` and `full_prompt` are separate variables in `execute_agent_pipeline`; only
  `full_prompt` receives the frozen memory. This is what makes v2's approach work.
- Hermes cadence: `_memory_nudge_interval = 10` (`agent_init.py:1744`); review suppressed for
  cron at `turn_finalizer.py:788`.
- Live damage from v1: 3 of 5 `MEMORY.md` entries recursive; 54 of 86 `decisions/log.md`
  entries machine-generated.

## Open Issues

- **Recall gap:** the prefilter only fires on trigger phrases, so a durable *fact*
  ("my thesis adviser is Briane Paul V. Samson") is dropped before the gate sees it.
  Verified 2026-08-21. This is the recall question for the day-7 audit.
- **No dedup:** the same preference stated twice writes two near-identical entries.
  Self-corrects at the budget ceiling via `replace`, but wastes budget.
- `ledger._transition` silently no-ops on an unknown id, leaving a candidate pending
  and re-billed at each review. Only reachable if the ledger is truncated mid-flight.
- No ledger rotation; `_latest_by_id` parses the whole file per call.
- `memory_gate._default_runner` passes candidate text via argv, so it is briefly
  visible in `ps`.
- Ten P0/P1 fixes from the infra audit are in `tasks.md` and untouched.
  `import re` in `achiAgy/src/bot.py:860` is a one-line fix for a guaranteed crash.
- 4 systemd units still `failed`; `systemctl --user reset-failed` not run.
- `@achiOSBot` token is in journald in cleartext, not yet rotated.
- 44 pre-existing `test_daily_brief.py` failures (`parse_tasks` rename).

## Waiting on Aki

- Run Task 8 steps 2-4: a live Telegram turn test against `@achiAgyOSBot`.
- Whether the dated tasks from the infra audit should become calendar events.

## Carried forward (from 2026-08-17 buildout)

- `achibuntu` is live and healthy; runbook Phases 0-7 complete.
- Phase 8 "pull the power cord" is **blocked, not pending** — no battery is fitted, so mains
  loss is an instant power-off. This is why every timer needs `Persistent=true`. Already
  recorded permanently in `CLAUDE.md`; kept here only because the check can never pass as
  written.
