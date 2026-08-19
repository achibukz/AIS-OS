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
Goal: Add ETF digest, systemd failure alerts, and several new Telegram debrief crons.

Decisions:
- `OnFailure=achios-failure-alert@%n.service` on all user services, with token/key redaction.
- `voo_digest.py` (VOO/VXUS/QQQM) at 04:30 + 08:00 Manila; timer-based, not cron.
- New crons: tasks digest, evening debrief, VIP email triage — each its own script+timer, sent to `achinouncements`.
- `daily_brief.py` refactored to deterministic Python (no LLM call, <1s).
- Vault inbox sync daemon (15 min) auto-commits mobile captures with rebase conflict protection.
- Published `achiAgy` repo; added PDF delivery pipeline; added Telegram conversation archive (`tgdb`) and cross-platform transcript exporter.

Rejected:
- Cron over systemd timers — ignores `CRON_TZ`, no `Persistent=true` recovery.
- LLM subprocess for daily brief — slow/flaky vs. deterministic formatting.
- Blind `git add -A` across vaults — risks staging scratch files outside `inbox/`.

## 2026-08-18 20:10 [saved]
Goal: CasaOS dashboard setup, DLSU schedule planner, ID 123 enlistment appointment.

Decisions:
- CasaOS live on achibuntu; Code-Server :8085, Filebrowser :8082. Webview ServiceWorker blocker fixed via Chrome insecure-origin flag, not self-signed certs.
- DLSU Term 1 planner built in Google Sheets (`1qqaTvcyz40JvyTDyT8MXiOEjPVh57PAL96jb_967BJ4`).
- Golden 14-unit load: online Tuesday + one Friday on-campus block, keeping Mon/Wed/Thu/Sat free for the ING internship.
- ID 123 2nd DL enrollment added to `DLSU` calendar, Tue 2026-08-25 11:30-12:30. Codex eval rescheduled to 2026-10-29.

Rejected:
- Monday/Thursday electives (`HCI2000`) — extra campus days conflict with internship hours.

## 2026-08-19 05:50 [saved]
Goal: Bot separation (Finance + School), SSH Termius setup, ETF schedule optimization, weekly recap cron.

Decisions:
- Split one-way bots by domain: `@achiETFBot` (market digests), `@achiSchooNounceBot` (DLSU email), keeping `@achiOSBot`/`@schoMemBot` as before. `telegram_notify.py` parametrized with `env_path` to support this.
- Re-tuned ETF schedule to 08:00 + 22:00 Manila; added Sunday 18:00 weekly ETF recap.
- Termius on iPhone connected to achibuntu via Tailscale.
- Fixed a bash interpolation bug by using script-file payloads instead of quoted string interpolation.

Rejected:
- Duplicate 04:30/08:00 morning pings — market closed throughout both.
- Merging school announcements into two-way `@schoMemBot` — keeps its context clean.

Open:
- Finalize elective/GE section by 2026-08-23, ahead of 2026-08-25 enrollment.
- Improve email digest noise filtering (`!med`).
- Research multi-dev collab setup for Asa (`!high`).


