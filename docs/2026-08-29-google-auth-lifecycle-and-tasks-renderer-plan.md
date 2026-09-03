# Google auth lifecycle and /tasks renderer plan

Date: 2026-08-29
Status: superseded on 2026-09-03
Owner: Aki

Superseded by the [unified AIS-OS open tickets implementation plan](http://100.106.210.38:8999/Code/GitHub/AIS-OS/.hermes/plans/2026-09-03_052750-unified-ais-os-open-tickets.md). This document remains as the record of the original ticket decomposition and the decisions that produced it.

## Why this exists

Two problems surfaced together, and they share a root: achiOS has silent failure modes where
it should have loud ones.

**Google auth.** All three legacy token files (`~/.config/achios/google_token.json`,
`google_token_dlsu.json`, `google_token_work.json`) are dead. A live refresh attempt on each
returns `invalid_grant: Token has been expired or revoked`. Their stored expiry stamps are
2026-08-23 and 2026-08-24, five and six days before this was noticed. The cause is that GCP
project `achiclaude` keeps its OAuth consent screen in Testing, and Google kills refresh
tokens for Testing apps after seven days.

The calendar and email digests survived this because they call the `gws` CLI first and only
fall back to token files when the `gws` binary is absent. The four `gws-*` profiles refreshed
today at 09:30 and are healthy. So the legacy path is dead weight that has been dead for five
days without a single alert.

`gcal_add.py` did not survive. It reads token files only, with no `gws` path at all.
`gcal_add.py --list` fails right now. Every dated task written to `tasks.md` since 2026-08-24
was recorded in the register and silently never created as a calendar event.

**`/tasks`.** `achiAgy/src/bot.py:1684` `cmd_tasks` does not render anything. It calls
`_start_session_turn(session_key, update, "/tasks")`, handing the literal string `/tasks` to
whatever model the session is on. Output structure changes every invocation because nothing
constrains it. `cmd_etf` in the same file does it correctly: it shells out to a real script
and reports the exit code.

## Decisions taken

Reached by grilling on 2026-08-29. Each was put to Aki explicitly.

### Auth strategy

**Accept the 7-day cycle. Do not publish the consent screen to Production.** Publishing would
remove the 7-day cap outright and cost nothing, but Aki declined it: no domain, no appetite
for the unverified-app warning path. So the design assumes tokens die weekly by construction,
and everything else follows from that.

**`gws` is the one true auth path.** The legacy token path gets deleted, not repaired.

A fact that constrains this: **`gws` credentials cannot be handed to Python's `google-auth`.**
`token_cache.json` is ciphertext, not JSON, encrypted by the `.encryption_key` beside it.
achiOS can only reach those credentials by shelling out to the `gws` binary. This is already
how `daily_brief.py` and `email_digest.py` work.

The write path exists. `gws calendar events insert --json '<body>' --params '{"calendarId":"..."}'`
gives raw API access, which covers all-day events. The `+insert` helper alone does not, because
it requires `--start` and `--end` with no all-day flag.

### Re-auth flow

Keep Aki's existing flow as the baseline: run the four `gws auth login` commands on the Mac,
each with its own `GOOGLE_WORKSPACE_CLI_CONFIG_DIR` (`gws-main`, `gws-personal`, `gws-work`,
`gws-dlsu`) and `GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file`, scoped `--services=gmail,calendar`.
Then copy the four config directories up to achibuntu.

**Test a server-only alternative before committing to that copy step.** `gws auth login` has no
device-code flow, browser only, but the browser only has to reach a localhost port on the
machine holding the credentials. From the Mac, `ssh -L <port>:localhost:<port> achibukz@achibuntu`,
run the four logins inside that session, paste the printed consent URL into the Mac's browser,
and the redirect travels back down the tunnel. Credentials land on achibuntu directly and
nothing is copied. **Open risk: `gws` may bind a random port each run, which breaks a fixed
`-L` forward.** Aki deferred this test to after planning. If the port is random, the copy flow
stands and the reminder ships all five commands as one copy-pasteable block.

### Health check

Reactive and proactive, in one script, per profile.

Reactive proves the credential works, and read and write are separate failures. A successful
`gws calendar +agenda` does not prove `events insert` will succeed, and `insert` is what
`gcal_add.py` depends on. So per profile: one read call, one dry-run write, and a Gmail read
for the three profiles carrying mail. Four profiles, each named individually in any alert.

Proactive computes days since `credentials.enc` mtime and warns before the wall.

Cadence is both fixed and drifting, and they do different jobs:
- Fixed Sunday 09:00 Manila is the routine re-auth nudge, so it becomes habit.
- The mtime-driven warning is a safety net that speaks only when a profile is inside 48 hours
  of the 7-day wall. If Aki re-auths every Sunday it never fires, which is the point.

Alerts go to `achinouncements` (`@achiOSBot`), same as every other scheduled job. No fifth bot.

### Digest behaviour while auth is dead

**Keep sending, with a one-line banner naming the dead profiles.** Suppressing the digest would
also cost the tasks half of the daily brief, which needs no Google credential and works fine.
Silence is what let this run five days unnoticed, so the fix must not add more silence.

### `/tasks` renderer

**Fixed skeleton, dynamic labels.** Deadline sections (overdue, due today, upcoming) stay
constant and are computed in Python. Deadlines are objective and never a model's call. The
model groups only the undated remainder into themes it chooses, which is where `tasks.md`
genuinely is a mess and where dynamic grouping earns its cost.

**One renderer, two callers.** Refactor `build_focused_digest` in `scripts/tasks_digest.py`
into an importable function. The cron and `cmd_tasks` both call it, so they cannot drift.

**Pinned to `gemini-3.7-flash-high`** as a dedicated call, not a full agy session turn.

**Deterministic fallback.** If the model call fails, times out, or returns a shape that does
not validate, send the deterministic card. Same degradation contract `daily_brief.py` already
earned.

**Replies in chat.** Aki types `/tasks` to see them now. Bouncing him to another bot to read
the answer is friction `/etf` only tolerates because the ETF card belongs in a finance log.

### `/status` cleanup

Strip all emoji. Drop the `achiCore Status Report` title, since the command already says what
it is. Flat `Label: value` list, no bold, blank lines between the session block and the host
block. Keep `<code>` on values, where monospace does real work.

The current block also mixes emoji-prefixed lines with one bare bullet for Engine, and bolds
every label, which by Aki's own rules means none of them are emphasis.

## Known bugs this fixes

1. `gcal_add.py` is dead. Dated tasks since 2026-08-24 have no calendar events. Aki reads the
   calendar on his phone, so the register alone has not been reaching him.
2. `/tasks` output structure is unconstrained and changes per invocation.
3. `tasks_digest.py` bucketing drops tasks silently. A task dated more than 30 days out falls
   into `other_tasks` and is never printed. A `!high` task that carries a date never reaches
   the high-priority section. The caps of 4 and 5 mean the visible set shifts depending on
   what else happens to be dated.
4. The legacy token fallback path is untested and was dead for five days undetected.

## Work breakdown

Published 2026-08-29 as seven tickets, all AFK, all labelled `ready-for-agent`.

| Issue | Work | Repo | Blocked by | Model |
|---|---|---|---|---|
| [#3](https://github.com/achibukz/AIS-OS/issues/3) | Fix the failing `test_daily_brief` suite | AIS-OS | none | flash-high |
| [#4](https://github.com/achibukz/AIS-OS/issues/4) | Port `gcal_add.py` to the gws CLI | AIS-OS | none | sonnet-5 |
| [#5](https://github.com/achibukz/AIS-OS/issues/5) | Build the Google auth health check and its timer | AIS-OS | none | flash-high |
| [#6](https://github.com/achibukz/AIS-OS/issues/6) | Extract a shared tasks renderer and stop dropping tasks | AIS-OS | none | sonnet-5 |
| [#7](https://github.com/achibukz/AIS-OS/issues/7) | Delete the legacy Google token path | AIS-OS | #3, #4, #5 | flash-high |
| [#8](https://github.com/achibukz/AIS-OS/issues/8) | Warn in the digests when a gws profile is dead | AIS-OS | #5, #7 | flash-high |
| [#57](https://github.com/achibukz/achiCore/issues/57) | Rewrite `cmd_tasks` to use the shared renderer, strip emoji from `cmd_status` | achiCore | AIS-OS #6 | flash-high |

### Dependency order

Four tickets start immediately and run in parallel: #3, #4, #5, #6.

```
#3 ─┐
#4 ─┼─► #7 ─► #8
#5 ─┘   ▲
        └── #5 also feeds #8 directly

#6 ─────► achiCore #57
```

`#4` goes first among the parallel four in practice, because `gcal_add.py` is a live bug and
every dated task added today is still failing to reach the calendar.

`#7` cannot start until `#3` is green, or the deletion ships with no regression net on
`daily_brief.py`. It also waits on `#4`, because deleting the token path before `gcal_add.py`
has a gws path leaves calendar writes with no implementation at all.

`#8` waits on `#7` rather than running beside it, since both edit the same two files.

### Not tickets

- The achiCore #41 comment, posted 2026-08-29. Frames per-call graceful degradation as a
  second fallback class alongside engine-level quota failover.
- The SSH port-forward re-auth test. Needs Aki's Mac and a browser, so it lives in `tasks.md`.
- The constrained `gemini-3.7-flash-high` grouping pass for undated tasks. Deliberately held
  back. `#6` ships deterministic-only, and the model pass is worth reopening once the
  deterministic card is visible and can be judged.

### Profile resolution for gcal_add.py

Search `calendarList` across all four profiles at call time in the order
`personal, work, main, dlsu`, first writable match wins. Cache nothing. A hardcoded
calendar-to-profile map goes stale the moment a calendar is shared differently, and `--list`
already does the same walk.

Aki's calendars are spread across accounts: `ING`, `DLSU`, the course calendars
(`CSOPESY`, `THS-ST1`, `STCLOUD`, `PEDFOUR`, `STSP001`, `LSCS`), `Job`, `Bdayy`, `Family`,
`Personal`. Routing by subject is defined in `CLAUDE.md` and does not change here.

## On achiAgy #41

#41 covers engine-level quota failover: an engine hits its wall, fail over to another model.
The `/tasks` case is a second and narrower class: one pinned call that must degrade to a
deterministic path when it fails, times out, or returns an invalid shape. Related enough to
share a ticket, and keeping them together stops two unrelated retry mechanisms being built.
Goes on #41 as a comment, not a new ticket.

## Deliberately not doing

- **Publishing `achiclaude` to Production.** The actual root fix, declined by Aki. Revisit if
  the weekly re-auth becomes a chore he resents.
- **A service account.** Cannot read personal Gmail or Calendar without Workspace
  domain-wide delegation, which Aki does not control for gmail.com and probably not for DLSU.
- **A token rotation script.** No amount of scripting revives a refresh token Google
  deliberately kills at day 7.
- **A fifth Telegram bot for auth alerts.** One message a week does not earn its own channel.

## Open

- The SSH port-forward test. Decides whether the manual copy step survives.
- DLSU is a Workspace account and its admin can restrict app access independently. If it
  breaks alone, the school email digest needs a separate answer.
- `tests/test_daily_brief.py` fails against the refactored module, predating this work. Items
  2 and 4 both touch `daily_brief.py`, so that has to be resolved first or those changes ship
  untested.
