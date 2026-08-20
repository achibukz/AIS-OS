# State

_Updated 2026-08-21 02:40 Manila. Previous state (server buildout Phase 8, 2026-08-17) is summarised
under "Carried forward" — the still-open items were preserved, the completed ones dropped._

## Current Goal

Self-learning loop v2 is **done, deployed, and verified live**. Trial week runs to the
2026-08-27 audit. No active build task.

## Plan Status

Plan `docs/superpowers/plans/2026-08-20-self-learning-loop-v2.md` — all 8 tasks complete,
Task 8 live test **passed 2026-08-21**: capture, turn-10 trigger, gate, and write all
worked; filler messages correctly ignored.

Test procedure and how to read the output: `docs/2026-08-21-self-learning-loop-test-guide.md`.
Future work, ranked: `docs/ROADMAP.md`.

Also shipped this session, outside the plan:
- `3bc7870` achiAgy `import re` — the HTML send fallback always raised NameError.
- `eeb8729` + `23fce8f` CLI writes recorded in the ledger as `source: cli`, excluded
  from the loop's daily budget.
- `c9cb99f` telegram_notify retry/backoff plus token redaction, and
  `Restart=on-failure` on the six Telegram units. `systemctl --user reset-failed` run,
  0 failed units.

Tests: AIS-OS 224 passed / 44 pre-existing failures. achiAgy 67 passed.
Both repos clean and pushed. `MEMORY.md` 207 chars, `USER.md` 1706 of 2500.

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

Ranked detail lives in `docs/ROADMAP.md`. The load-bearing ones:

- **Second memory writer is logged but ungated.** The agy model writes via the
  memory_engine CLI with no gate and no cap. The gate governs one of two paths in.
- **Recall gap.** Capture fires only on ~21 trigger phrases, so durable *facts*
  ("my thesis adviser is Briane Paul V. Samson") are never captured.
- **Failure alerts still share the network path they report on.** Retry helps; a long
  outage still loses the alarm. Store-and-forward is the real fix.
- `@achiOSBot` token still in journald cleartext from before the redaction fix; not
  rotated. `achiAgy/.env*` perms not tightened.
- 44 `test_daily_brief.py` failures (`parse_tasks` → `parse_active_tasks` rename), so
  the most user-visible component has no working regression net.
- `USER.md` at 1706/2500: at the ceiling the loop replaces the *oldest* entry, which is
  the Identity line.
- No concurrency guard in achiAgy; the loop now mutates session state from that path.

## Waiting on Aki

- Whether the dated tasks from the infra audit should become calendar events.
- Which roadmap item to take next. Items 1 and 2 are the high-value ones.

## Carried forward (from 2026-08-17 buildout)

- `achibuntu` is live and healthy; runbook Phases 0-7 complete.
- Phase 8 "pull the power cord" is **blocked, not pending** — no battery is fitted, so mains
  loss is an instant power-off. This is why every timer needs `Persistent=true`. Already
  recorded permanently in `CLAUDE.md`; kept here only because the check can never pass as
  written.
