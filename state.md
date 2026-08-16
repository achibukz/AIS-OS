# State

## Current Goal
`achibuntu` (HP 14-ac137TX) is live as a headless agent host. Finishing Phase 8 verification
of `achiMem/output/2026-08-16-linux-server-buildout.md`.

## Plan Status
Runbook Phases 0–7 complete. **Phase 8 (prove it works) is 1 of 4:**
- [x] Message the bot from the phone and get a reply
- [ ] Ask it to read a file from a vault
- [ ] Schedule a one-off cron job, confirm delivery to Telegram
- [ ] **Pull the power cord** — confirm unattended boot, gateway return, bot answers

## Evidence
- Gateway: `active`, ~104 MB, lingering user systemd unit, `✓ telegram connected` at 19:51:04
- Model: OpenRouter `nvidia/nemotron-3-ultra-550b-a55b:free`, ₱0/month
- Reach: Tailscale `achibuntu` / `100.106.210.38`; SSH alias + key auth working
- `achimem_capture.py`: 51 tests pass; verified against a real two-clone git fixture, not just mocks
- Wiki written and pushed (`892bf20`): new `achibuntu` page, 4 open questions closed

## Open Issues
- **Brownout survival untested.** This BIOS has no "Restore on AC Power Loss"; recovery depends
  on a ten-year-old battery of unmeasured health. This is the power-cut test.
- **1 TB HDD unattached.** Intended for `/srv` as a restic/borg target; both vaults are currently
  protected only by their git remotes.
- **career-ops data unreachable on the server** — `cv.md`, `applications.md`, `profile.yml` are
  gitignored, so recruiter replies degrade there. Deferred because password SSH was open; that
  objection is now gone, so it can be revisited.
- Codex is the intended eventual model. Verify the plan tier permits third-party harnesses
  **before** subscribing — the Anthropic Pro/Max mistake has the same shape.

## Done since last save (2026-08-17)
- **SSH hardened** — key-only, root login off, `sshd_config.d/01-hardening.conf`. Tailscale SSH
  enabled first as an independent fallback. Verified via the LAN IP.
- **`hermes` PATH fixed** — `~/.local/bin` moved above `.bashrc`'s non-interactive guard. Note
  the gateway's systemd unit already had its own correct `PATH`, so Hermes' internal cron was
  never affected; this only fixed `ssh host 'cmd'`, scripts, and system cron.
- **Four skills ported** to `~/.hermes/skills/`, and `sync-claude-config.sh` now pushes to both
  `~/.claude/skills` and `~/.hermes/skills`.
- **Access guide written** — `achiMem/output/2026-08-17-achibuntu-access-guide.md`, including
  the add-a-device procedure.
