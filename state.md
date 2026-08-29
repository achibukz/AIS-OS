# State

_Updated 2026-08-29 11:15 Manila. The self-learning-loop v2 state from 2026-08-21 is summarised
under "Carried forward" — still-open items preserved, completed ones dropped._

## Current Goal

Ship the Google auth lifecycle and /tasks renderer batch. Plan:
`docs/2026-08-29-google-auth-lifecycle-and-tasks-renderer-plan.md`. Seven tickets published
2026-08-29, one already closed.

## Plan Status

| Issue | Work | Status |
|---|---|---|
| AIS-OS #3 | Fix the failing `test_daily_brief` suite | open, unblocked |
| AIS-OS #4 | Port `gcal_add.py` to the gws CLI | **closed 2026-08-29** |
| AIS-OS #5 | Google auth health check and timer | open, unblocked |
| AIS-OS #6 | Shared tasks renderer, stop dropping tasks | open, unblocked |
| AIS-OS #7 | Delete the legacy Google token path | blocked by #3, #4, #5 |
| AIS-OS #8 | Dead-profile banner in the digests | blocked by #5, #7 |
| achiCore #57 | `cmd_tasks` shared renderer, strip `/status` emoji | blocked by AIS-OS #6 |

#3, #5 and #6 can run in parallel right now.

The decision that shapes all of it: accept the seven-day Testing-mode token cycle rather than
publish `achiclaude` to Production, and make `gws` the only auth path. Recorded in
`decisions/log.md`.

## Evidence

- All three `~/.config/achios/google_token*.json` files return `invalid_grant` on a live
  refresh. Stored expiry 2026-08-23 and 2026-08-24, unnoticed for five days.
- The digests survived because they call `gws` first and only fall back to token files when the
  binary is absent. `gcal_add.py` had no gws path and failed outright.
- gws `token_cache.json` is ciphertext keyed by `.encryption_key`, so `google-auth` can never
  load those credentials. Shelling out to the binary is the only way in.
- `gws calendar events insert --json` writes all-day events. The `+insert` helper cannot: it
  requires `--start` and `--end`.
- `gws auth login` has no device-code flow, browser only.
- `cmd_tasks` at `achiCore/src/bot.py:1684` passes the literal string `/tasks` to a model.
  `cmd_etf` in the same file shells out to a real script, which is the pattern to copy.
- Post-port verification: `--list` returns 30 writable calendars across all four profiles,
  insert writes `start.date` with reminders off, a rerun is a no-op, unknown calendar exits 1.
  `tests/test_gcal_add.py` 21 passed.

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
  the most user-visible component has no working regression net. Now ticketed as AIS-OS #3,
  and it blocks #7.
- **The gws credentials hit their own seven-day wall around 2026-09-04.** Nothing will say so
  until #5 lands. If the calendar goes quiet next weekend, that is why.
- `tasks_digest.py` silently drops tasks: dated more than 30 days out, or `!high` with a date.
  Ticketed as AIS-OS #6.
- `USER.md` at 1706/2500: at the ceiling the loop replaces the *oldest* entry, which is
  the Identity line.
- No concurrency guard in achiAgy; the loop now mutates session state from that path.

## Waiting on Aki

- The `ssh -L` port-forward re-auth test. Needs his Mac and a browser. Decides whether the
  credential copy step survives.
- Whether the overdue dated tasks from 2026-08-27 and 2026-08-28 should get calendar events.
  Two future ones were backfilled (BPI on ING for 09-02, learning architecture on Personal for
  08-30). Two more turned out to already exist under different wording, so the duplicates I
  created were deleted. Past-due ones were left alone.
- Whether the original "Plan and implement automated weekly Google OAuth token refresh" task
  in `tasks.md` should be closed now that it is superseded by the ticket batch.
- Which roadmap item to take after this batch. Items 1 and 2 are the high-value ones.

## Carried forward (from 2026-08-21 self-learning loop v2)

Loop v2 is done, deployed and verified live. Plan
`docs/superpowers/plans/2026-08-20-self-learning-loop-v2.md` all 8 tasks complete, Task 8 live
test passed 2026-08-21. Test procedure: `docs/2026-08-21-self-learning-loop-test-guide.md`.
`prompt` and `full_prompt` stay separate variables in `execute_agent_pipeline`; only
`full_prompt` carries the frozen memory, and that separation is what stops v1's self-amplifying
recursion. Do not merge them.

## Carried forward (from 2026-08-17 buildout)

- `achibuntu` is live and healthy; runbook Phases 0-7 complete.
- Phase 8 "pull the power cord" is **blocked, not pending** — no battery is fitted, so mains
  loss is an instant power-off. This is why every timer needs `Persistent=true`. Already
  recorded permanently in `CLAUDE.md`; kept here only because the check can never pass as
  written.
