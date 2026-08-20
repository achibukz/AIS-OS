# State

_Updated 2026-08-20 18:40. Previous state (server buildout Phase 8, 2026-08-17) is summarised
under "Carried forward" — the still-open items were preserved, the completed ones dropped._

## Current Goal

Self-learning loop v2: design approved, spec written, **plan written**. Ready to execute.

## Plan Status

Spec: `docs/superpowers/specs/2026-08-20-self-learning-loop-design.md` — approved.
Plan: `docs/superpowers/plans/2026-08-20-self-learning-loop-v2.md` — 8 tasks, ready to execute
via `subagent-driven-development`. Implementation is Gemini 3.7 Flash's job per `.agentrules` §6.

**v1 harvester is dead** (commit `fbffe37`) — call site removed from `vault_inbox_sync.py`,
`MEMORY.md` checksum verified stable across a full non-dry run. Spec §10 cutover step 2 is
done; the plan says not to redo it.

Task order: 1 ledger → 2 gate prefilter → 3 gate classify → 4 review orchestration →
5 wire into bot.py → 6 delete extract_corrections → 7 archive+purge → 8 deploy+verify.
Tasks 7 and 8 must come last: purging before the new loop is deployed is safe now that v1
is dead, but the live verification in Task 8 depends on Task 7's clean baseline.

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

- `MEMORY.md` still holds the 3 recursive entries and `decisions/log.md` the 54 harvested
  ones. Inert now that v1 is dead, but Task 7 cleans them.
- Ten P0/P1 fixes from the infra audit (`docs/2026-08-20-opus-audit-achios-achiagy.md`) are in
  `tasks.md` and untouched. `import re` in `achiAgy/src/bot.py` is a one-line crash fix.
- 4 systemd units still in `failed` state; `systemctl --user reset-failed` not run.
- `@achiOSBot` token is in journald in cleartext, not yet rotated.
- Ten tasks added today carry dates I chose, not Aki. No calendar events created for them —
  needs his confirmation before they go to `Personal`.

## Waiting on Aki

- Approve executing the plan (subagent-driven, 8 tasks).
- Whether the dated tasks should become calendar events.

## Carried forward (from 2026-08-17 buildout)

- `achibuntu` is live and healthy; runbook Phases 0-7 complete.
- Phase 8 "pull the power cord" is **blocked, not pending** — no battery is fitted, so mains
  loss is an instant power-off. This is why every timer needs `Persistent=true`. Already
  recorded permanently in `CLAUDE.md`; kept here only because the check can never pass as
  written.
