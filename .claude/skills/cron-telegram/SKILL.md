---
name: cron-telegram
description: Use this whenever Aki wants something to happen on a schedule and land in his Telegram. Triggers on "make a cron that…", "every morning send me…", "at 1pm search for X and message me", "remind me daily about…", "schedule a job that…", "have it check X every hour and tell me", or any request naming a time of day plus an outcome he wants delivered to his phone. Also use it when he asks to change, inspect, or remove an existing scheduled job, or when a cron he already has is not firing. Covers the whole path: the Telegram bot credentials, the systemd user timers on the achibuntu server (cron is not used there — it ignores CRON_TZ), the Python interpreter to use, and when a job should call a model instead of just running code.
---

# Scheduled jobs that report to Telegram

Aki runs a headless Ubuntu server (`achibuntu`) that owns his scheduled work. This skill
is the wiring diagram: what already exists, what to reuse, and the handful of traps that
cost real debugging time the first time round.

The shape of every job is the same. **A Python script produces text. A systemd timer runs it.
The text goes to Telegram.** Most of the work is deciding what the script does; the delivery
half is already solved and should be imported, not rewritten.

## Before writing anything, settle four questions

1. **What does it produce?** One message or several? Aki reads these on a phone at a
   glance, so the answer is usually "short, spaced out, one topic per message."
2. **Does it need a model?** See *Python or Sonnet* below. Default to no.
3. **When does it run?** In Manila time. He will say "1pm" and mean 1pm where he is, and
   the box runs UTC, so put `Asia/Manila` in the `OnCalendar=` line and let systemd convert.
4. **What happens when it fails?** A job that dies silently is worse than no job. Every
   job logs, and anything model-dependent falls back to a plain-text version.

Ask about anything genuinely ambiguous, but don't interview him over things with an
obvious default — daily at the stated time, one message, no model.

## The pieces that already exist

| Thing | Where | Notes |
|---|---|---|
| Telegram sender | `scripts/telegram_notify.py` | `from telegram_notify import send` — import it |
| Credentials | `~/.config/achios/telegram.env` | mode 600, outside the repo, never commit |
| Python | `~/.local/share/achios/venv/bin/python` | uv-managed; has `requests` + the Google libs |
| Google Calendar auth | `~/.config/achios/google_token*.json` | personal + work tokens, auto-refreshing |
| Schedules | unit files in `systemd/`, installed by `scripts/install_units.sh` | systemd **user** timers. Not cron — see below |
| Live units | `~/.config/systemd/user/` | generated copies. Edit `systemd/` and re-run the installer, never these |
| Log dir | `~/.local/state/achios/` | one `<job>.log` per job |
| Worked example | `scripts/daily_brief.py` | the fullest one; copy its shape |

`~/.hermes/` is a **different** agent stack with its own bot. Nothing here reads it, and
new jobs must not either — that separation is deliberate.

## Sending to Telegram

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from telegram_notify import send

send("first message", "second message")
```

`send()` reads the credentials, splits anything over Telegram's 4096-character limit at
blank lines, and raises `SystemExit` with the API's own error text if Telegram rejects
the payload. It returns how many messages actually went out.

**Send plain text, no `parse_mode`.** Markdown and HTML modes make Telegram reject the
whole message over a stray underscore or bracket, which is a miserable failure for an
unattended job. Structure with emoji, blank lines, and indentation instead — that reads
better on a phone anyway.

If the bot ever needs re-pairing: `python scripts/telegram_notify.py` prints the chat ids
that have messaged it, without echoing the token.

## Python or Sonnet

These jobs run unattended and forever, so the bar for adding a model is real.

**Plain Python** covers most jobs: reading files, hitting an API, filtering, counting,
formatting. It is instant, free, and cannot hallucinate. Reach for this by default.

**Add a `claude -p` call** when the job needs judgment that code cannot express —
rewriting text so it reads like a person wrote it, summarising something long,
researching an open question, deciding what actually matters today. If a request is
literally "search for X and tell me" or "chat about X," that is a model job.

When a job does call a model:

```python
subprocess.run(
    [
        "claude", "-p", prompt,
        "--model", "claude-sonnet-5",
        "--allowed-tools", "",
        "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
    ],
    capture_output=True, text=True, timeout=300,
    cwd=Path.home() / ".local" / "share" / "achios" / "llm",
)
```

Five details in there matter, and each one was learned the hard way:

- **`cwd` is a bare directory with no `CLAUDE.md`.** Run from the repo instead and the
  scheduled session loads the project instructions *and* fires the achiMem SessionEnd hook,
  writing a junk session log to Aki's vault every single night.
- **`--mcp-config '{"mcpServers":{}}'`**, not `'{}'` — the bare object fails validation.
  With `--strict-mcp-config` this keeps MCP servers out of a job that has no use for them.
- **`--allowed-tools ""`** for a pure text transform. If the job genuinely needs to search
  or read files, grant only what it needs.
- **Sonnet, pinned.** Aki's global default is Opus; a recurring background job does not
  warrant it. Pass `--model claude-sonnet-5` explicitly.
- **Always have a fallback.** Check the return code and fall back to the unpolished text.
  A degraded message beats silence, and the model step is the most likely thing to fail.

It runs on Aki's Claude subscription, not API billing. Expect 40–90 seconds per call, and
run several concurrently with a thread pool rather than in sequence.

## Scheduling: use a systemd user timer, not cron

**Do not use cron on this box.** Ubuntu's `cron 3.0pl1` does not support per-user
timezones, and it silently ignores `CRON_TZ`. From `man 5 crontab`:

> It currently does not support per-user timezones… Even if a user specifies the `TZ`
> environment variable in his crontab this will affect only the commands executed in the
> crontab, not the execution of the crontab tasks themselves.

The box runs `Etc/UTC`, so a crontab that *looks* like 8am Manila fires at 4pm Manila.
The daily brief shipped this way and never fired once. Verified two ways:
`grep -c CRON_TZ /usr/sbin/cron` → `0`, and a live probe armed in Manila time that never
went off.

systemd honours a named timezone directly, and — because this laptop is **batteryless** and
dies outright on any mains blip — `Persistent=true` re-runs a job that was missed while the
box was down, the moment it boots. Cron cannot do that. Both problems, one mechanism.

Units are version-controlled in `systemd/` and installed by `scripts/install_units.sh`,
which substitutes `@REPO@` for the repo root, expands nothing else, then reloads, enables
and lingers. Add a job by dropping two files in `systemd/` and re-running it:

```ini
# achios-<job>.service
[Unit]
Description=achiOS <job> -> Telegram
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
# Scripts that shell out to `claude` need it on PATH; a user unit's PATH is bare.
Environment=PATH=/home/achibukz/.npm-global/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/home/achibukz/.local/share/achios/venv/bin/python /home/achibukz/Code/GitHub/AIS-OS/scripts/<job>.py
StandardOutput=append:/home/achibukz/.local/state/achios/<job>.log
StandardError=append:/home/achibukz/.local/state/achios/<job>.log
TimeoutStartSec=10min
```

```ini
# achios-<job>.timer
[Unit]
Description=achiOS <job> at <time> Manila

[Timer]
OnCalendar=08:00 Asia/Manila
Persistent=true
AccuracySec=1min

[Install]
WantedBy=timers.target
```

```bash
./scripts/install_units.sh    # installs every unit in systemd/, then prints the timer table
```

Confirm `NEXT` in that table is the Manila time you meant, converted to UTC. Use `%h` for
anything under his home directory and `@REPO@` for anything in the repo, so the units carry
no absolute paths — check they expanded with
`systemctl --user show achios-<job>.service -p ExecStart`.

Rules that keep these jobs alive:

- **Check the calendar spec before trusting it**: `systemd-analyze calendar "08:00 Asia/Manila"`
  prints the next elapse in UTC. Read it and confirm it is the hour you meant.
- **No absolute paths in the committed unit** — `%h` for home, `@REPO@` for the repo. But
  never rely on `PATH` inside the unit; name the interpreter in full via `%h`.
- **Set `Environment=PATH=…`** if the script shells out to `claude` or any npm-global binary.
- **`Persistent=true` on every timer.** The box loses power without warning; a missed brief
  should arrive late, not never.
- **Append both streams to a log.** Without it, failures vanish into the journal.
- **`loginctl enable-linger achibukz`** must stay on or user timers stop when Aki logs out.
  It is currently on.

## Verify before calling it done

A job that was never run through its own unit is not finished. Four checks:

```bash
# 1. It runs, and produces what you expect
~/.local/share/achios/venv/bin/python scripts/<job>.py --dry-run

# 2. The schedule means what you think — read the UTC elapse and check the hour
systemd-analyze calendar "08:00 Asia/Manila"
systemctl --user list-timers achios-<job>.timer

# 3. It survives the unit's bare environment — the usual failure point
systemctl --user start achios-<job>.service
systemctl --user show achios-<job>.service -p Result -p ExecMainStatus

# 4. It actually reaches his phone — check the log, then ask him
tail ~/.local/state/achios/<job>.log
```

Run it through `systemctl --user start`, not just the interpreter. The two disagree about
`PATH`, and a script that shells out to `claude` passes by hand and fails under the unit.

Give every job a `--dry-run` that prints instead of sending, so it can be exercised
without spamming him. Then tell him it sent and ask him to confirm it arrived — only he
can see the phone.

If a job is not firing, in this order: `systemctl --user list-timers --all` (is `NEXT` the
hour you meant?), its log, `systemctl --user status achios-<job>.service`, then
`loginctl show-user achibukz | grep Linger`.

## Things that will bite

- **Long shell commands wrap in his terminal** and the wrapped remainder gets executed as
  a separate command. Anything he has to paste should fit one line, or better, go in a
  script with a short invocation.
- **Never print a bot token or ask him to paste one into chat.** It ends up in the
  transcript, which achiMem captures into a git repo. If one leaks, the fix is BotFather
  `/revoke`, and say so immediately.
- **A green exit code is not a working job.** `daily_brief.py` once called an undefined
  `polish_all` and the failure sat unnoticed in a log nobody read, because the schedule was
  wrong and it had never actually run. Check the log has a success line, not just an exit 0.
- **`--user` on every `systemctl` call.** These are user units; the system manager knows
  nothing about them and the error message does not make that obvious.
- **Tests are not optional.** Parsing and formatting logic goes in `tests/`, mirroring
  `tests/test_daily_brief.py`. These jobs run unattended, so a silent format regression
  can go unnoticed for weeks.

## After it ships

Record it, or the next session rediscovers all of this:

- A row in `connections.md` if it reaches a system not already listed.
- A short section in `CLAUDE.md` under the daily brief: what it does, when it fires, where
  it logs, how to preview it.
- A line in `decisions/log.md` if a real tradeoff was made (model choice, schedule, what
  gets left out).
