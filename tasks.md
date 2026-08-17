# Tasks

Aki's master task register. achiOS hosts this — settled 2026-08-10 (see
`achiMem/wiki/personal/open-questions.md`). Tasks are operating state; achiMem records
knowledge, not pending work.

Read by `scripts/daily_brief.py` for the 8am Telegram brief. Keep the line format below or
the parser skips the line.

## Format

```
- [ ] What to do #area !high @2026-08-20
```

- `- [ ]` active, `- [x]` done, `- [~]` blocked
- `#area` optional, one or more. Free-form: `#thesis`, `#career`, `#achios`, `#school`
- `!high` `!med` `!low` optional. Missing means `!med`
- `@YYYY-MM-DD` optional due date. Overdue and due-today are called out in the brief

Move finished items to `## Done` with the completion date appended. Don't delete them.

## Active

- [ ] Maybe buy Codex — align its billing to the Claude subscription renewal so both land on the 29th #achios !low @2026-08-29
- [ ] Put a battery back in achibuntu — the BAT0 slot is empty (`ACPI: battery: Slot [BAT0] (battery absent)`), so any mains blip is an instant power-off. Firmware supports one, and its Insyde BIOS has no AC-recovery setting, so a battery is the only fix. A UPS is the fallback #infra !med
- [ ] Confirm which ING team Aki is joining — Data/AI/Transformation vs Retail Tech, one message to Vanscell Nierra #career !high
- [ ] Approach the DLSU school coordinator for the internship agreement signature #career !high
- [ ] Fix `career-ops/config/profile.yml` — still says T1 starts 2026-08-03, feeds wrong availability into live applications #career !high
- [ ] Add the oboda row to `career-ops/data/applications.md` — offer received and declined, missing entirely from the tracker #career !med
- [ ] Mount the 1 TB HDD at `/srv` and set up restic or borg backups for both vaults #achios !med
- [ ] Run `ADD TERM` for `AY2627-T1` in schoolMem once enlistment lands #school !low @2026-09-03
- [ ] Fix stale skill descriptions — `thesis-script-writer` and `thesis-humanizer` reference C3-LMM and MicroTok-PH, which match neither vault #achios !low
- [ ] Reapply for a BPI SaveUp account — the 2026-08-15 application was closed for being unfunded. Required initial deposit is Php 1 and monthly ADB is Php 0, so the deadline is the risk, not the amount. Fund it the day the account number lands #finances !med
- [ ] Check `CLAUDE_MEM_EXCLUDED_PROJECTS` in the Mac's `~/.claude-mem/settings.json` — it was empty on achibuntu despite CLAUDE.md saying claude-mem is disabled here. That file sits outside `~/.claude/`, so `sync-claude-config.sh` never copies it #achios !med
- [ ] Set the schoolMem bot to `dmPolicy: allowlist` — run `/telegram:access policy allowlist` inside the bot's own session (it must have `TELEGRAM_STATE_DIR` set, or it edits the achiOS bot instead). Still on `pairing`, so strangers who find `@schoMemBot` get a pairing code back #achios !med

## Blocked

- [~] Pull the power cord on achibuntu to test unattended boot recovery — blocked until a battery is installed. BAT0 is absent and the BIOS has no "Restore on AC Power Loss", so pulling the cord today just hard-kills it #achios !med

## Done

- [x] Stand up a second Telegram bot for schoolMem — `@schoMemBot`, own token and allowlist via `TELEGRAM_STATE_DIR`, running on achibuntu under `tmux -L schoolmem` + `achios-schoolmem-bot.service`, restarting daily at 04:00 Manila. Sonnet, bypass permissions, but hard-blocked out of `wiki/` by a PreToolUse hook; captures land in the tracked `schoolMem/inbox/` #achios !med @2026-08-17
- [x] Sync Claude Code memory to achibuntu — `scripts/sync_claude_memory.py`, called from `sync-claude-config.sh`. Remaps the path-derived project slug, sends only `memory/*.md` so session transcripts stay put, and unions `MEMORY.md` with no `--delete` so the server's own memories survive. Allowlisted to achiOS alone #achios !med @2026-08-17
