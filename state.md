# State

## Current Goal
`achibuntu` (HP 14-ac137TX) is live as a headless agent host. Finishing Phase 8 verification
of `achiMem/output/2026-08-16-linux-server-buildout.md`.

## Plan Status
Runbook Phases 0–7 complete. **Phase 8 (prove it works) is 1 of 4:**
- [x] Message the bot from the phone and get a reply
- [ ] Ask it to read a file from a vault
- [ ] Schedule a one-off cron job, confirm delivery to Telegram
- [~] **Pull the power cord** — blocked, not pending. No battery is fitted, so this cannot pass
      as written (see Open Issues)

## Evidence
- Gateway: `active`, ~104 MB, lingering user systemd unit, `✓ telegram connected` at 19:51:04
- Model: OpenRouter `nvidia/nemotron-3-ultra-550b-a55b:free`, ₱0/month
- Reach: Tailscale `achibuntu` / `100.106.210.38`; SSH alias + key auth working
- `achimem_capture.py`: 51 tests pass; verified against a real two-clone git fixture, not just mocks
- Wiki written and pushed (`892bf20`): new `achibuntu` page, 4 open questions closed

## Open Issues
- **Brownout survival is already answered, and the answer is no.** There is no battery in the
  box at all — the kernel reports `ACPI: battery: Slot [BAT0] (battery absent)` and only `AC`
  appears under `/sys/class/power_supply/`. With no battery and no BIOS "Restore on AC Power
  Loss", mains loss is an instant power-off and the box stays off until someone presses the
  button. Fitting a battery is the fix; `Persistent=true` on the timers is the mitigation.
- **1 TB HDD unattached.** Intended for `/srv` as a restic/borg target; both vaults are currently
  protected only by their git remotes.
- **career-ops data unreachable on the server** — `cv.md`, `applications.md`, `profile.yml` are
  gitignored, so recruiter replies degrade there. Deferred because password SSH was open; that
  objection is now gone, so it can be revisited.
- Codex is the intended eventual model. Verify the plan tier permits third-party harnesses
  **before** subscribing — the Anthropic Pro/Max mistake has the same shape.

## Waiting on Aki
- **Start the schoolMem bot unit.** Built, tested, pushed — not yet running. He must exit the
  foreground session on pts/2 first (two pollers on one token 409), then
  `systemctl --user start achios-schoolmem-bot.service`. The restart timer is already live and
  fires 04:00 Manila. `tasks.md` still lists this as active; flip it once the unit is up.
- **achiOS bot's channel server is down** — `~/.claude/channels/telegram/bot.pid` is gone and its
  MCP disconnected mid-session, though the session on pts/1 is still alive. Unrelated to the
  schoolMem work; the achiOS bot will not answer until that session is restarted.

## Done since last save (2026-08-17)
- **schoolMem Telegram bot** — `@schoMemBot`, second channel session, own token and allowlist via
  `TELEGRAM_STATE_DIR=~/.claude/channels/telegram-schoolmem`, launched from the vault so
  schoolMem's own `CLAUDE.md` loads. Runs `sonnet` with `bypassPermissions` under
  `tmux -L schoolmem`, restarting daily at 04:00 Manila and fast-forwarding the vault first.
  `scripts/schoolmem_wiki_guard.py` is a PreToolUse hook that hard-denies writes into `wiki/`;
  the wrapper arms it every start and refuses to launch without it. 26 guard tests, 164 total,
  all pass. Captures land in the new tracked `schoolMem/inbox/`. Full rationale in
  `decisions/log.md`.
- **`sync-repos` ships** — `scripts/sync-repos.sh`, symlinked to `~/.local/bin/sync-repos`. Aki
  runs it when he opens the VM. Scans `~/Code/GitHub`, `~/Documents/Obsidian`, `~/.hermes` and
  fast-forwards only; `held back` / `DIVERGED` / `FETCH FAILED` are reported and the repo left
  untouched. 11 tests build real repos in a tmpdir and assert no work is lost. Caveat:
  `hermes-agent`'s first fetch on this connection has run past 20 minutes and 227 MB, so it will
  report a timeout until that completes — `SYNC_REPOS_TIMEOUT` overrides the 300s default.
- **Claude Code memory now reaches achibuntu** — `scripts/sync_claude_memory.py`, called from
  `sync-claude-config.sh`. The two machines each kept their own `~/.claude/projects/*/memory`
  and had never exchanged anything, so Mac-side rules did not bind the box that runs
  unattended. Not a plain rsync: the project dir is a slug of the repo's absolute path so the
  `$HOME` prefix is remapped, `projects/` also holds session transcripts so only `memory/*.md`
  is sent, and `MEMORY.md` is unioned with no `--delete` so the server's own memories survive.
  Allowlisted to achiOS alone — schoolMem's memory carries Aki's student ID, and Hermes reads
  whatever lands there unsupervised. 17 new tests; verified idempotent against the live box.
- **SSH hardened** — key-only, root login off, `sshd_config.d/01-hardening.conf`. Tailscale SSH
  enabled first as an independent fallback. Verified via the LAN IP.
- **`hermes` PATH fixed** — `~/.local/bin` moved above `.bashrc`'s non-interactive guard. Note
  the gateway's systemd unit already had its own correct `PATH`, so Hermes' internal cron was
  never affected; this only fixed `ssh host 'cmd'`, scripts, and system cron.
- **Four skills ported** to `~/.hermes/skills/`, and `sync-claude-config.sh` now pushes to both
  `~/.claude/skills` and `~/.hermes/skills`.
- **Access guide written** — `achiMem/output/2026-08-17-achibuntu-access-guide.md`, including
  the add-a-device procedure.
- **Bun installed on achibuntu** (1.3.14, `~/.bun/bin/bun`, symlinked into `~/.local/bin`).
  The official `bun.sh/install` script needs `unzip`, which the box lacks and which needs sudo,
  so the release zip was fetched from GitHub and extracted with Python instead. Same binary.
  This was silently breaking claude-mem's `bun-runner.js` on every SessionStart.
- **claude-mem was never actually excluded from this repo on achibuntu.** `CLAUDE.md` says it is
  disabled here, but `CLAUDE_MEM_EXCLUDED_PROJECTS` in `~/.claude-mem/settings.json` was empty and
  the db already held 9 observations and 1 session summary tagged `AIS-OS`. The exclusion lives
  outside `~/.claude/`, so `sync-claude-config.sh`'s allowlist never carried it over from the Mac.
  Now set to `AIS-OS` on this box. Check the Mac's copy matches.
