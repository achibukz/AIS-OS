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
