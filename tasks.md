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

- [ ] Run deep research, market analysis, and statistic gathering on GCash ImaGnation pitch with Claude Opus #hackathon #research #achigcash !high @2026-08-20
- [ ] Ingest and synthesize GCash ImaGnation team meeting transcripts (`Transcripts/GCASH MEETING.md` & `notes.md`) with Claude Opus into achiGcash #hackathon #achigcash !high @2026-08-20
- [ ] Draft business case & submit video pitch for GCash ImaGnation Innovation Challenge #hackathon #projects !high @2026-08-24
- [ ] Run full system architecture audit with Claude Opus across achiOS daemons, achiAgy, crons, and notification routing per docs/2026-08-20-system-architecture-audit.md #audit #achios #achiagy !high @2026-08-20

- [ ] Reply to Sir Austin Fernandez's email re: character reference #school #career !high @2026-08-20
- [ ] Follow up / Pick up DLSU Good Moral Certificate (CGMC) once release notification arrives (8-10 working days, event set on DLSU Calendar) #career #school !high @2026-09-02
- [ ] Undergo Physical Exam at an outside clinic and obtain "Fit to Work" Medical Certificate for ING (DLSU clinic only issues for school-required practicum) #career !med
- [ ] Prepare scanned copy of PSA Birth Certificate for ING #career !high
- [ ] Open/fund BPI SaveUp or bank account and obtain proof reflecting account number for ING #finances #career !high
- [ ] Complete 5-month ING Internship Agreement Form (signatures: Aki, Parent/Guardian, DLSU coordinator, then notarize) #career #school !high
- [ ] DLSU Term 1 (AY2627-T1) Enrollment via Archers Hub / Animo.sys — ID 123 2nd DL timeslot 11:30 AM - 12:30 PM #school !high @2026-08-25
- [ ] Finalize proposed schedule for Term 1 (CCINOV8, STDISCM, THS-ST2, STELEC4, GE) in [Google Sheets](https://docs.google.com/spreadsheets/d/1qqaTvcyz40JvyTDyT8MXiOEjPVh57PAL96jb_967BJ4) ahead of Aug 25 enrollment #school !high @2026-08-23
- [ ] Go to a BPI branch and ask for an alternative on how to create a new BPI SaveUp account (avoiding traditional bank account) following the notice in work inbox #finances !high
- [ ] Research & design Asa as a universal multi-agent orchestrator connecting Claude Code, Antigravity (AGY), and Codex with bidirectional subagent delegation (e.g. Claude Opus orchestrating AGY & Codex, Codex orchestrating AGY & Opus, and vice versa) with native Telegram integration #collab #agents #career #telegram !high
- [ ] Build Asa Telegram Gateway & Interactive Channel (enabling tri-agent dispatch, cross-model consensus discussion, and subagent supervision directly from Telegram) #collab #agents #telegram !high
- [ ] Build achiOS Curator & Log Rotation daemon (user-level `logrotate` for `~/.local/state/achios/*.log` and state pruning timer) #achios !med
- [ ] Implement Dynamic CLI Skill Synthesizer (auto-packaging complex workflows into documented Python CLI scripts with `--help` and `--dry-run`) #achios !med
- [ ] Create System Crash Reflection & Self-Healing Playbook (logging service failures and validated fixes to `references/troubleshooting-recipes.md`) #achios !med
- [ ] Reply to Rohde & Schwarz re: unsolicited application (email in work inbox, 2026-08-17) #career
- [ ] Reapply for a BPI SaveUp account — the 2026-08-15 application was closed for being unfunded. Required initial deposit is Php 1 and monthly ADB is Php 0, so the deadline is the risk, not the amount. Fund it the day the account number lands #finances !med
- [ ] Check `CLAUDE_MEM_EXCLUDED_PROJECTS` in the Mac's `~/.claude-mem/settings.json` — it was empty on achibuntu despite CLAUDE.md saying claude-mem is disabled here. That file sits outside `~/.claude/`, so `sync-claude-config.sh` never copies it #achios !med
- [ ] Set the schoolMem bot to `dmPolicy: allowlist` — run `/telegram:access policy allowlist` inside the bot's own session (it must have `TELEGRAM_STATE_DIR` set, or it edits the achiOS bot instead). Still on `pairing`, so strangers who find `@schoMemBot` get a pairing code back #achios !med
- [ ] Decide whether the achiOS bot should be blocked from `achiMem/wiki/` — the logging contract says unattended writes never reach the vault's wiki, and that rule is currently documented but unenforced on a bypass-permissions bot. `BOT_GUARD` already exists; it needs a guard script for that path and a decision about whether a Telegram-driven session counts as a human in the loop #achios !med
- [ ] Think through the prompt-injection surface — a Telegram message drives an agent with bypass permissions and pre-authorised push. Anything Aki forwards or pastes (an email, a job posting, a webpage) is untrusted input reaching a tool-using agent. No mitigation today beyond the allowlist #achios !med
- [ ] Put a battery back in achibuntu — the BAT0 slot is empty (`ACPI: battery: Slot [BAT0] (battery absent)`), so any mains blip is an instant power-off. Firmware supports one, and its Insyde BIOS has no AC-recovery setting, so a battery is the only fix. A UPS is the fallback #infra !low
- [ ] Mount the 1 TB HDD at `/srv` and set up restic or borg backups for both vaults #achios !low
- [ ] Research whether the three Telegram bots (achiOS/Claude Code, Antigravity/Gemini, Hermes/Codex) can be made to discuss with each other and produce a combined decision or discussion output #achios !low
- [ ] Maybe buy Codex — align its billing to the Claude subscription renewal once ING internship / thesis workload ramps up #achios !low @2026-10-29
- [ ] Cancel current Google One subscription ahead of renewal #finances #personal !low @2026-10-13
- [ ] Subscribe to Google AI Pro Student Discount (₱275/mo for up to 4 years via SheerID verification) #finances #personal !low @2026-10-14
- [ ] Run `ADD TERM` for `AY2627-T1` in schoolMem once enlistment lands #school !low @2026-09-03
- [ ] Fix stale skill descriptions — `thesis-script-writer` and `thesis-humanizer` reference C3-LMM and MicroTok-PH, which match neither vault #achios !low
- [ ] Rotate the bot logs — `~/.local/state/achios/{achios,schoolmem}_bot.log` are append-only with no rotation and grow for as long as the bots run #achios !low
- [ ] Measure what the two always-on Sonnet sessions cost against the plan quota — no visibility today, and they restart daily forever. The `usage-limit-reducer` skill reads the local JSONL logs #achios !low
- [ ] Harden the Bash side of the schoolMem wiki guard, or stop relying on it — the path-based deny is deterministic but the Bash layer is a regex heuristic, so a shell can still reach `wiki/`. The airtight fix is running that bot as its own unix user with read-only access to `wiki/` #achios !low

## Blocked

- [~] Pull the power cord on achibuntu to test unattended boot recovery — blocked until a battery is installed. BAT0 is absent and the BIOS has no "Restore on AC Power Loss", so pulling the cord today just hard-kills it #achios !low

## Done

- [x] E-sign ING Offer Letter #career !high @2026-08-20
- [x] E-sign ING Privacy Notice for Applicants #career !high @2026-08-20
- [x] E-sign ING Privacy Notice for Employees #career !high @2026-08-20
- [x] Fill out ING Intern Information Sheet (using 3 confirmed references: Doc Briane Samson, Sir Aris Pulumbarit, Doc Jordan Deja; leave gov IDs blank) #career !high @2026-08-20
- [x] Prepare copy of DLSU School ID (scanned/clear photo) for ING submission #career !high @2026-08-20

- [x] Run system architecture audit on Universal TGDB Vault Archive & Exporter with Claude Opus per docs/2026-08-18-feature-audit-tgdb-and-correction-harvester.md — Audited transcript exporter, TGDB logger, secret sanitization, intermediate tool/XML stripping, bot identity detection, and Obsidian vault note formatting #audit #tgdb #achios !high @2026-08-20
- [x] Implement Hermes-inspired Self-Learning Loop for achiAgy and achiOS per docs/superpowers/plans/2026-08-19-self-learning-loop-implementation.md — Created MemoryEngine with 2.5k-char budget per file, CLI mutations, /learn authoring engine, harvester routing to MEMORY.md/USER.md/.agentrules/decisions, and 25 passing unit tests; merged to main/master #achiagy #achios !high @2026-08-20
- [x] Monitor replies from character references (Doc Briane Samson ✅, Sir Aris Pulumbarit ✅, Doc Jordan Deja ✅) — All 3 faculty references confirmed for ING onboarding packet #career #school !high @2026-08-19
- [x] Form 5-member team & register for GCash ImaGnation Innovation Challenge — Team "Mamdani Administration" registered via official portal #hackathon #projects !high @2026-08-19
- [x] Improve email digest filtering, classification rules, and message formatting (`scripts/email_digest.py`) — Implemented hybrid noise filtering + LLM synthesis cards with DLSU faculty/suspension and ING context #achios !med @2026-08-19
- [x] Order DLSU Good Moral Certificate for ING onboarding via Google Form #career #school !high @2026-08-19
- [x] Build Autonomous Correction Harvester (`scripts/extract_corrections.py` to detect user corrections in `tgdb/` and auto-update `.agentrules` & `decisions/log.md`) #achios !med @2026-08-18
- [x] Install and evaluate CasaOS dashboard for browser-based monitoring and file management — Configured with Filebrowser, Code-Server, and Tailscale remote access #infra #achios !high @2026-08-18

- [x] Check GitHub CodeQL Analysis failure on career-ops main — Removed all GitHub Actions workflows from career-ops so no automated CI/CD runs or sends notifications #achios @2026-08-18
- [x] Confirm which ING team Aki is joining — Role confirmed as Retail Tech (voluntarily accepted, Oct 2026 – Mar 2027) #career !high @2026-08-18
- [x] Fix `career-ops/config/profile.yml` — Updated T1 start date to 2026-09-03 and committed to career-ops main #career !high @2026-08-18
- [x] Add the oboda row to `career-ops/data/applications.md` — Offer received (₱5,000/mo) and declined (below floor); committed to career-ops main #career !med @2026-08-18
- [x] Close the `inbox/` loop — `scripts/vault_inbox_sync.py` and `systemd/achios-vault-sync.timer` automatically sweep, commit, and push new mobile captures from `schoolMem/inbox/` and `achiMem/inbox/` to GitHub `origin/main` every 15 minutes, with autash rebase conflict protection #achios !high @2026-08-18
- [x] Alert when a bot dies — `OnFailure=achios-failure-alert@%n.service` attached across all user services, pointing to `scripts/service_failure_alert.py` with sensitive token redaction; trap handler in bot launcher scripts sends immediate Telegram failure notice to achinouncements with journal logs #achios !med @2026-08-18
- [x] Stand up a second Telegram bot for schoolMem — `@schoMemBot`, own token and allowlist via `TELEGRAM_STATE_DIR`, running on achibuntu under `tmux -L schoolmem` + `achios-schoolmem-bot.service`, restarting daily at 04:00 Manila. Sonnet, bypass permissions, but hard-blocked out of `wiki/` by a PreToolUse hook; captures land in the tracked `schoolMem/inbox/` #achios !med @2026-08-17
- [x] Sync Claude Code memory to achibuntu — `scripts/sync_claude_memory.py`, called from `sync-claude-config.sh`. Remaps the path-derived project slug, sends only `memory/*.md` so session transcripts stay put, and unions `MEMORY.md` with no `--delete` so the server's own memories survive. Allowlisted to achiOS alone #achios !med @2026-08-17
