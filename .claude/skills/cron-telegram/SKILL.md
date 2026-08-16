---
name: cron-telegram
description: Use this whenever Aki wants something to happen on a schedule and land in his Telegram. Triggers on "make a cron that…", "every morning send me…", "at 1pm search for X and message me", "remind me daily about…", "schedule a job that…", "have it check X every hour and tell me", or any request naming a time of day plus an outcome he wants delivered to his phone. Also use it when he asks to change, inspect, or remove an existing scheduled job, or when a cron he already has is not firing. Covers the whole path: the Telegram bot credentials, the crontab on the achibuntu server, the Python interpreter to use, and when a job should call a model instead of just running code.
---

# Scheduled jobs that report to Telegram

Aki runs a headless Ubuntu server (`achibuntu`) that owns his scheduled work. This skill
is the wiring diagram: what already exists, what to reuse, and the handful of traps that
cost real debugging time the first time round.

The shape of every job is the same. **A Python script produces text. Cron runs it. The
text goes to Telegram.** Most of the work is deciding what the script does; the delivery
half is already solved and should be imported, not rewritten.

## Before writing anything, settle four questions

1. **What does it produce?** One message or several? Aki reads these on a phone at a
   glance, so the answer is usually "short, spaced out, one topic per message."
2. **Does it need a model?** See *Python or Sonnet* below. Default to no.
3. **When does it run?** In Manila time. He will say "1pm" and mean 1pm where he is.
4. **What happens when it fails?** A cron that dies silently is worse than no cron. Every
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
| Crontab | `crontab -l` for user `achibukz` | `CRON_TZ=Asia/Manila` is set at the top |
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

Cron runs unattended and forever, so the bar for adding a model is real.

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
  cron session loads the project instructions *and* fires the achiMem SessionEnd hook,
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

## The crontab

The box runs **UTC**; Aki thinks in **Manila**. `CRON_TZ=Asia/Manila` sits at the top of
his crontab so schedules can be written in local time. Keep it there and keep new jobs
under it.

```
CRON_TZ=Asia/Manila
MAILTO=""

# achiOS daily brief -> Telegram, 08:00 Manila
0 8 * * * /home/achibukz/.local/share/achios/venv/bin/python /home/achibukz/Code/GitHub/AIS-OS/scripts/daily_brief.py >> /home/achibukz/.local/state/achios/daily_brief.log 2>&1
```

To add a job, read the current crontab, append, and install the whole thing — never
hand-edit the spool file:

```bash
crontab -l > /tmp/cron.txt
# append the new line to /tmp/cron.txt
crontab /tmp/cron.txt
crontab -l          # confirm it took
```

Rules that keep these jobs alive:

- **Absolute paths everywhere**, interpreter included. Cron's `PATH` is nearly empty.
- **Redirect to a log** (`>> …log 2>&1`). Without it, failures vanish.
- **`MAILTO=""`** so cron doesn't try to mail output on a box with no mailer.
- **One comment line** above each entry saying what it is and in which timezone.
- **Never `%` unescaped** in a cron command — cron turns it into a newline. Escape as `\%`.

## Verify before calling it done

A cron job that was never tested under cron's environment is not finished. Three checks:

```bash
# 1. It runs, and produces what you expect
~/.local/share/achios/venv/bin/python scripts/<job>.py --dry-run

# 2. It survives cron's stripped environment — the usual failure point
env -i HOME=/home/achibukz PATH=/usr/bin:/bin \
  /home/achibukz/.local/share/achios/venv/bin/python \
  /home/achibukz/Code/GitHub/AIS-OS/scripts/<job>.py --dry-run

# 3. It actually reaches his phone
~/.local/share/achios/venv/bin/python scripts/<job>.py
```

Give every job a `--dry-run` that prints instead of sending, so it can be exercised
without spamming him. Then tell him it sent and ask him to confirm it arrived — only he
can see the phone.

If a job is not firing: check `crontab -l`, then its log, then `systemctl is-active cron`,
then re-run check 2 above. In that order, because the environment is the usual culprit.

## Things that will bite

- **Long shell commands wrap in his terminal** and the wrapped remainder gets executed as
  a separate command. Anything he has to paste should fit one line, or better, go in a
  script with a short invocation.
- **Never print a bot token or ask him to paste one into chat.** It ends up in the
  transcript, which achiMem captures into a git repo. If one leaks, the fix is BotFather
  `/revoke`, and say so immediately.
- **`crontab` writes can be blocked by the sandbox.** If it fails with a confusing path
  error, that is why.
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
