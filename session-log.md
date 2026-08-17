# Session Log

## 2026-08-17 03:45 [saved]
Goal: Turn the old HP laptop into a headless Hermes/Claude Code agent host.

Decisions:
- `commit()` in `achimem_capture.py` now rebases, pushes, retries once, and **aborts** a conflicting rebase — two machines append to `log.md`, so conflicts are unresolvable unattended.
- `sync-claude-config.sh` uses an **allowlist**, not a denylist — a future credential file dropped in `~/.claude/` cannot leak by default.
- Plugins are excluded from the sync; `enabledPlugins` in `settings.json` refetches them, avoiding a 333 MB transfer.
- Hermes `write_approval: true` on memory and skills — both default false, and a sub-70B model is running autonomously.
- Ubuntu **Server**, not Desktop — desktop power daemons actively fight the lid-close override an always-on box needs.

Rejected:
- `pip list` as evidence of a missing package — uv venvs have no `pip`.
- `| bash --flag` for piped installers — bash eats it; use `bash -s -- --flag`.
- Auto-merging the vault's append-only log unattended — risks silent mangling.

Open:
- Phase 8 unfinished: cron round-trip, power-cut test.
- SSH password auth still enabled on the server.

## 2026-08-17 04:30 [saved]
Goal: Port Claude Code writing skills to Hermes on the server.

Decisions:
- Copy chosen skills into `~/.hermes/skills/` rather than pointing `external_dirs` at `~/.claude/skills` — Hermes already ships 40+, and 51 more bloats what it reasons over.
- Made paths `~/`-relative in the **Mac** copies too, not a server fork — hardcoded `/Users/achibukz/` breaks on any second machine.
- `pbcopy` guarded with `command -v`, not removed — still works on the Mac, skips silently on Linux.
- career-ops personal data (`cv.md`, `applications.md`, `profile.yml`) is gitignored and stays that way; recruiter replies degrade on the server rather than putting a CV on a box with password SSH enabled.

Rejected:
- `external_dirs` exposing all 51 skills — context bloat.
- Reimplementing `pbcopy` via xclip — headless has no clipboard to fill.

Open:
- career-ops data unreachable on server; three options pending.
- `message-writer` voice.md path bug existed on Mac too, now fixed.

## 2026-08-17 09:15 [saved]
Goal: One command to bring every git repo on achibuntu up to date.

Decisions:
- `sync-repos` fast-forwards only — no merge, rebase, stash or push, because nothing running unattended may lose a commit.
- Untracked files do not block a pull; a fast-forward leaves them alone and aborts by itself on collision.
- Roots are scanned, not hardcoded, so a new clone is never silently skipped.

Rejected:
- `pull --rebase` everywhere — rewrites local commits unattended.
- Auto-stash before pulling — hides work he was mid-way through.
- `~/.claude` as a root — no remote on skills, marketplaces are `/plugin`'s job.

Open:
- `hermes-agent` first fetch exceeds the 300s default; still running at 227 MB.

## 2026-08-17 12:30 [saved]
Goal: Always-on schoolMem Telegram bot that can never write to the wiki.

Decisions:
- One bot per vault, not one routing between them — a misroute writes to the wrong vault under the wrong rules.
- `wiki/` ban enforced by a PreToolUse hook, not by CLAUDE.md — bypassPermissions removes every other gate.
- PreToolUse hooks DO fire under `--permission-mode bypassPermissions`; verified with a real denied write.
- `claude` falls back to `--print` with no TTY, so an unattended session needs tmux, not just systemd.
- Captures go to a tracked `inbox/`; `raw/` and `output/` are gitignored and strand notes on the server.

Rejected:
- `chmod -R a-w wiki/` — also blocks git fast-forwards, breaking daily sync.
- Trusting CLAUDE.md to hold the wiki line under bypass.
- `RuntimeMaxSec`+`Restart=always` — does not compose with oneshot+tmux.

Open:
- Bash under bypass is narrowed by heuristic, not closed.
- Separate unix user with read-only `wiki/` is the airtight fix, deferred.

## 2026-08-17 12:38 [saved]
Goal: Second always-on Telegram bot for achiOS, this one with write access.

Decisions:
- Operator bot runs unguarded — editing tasks.md, calendar and commits are the job, not a hazard.
- One `telegram-bot.sh` driven by `BOT_*` env vars per unit; `schoolmem-bot.sh` deleted.
- Guard made optional, not assumed, so an unguarded bot reuses the path without pretending otherwise.
- Restart timers staggered 04:00/04:10 — both fetch on launch and the box has one uplink.
- `install_units.sh` now enables `WantedBy=default.target` services, not only timers.

Rejected:
- A second standalone script — drifts, duplicates the fail-closed guard logic.
- Guarding the operator's achiMem/wiki writes anyway — would override an explicit instruction.
- A shared library sourced by two thin scripts — more parts than env vars, for two callers.

Open:
- Logging contract's achiMem/wiki ban is now documented but unenforced on the operator bot.
- Push is pre-authorised here, so a Telegram message can reach GitHub unattended.

## 2026-08-17 12:55 [saved]
Goal: achiOS bot went deaf — ordinary sessions were stealing its Telegram token.

Decisions:
- No bot token may live in `~/.claude/channels/telegram/`; achiOS moved to `telegram-achios`.
- Diagnosis is in the MCP log line `Channel notifications skipped: not in --channels list`.
- Regression test asserts no unit's `BOT_STATE_DIR` ends in `/channels/telegram`.
- Accepted a failed telegram MCP server in every ordinary session as the cost.

Rejected:
- Disabling the telegram plugin globally — the bot needs it enabled to use `--channels`.
- Per-project plugin scoping — bot and terminal share the same cwd, so it cannot separate them.

Open:
- Nothing stops a future `/telegram:configure` from writing a token back to the default dir.

## 2026-08-18 01:45 [saved]
Goal: Add automated multi-ETF market digest (VOO, VXUS, QQQM) and systemd failure alerts to Telegram.

Decisions:
- `OnFailure=achios-failure-alert@%n.service` attached across all user services, invoking `scripts/service_failure_alert.py` with sensitive token/key redaction.
- Process traps added in `telegram-bot.sh` and `run-bot.sh` so unexpected non-zero exits inside tmux also trigger failure alerts.
- Multi-ETF digest (`scripts/voo_digest.py`) queries Yahoo Finance chart APIs for VOO, VXUS, and QQQM; scheduled at 04:30 (US market close buffer) and 08:00 (morning brief) Asia/Manila.
- Initialized and published `achiAgy` private repository to GitHub (`achibukz/achiAgy`) with strict `.gitignore` protection for `.env*` secrets and dynamic sessions.

Rejected:
- Standard cron for ETF digest — ignores `CRON_TZ` and lacks `Persistent=true` recovery.
- Unsanitized journal logs in alerts — risked leaking bot tokens to Telegram.

Open:
- Automated `logrotate` for `~/.local/state/achios/*.log`.
- Auto-sync/commit loop for `schoolMem/inbox/`.

