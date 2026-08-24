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
- Research inquiries must be paired with an entry in [research.md](file:///home/achibukz/Code/GitHub/AIS-OS/research.md) detailing lenses and deliverable, linked via anchor.

Move finished items to `## Done` with the completion date appended. Don't delete them.

## Active
- [ ] Build YouTube transcript extraction and structured ingestion workflow in Asa to generate dedicated video learning pages and update achiMem knowledge (secondary to Sciel/achiMem fixes) #asa #workflows #achimem #automation !med
- [ ] Audit and refine ~/.config/achios/USER.md and MEMORY.md with Claude Code to optimize structure, conciseness, and 2,500-char budget utilization #achios #memory #audit !high
- [ ] Research Syncthing and real-time file sync setups between Achibuntu and MacBook Air to eliminate manual git pull/fetch workflows per [research.md#4-continuous-bi-directional-file-synchronization-across-achibuntu-and-macos-syncthing-vs-alternatives](file:///home/achibukz/Code/GitHub/AIS-OS/research.md#4-continuous-bi-directional-file-synchronization-across-achibuntu-and-macos-syncthing-vs-alternatives) #infra #tooling #achios !med
- [ ] Audit and plan integration of Matt Pocock workflows (Wayfinder, Grilling, Codebase Design) with asa SCAN/STORM research pipeline in Claude Code per [docs/2026-08-24-matt-pocock-workflow-integration-and-wayfinder-asa-audit.md](file:///home/achibukz/Code/GitHub/AIS-OS/docs/2026-08-24-matt-pocock-workflow-integration-and-wayfinder-asa-audit.md) #achios #asa #workflows #audit !med @2026-08-26
- [ ] Build Google Sheets Schedule Planner skill for Claude Code / achiOS based on Hermes OAuth and Sheets v4 API spec in [docs/2026-08-24-google-sheets-schedule-planner-skill-spec.md](file:///home/achibukz/Code/GitHub/AIS-OS/docs/2026-08-24-google-sheets-schedule-planner-skill-spec.md) #skills #automation #achios !high @2026-08-25
- [ ] Audit Hermes research retrospective and orchestrator findings with Claude Code in asa [docs/reports/2026-08-24-hermes-research-and-orchestrator-audit.md](file:///home/achibukz/Code/GitHub/asa/docs/reports/2026-08-24-hermes-research-and-orchestrator-audit.md) #asa #audit !high @2026-08-25
- [ ] Benchmark Althea fact-checking on gemini-3.1-pro-high vs gemini-3.7-flash-high across claim granularity, latency, and tool fidelity in asa #asa #eval #benchmark !med @2026-08-26
- [ ] Implement active heartbeat polling loop in asa orchestrator to prevent streaming inactivity timeouts #asa #arch !high @2026-08-25
- [ ] Update achiAgy/src/bot.py to push intermediate orchestrator milestone summaries to Telegram during long multi-agent runs #achiagy #telegram !med @2026-08-26
- [ ] Execute the new implementation plan created with Claude Code #asa #arch !med
- [ ] Follow up / Pick up DLSU Good Moral Certificate (CGMC) once release notification arrives (8-10 working days, event set on DLSU Calendar) #career #school !high @2026-09-02
- [ ] Undergo Physical Exam at an outside clinic and obtain "Fit to Work" Medical Certificate for ING (DLSU clinic only issues for school-required practicum) #career !med
- [ ] Open/fund BPI SaveUp or bank account and obtain proof reflecting account number for ING #finances #career !high
- [ ] Complete 5-month ING Internship Agreement Form (signatures: Aki, Parent/Guardian, DLSU coordinator, then notarize) #career #school !high
- [ ] DLSU Term 1 (AY2627-T1) Enrollment via Archers Hub / Animo.sys — ID 123 2nd DL timeslot 11:30 AM - 12:30 PM #school !high @2026-08-25
- [ ] Go to a BPI branch and ask for an alternative on how to create a new BPI SaveUp account (avoiding traditional bank account) following the notice in work inbox #finances !high
- [ ] Reapply for a BPI SaveUp account — the 2026-08-15 application was closed for being unfunded. Required initial deposit is Php 1 and monthly ADB is Php 0, so the deadline is the risk, not the amount. Fund it the day the account number lands #finances !med
- [ ] Maybe buy Codex — align its billing to the Claude subscription renewal once ING internship / thesis workload ramps up #achios !low @2026-10-29
- [ ] Cancel current Google One subscription ahead of renewal #finances #personal !low @2026-10-13
- [ ] Subscribe to Google AI Pro Student Discount (₱275/mo for up to 4 years via SheerID verification) #finances #personal !low @2026-10-14
- [ ] Run `ADD TERM` for `AY2627-T1` in schoolMem once enlistment lands #school !low @2026-09-03

## Blocked

## Done
- [x] Rotate `@achiOSBot` Telegram token via BotFather (GitHub Secret Scanning alert #2), update `~/.config/achios/telegram.env`, and push redaction in `docs/2026-08-20-opus-audit-achios-achiagy.md` #security #achios !high @2026-08-21  (done 2026-08-25)
- [x] Research Hermes Kanban Architecture for Asa Milestone 5 (`kanban_db.py`, atomic claims, worker locks) #agents #collab #arch !high @2026-08-22  (done 2026-08-24)
- [x] Research Hermes agent response style and communication dynamics to update achiOS prompt architecture, reducing wordiness and text-heavy replies #achios #research #learning !high @2026-08-22  (done 2026-08-24)
- [x] Submit GCash ImaGnation Phase 1 entry via Google Form (3-slide PDF, 90s MP4, 5x CVs + Enrolment proofs) #hackathon #projects !high @2026-08-24  (done 2026-08-24)
- [x] Record 1-min 30-sec video pitch for GCash ImaGnation Challenge (exactly 90s, MP4) #hackathon #projects !high @2026-08-24  (done 2026-08-24)
- [x] Create 3-slide pitch deck for GCash ImaGnation Challenge using Andrei's Figma mockups and research debrief #hackathon #projects !high @2026-08-23  (done 2026-08-24)
- [x] Finalize proposed schedule for Term 1 (CCINOV8, STDISCM, THS-ST2, STELEC4, GE) in [Google Sheets](https://docs.google.com/spreadsheets/d/1qqaTvcyz40JvyTDyT8MXiOEjPVh57PAL96jb_967BJ4) ahead of Aug 25 enrollment — Locked 14u plan (STDISCM S04, CCINOV8 S02, STSP002 S30A, GELITPH Z20), ported Hanielle (18u) & Lui (14u) schedules with master overview #school !high @2026-08-23  (done 2026-08-24)
- [x] Have Claude Code review [docs/2026-08-23-asa-research-retrospective-startups-and-qa.md](file:///home/achibukz/Code/GitHub/asa/docs/2026-08-23-asa-research-retrospective-startups-and-qa.md) in `asa` to update the orchestrator loop, SKILL.md, and enforce mandatory alethea fact-checking #agents #asa #arch !high @2026-08-24  (done 2026-08-24)
- [x] Complete the implementation of the new architecture of Asa #agents #collab #arch !high @2026-08-22  (done 2026-08-24)
- [x] Implement shared task_engine.py, native achiAgy /tasks handler, concurrency guards, and systemd fixes per [2026-08-21-tasks-and-systemd-architecture-audit.md](file:///home/achibukz/Code/GitHub/AIS-OS/docs/2026-08-21-tasks-and-systemd-architecture-audit.md) #achios #achiagy !high @2026-08-22  (done 2026-08-24)
- [x] Name subagents with actual names #agents #achios #learning !med  (done 2026-08-22)
- [x] Prepare and send scanned copy of PSA Birth Certificate for ING #career !high  (done 2026-08-22)
- [x] Run deep research, market analysis, and primary source verification on GCash ImaGnation pitch; compile consolidated 23-page Research Dossier PDF #hackathon #research #mamdanigcash !high @2026-08-21  (done 2026-08-21)
- [x] Ingest and synthesize GCash ImaGnation team meeting transcripts (`Transcripts/GCASH MEETING.md` & `notes.md`) and create structured `docs/debrief.md` for Mamdani Administration #hackathon #mamdanigcash !high @2026-08-21  (done 2026-08-21)
- [x] Prompt Claude Code Opus in `~/Code/GitHub/asa` to draft the task-by-task implementation plan for Asa Milestones 1 & 2 in `docs/plans/2026-08-20-asa-core-and-presets-plan.md`, surfacing any remaining edge cases #agents #collab #career !high @2026-08-21  (done 2026-08-21)
- [x] Research & design Asa as a universal multi-agent orchestrator connecting Claude Code, Antigravity (AGY), and Codex with bidirectional subagent delegation (e.g. Claude Opus orchestrating AGY & Codex, Codex orchestrating AGY & Opus, and vice versa) with native Telegram integration #collab #agents #career #telegram !high  (done 2026-08-21)
- [x] Build Asa Telegram Gateway & Interactive Channel (enabling tri-agent dispatch, cross-model consensus discussion, and subagent supervision directly from Telegram) #collab #agents #telegram !high  (done 2026-08-21)
- [x] Run full system architecture audit with Claude Opus across achiOS daemons, achiAgy, crons, and notification routing per docs/2026-08-20-system-architecture-audit.md #audit #achios #achiagy !high @2026-08-20  (done 2026-08-20)
- [x] Reply to Sir Austin Fernandez's email re: character reference #school #career !high @2026-08-20  (done 2026-08-20)
- [x] Cut the harvester recursion: tag the frozen system prompt, strip it in the exporter, add a provenance guard + semantic dedup, with a regression test #achios #learning !high @2026-08-21  (done 2026-08-21)
- [x] After the recursion fix is green, purge the 3 bad MEMORY.md entries, 54 harvested decisions/log.md entries, .agentrules section 5, and 6 poisoned tgdb notes #achios #learning !high @2026-08-21  (done 2026-08-21)
- [x] Fix achiAgy crash: add `import re` to src/bot.py (HTML fallback always NameErrors, loses whole response) #achios #achiagy !high @2026-08-21  (done 2026-08-21)
- [x] Add retry + backoff + token redaction to scripts/telegram_notify.py and Restart=on-failure to all scheduled units (4 jobs died on a DNS blip today) #achios !high @2026-08-21  (done 2026-08-21)

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
