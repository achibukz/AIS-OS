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
- Research inquiries must be paired with an entry in [research.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/research.md) detailing lenses and deliverable, linked via anchor.

Move finished items to `## Done` with the completion date appended. Don't delete them.

## Active
- [ ] Design and implement a dedicated ticket-authoring skill / subagent (running on Gemini / Antigravity / Claude Sonnet) to create structured, unslop GitHub issues with tracer-bullet acceptance criteria rather than relying on Claude Opus alone #skills #agents #tickets #tooling !high @2026-08-28
- [ ] Audit Asa research failure modes and author implementation plan with Claude Code per [2026-08-28-asa-research-failure-modes-and-retry-loop-audit.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-08-28-asa-research-failure-modes-and-retry-loop-audit.md): (1) fix crashing `asa status` caused by unhandled FileNotFoundError on non-run directories in `~/.local/share/asa/runs/`, and (2) add automated Muses re-run loop when Althea unsupported claims exceed threshold (70-80%) #asa #audit #workflows #planning !high @2026-08-28
- [ ] Execute prioritized open tickets in achiAgy per [roadmap.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/roadmap.md) starting with #24 (read-only lock bypass), #1 (atomic persistence), #7 (per-topic defaults), #4 (orchestration mixin), and #9 (Atlas persona) #achiagy #engineering !high @2026-08-28
- [ ] Repair tests/test_daily_brief.py, all 44 tests fail against the refactored daily_brief module (no attribute parse_tasks, tasks_message, schedule_message, color_dot, polish_with_claude) #infra #testing !med
- [ ] Design and build AI-Assisted Learning Architecture project using achiMem and schoolMem as ground-truth knowledge bases with Claude Code / agy / asa subagents (adapted from amosblomqvist/learn DAG and probing mechanics) #achios #learning #arch #schoolmem #achimem !high @2026-08-30
- [ ] Audit and design end-to-end cohesion across achiOS daemons, email digest parser, task register, and calendar auto-sync with Claude Code #achios #audit #arch !high @2026-08-27
- [ ] Update Asa research workflow to mandate an exhaustive sources and citations appendix at the end of all generated markdown files and deliverables #asa #workflows #research !high
- [ ] Audit and refine ~/.config/achios/USER.md and MEMORY.md with Claude Code to optimize structure, conciseness, and 2,500-char budget utilization #achios #memory #audit !high @2026-08-27
- [ ] Audit and plan integration of Matt Pocock workflows (Wayfinder, Grilling, Codebase Design) with asa SCAN/STORM research pipeline in Claude Code per [2026-08-24-matt-pocock-workflow-integration-and-wayfinder-asa-audit.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-08-24-matt-pocock-workflow-integration-and-wayfinder-asa-audit.md) #achios #asa #workflows #audit !med @2026-08-27
- [ ] Implement Matt Pocock skills into Asa skills library and apply writing-for-agents standards to improve subagent prompt quality #asa #skills #agents !high
- [ ] Implement reflect skill and 3-subagent transcript review loop in achiOS (adapted from pstack/reflect) #achios #skills #learning !high
- [ ] Build Google Sheets Schedule Planner skill for Claude Code / achiOS based on Hermes OAuth and Sheets v4 API spec in [2026-08-24-google-sheets-schedule-planner-skill-spec.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-08-24-google-sheets-schedule-planner-skill-spec.md) #skills #automation #achios !high @2026-08-27
- [ ] Audit Hermes research retrospective and orchestrator findings with Claude Code in asa [2026-08-24-hermes-research-and-orchestrator-audit.md](http://100.106.210.38:8999/Code/GitHub/asa/docs/reports/2026-08-24-hermes-research-and-orchestrator-audit.md) #asa #audit !high @2026-08-27
- [ ] Benchmark Althea fact-checking on gemini-3.1-pro-high vs gemini-3.7-flash-high across claim granularity, latency, and tool fidelity in asa #asa #eval #benchmark !med @2026-08-27
- [ ] Execute the new implementation plan created with Claude Code #asa #arch !med @2026-08-27
- [ ] Create new BPI account and fund for ING onboarding proof #finances #career !high @2026-08-29
- [ ] Undergo Physical Exam at an outside clinic and obtain "Fit to Work" Medical Certificate for ING (DLSU clinic only issues for school-required practicum) #career !med
- [ ] Complete 5-month ING Internship Agreement Form (signatures: Aki, Parent/Guardian, DLSU coordinator, then notarize) #career #school !high
- [ ] Maybe buy Codex — align its billing to the Claude subscription renewal once ING internship / thesis workload ramps up #achios !low @2026-09-29
- [ ] Cancel current Google One subscription ahead of renewal #finances #personal !low @2026-10-13
- [ ] Subscribe to Google AI Pro Student Discount (₱275/mo for up to 4 years via SheerID verification) #finances #personal !low @2026-10-14

## Blocked

## Done
- [x] Execute achiAgy ticket #29: resolve HTML double-escaping in media dispatcher badges and enforce Tailscale web viewer link rendering #achiagy #telegram #media #bug !high @2026-08-28  (done 2026-08-28)
- [x] Set up new Term (AY2627-T1) in schoolMem with Claude Code — five subjects scaffolded to the current schema (CCINOV8, GELITPH, STDISCM, STSP002, THS-ST2), AY2526-T3 frozen, THS-ST1 thesis state carried into THS-ST2, [_term-index.md](http://100.106.210.38:8999/Documents/Obsidian/schoolMem/wiki/AY2627-T1/_term-index.md) #school #schoolmem !high @2026-08-28  (done 2026-08-28)
- [x] Fix the schoolMem wiki guard — it denied attended sessions because the hook outlives the bot that arms it; now keys off ACHIOS_UNATTENDED_BOT / TELEGRAM_STATE_DIR, and the Bash matcher no longer misses paths held in shell variables (`scripts/schoolmem_wiki_guard.py`, guard suite 20 → 47) #achios #schoolmem #security !high @2026-08-28  (done 2026-08-28)
- [x] Implement centralized documents and media repository synced via Syncthing across Mac and Achibuntu per [2026-08-27-centralized-documents-and-media-store-plan.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-08-27-centralized-documents-and-media-store-plan.md) with Claude Code #infra #storage #syncthing #schoolmem #achimem !high @2026-08-28  (done 2026-08-28)
- [x] Audit and implement achiOS Hub with Claude Code per [telegram-supergroup-hub-plan.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/telegram-supergroup-hub-plan.md) — Multi-window tmux hub daemon, topic router, and core forum topics (General, Atlas, SchoolMem, AchiMem, Aea, Luna, Aurora) live #achios #achiagy #hub #arch !high @2026-08-27  (done 2026-08-28)
- [x] Fix achiAgy streaming pipe inactivity timeouts during long background runs (Ticket #22 shipped in `src/stream_recovery.py` with watchdog timer) #achiagy #streaming #arch !high @2026-08-27  (done 2026-08-28)
- [x] Push intermediate orchestrator milestone summaries to Telegram in achiAgy/src/bot.py during long multi-agent runs (Ticket #23 shipped in `src/milestones.py`) #achiagy #telegram !high @2026-08-27  (done 2026-08-28)
- [x] Create ticket dependency graph and execution roadmap markdown file in achiAgy mapping issue relationships, priority order, and parallel workstreams per [roadmap.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/roadmap.md) #achiagy #planning #arch !high  (done 2026-08-28)
- [x] Research free and open-source alternatives to Whisper Flow (Wispr Flow) across features, feature gaps, and installation playbooks per [research.md#9-whisper-flow--wispr-flow-free-and-open-source-alternatives-deep-dive](http://100.106.210.38:8999/Code/GitHub/AIS-OS/research.md#9-whisper-flow--wispr-flow-free-and-open-source-alternatives-deep-dive) #research #tooling #ai !high @2026-08-28  (done 2026-08-28)
- [x] Build YouTube transcript extraction and structured ingestion workflow to generate dedicated video learning pages and update achiMem knowledge (standalone, non-Asa) #achimem #automation !med  (done 2026-08-27)
- [x] Research and configure Syncthing real-time continuous sync between Achibuntu and MacBook Air for Obsidian vaults (achiMem & schoolMem) per [research.md#4-continuous-bi-directional-file-synchronization-across-achibuntu-and-macos-syncthing-vs-alternatives](http://100.106.210.38:8999/Code/GitHub/AIS-OS/research.md#4-continuous-bi-directional-file-synchronization-across-achibuntu-and-macos-syncthing-vs-alternatives) #infra #tooling #obsidian !med  (done 2026-08-27)
- [x] Pick up DLSU Good Moral Certificate (CGMC) at SDFO / The Hub (formal release email received) #career #school !high @2026-08-26  (done 2026-08-26)
- [x] DLSU Term 1 (AY2627-T1) Enrollment via Archers Hub / Animo.sys — ID 123 2nd DL timeslot 11:30 AM - 12:30 PM #school !high @2026-08-25  (done 2026-08-25)
- [x] Research using Google Antigravity as model backend for Hermes Agent per [research.md#8-using-google-antigravity-as-model-backend-for-hermes-agent-plugins-proxies--bridge-repos](http://100.106.210.38:8999/Code/GitHub/AIS-OS/research.md#8-using-google-antigravity-as-model-backend-for-hermes-agent-plugins-proxies--bridge-repos) #hermes #antigravity #models #research !high @2026-08-25  (done 2026-08-25)
- [x] Research AI-integrated food and calorie tracking apps across free, one-time purchase, and subscription models per [research.md#7-ai-integrated-food-and-calorie-tracking-apps-landscape](http://100.106.210.38:8999/Code/GitHub/AIS-OS/research.md#7-ai-integrated-food-and-calorie-tracking-apps-landscape) #health #fitness #research !high @2026-08-25  (done 2026-08-25)
- [x] Rotate `@achiOSBot` Telegram token via BotFather (GitHub Secret Scanning alert #2), update `~/.config/achios/telegram.env`, and push redaction in `docs/2026-08-20-opus-audit-achios-achiagy.md` #security #achios !high @2026-08-21  (done 2026-08-25)
- [x] Research Hermes Kanban Architecture for Asa Milestone 5 (`kanban_db.py`, atomic claims, worker locks) #agents #collab #arch !high @2026-08-22  (done 2026-08-24)
- [x] Research Hermes agent response style and communication dynamics to update achiOS prompt architecture, reducing wordiness and text-heavy replies #achios #research #learning !high @2026-08-22  (done 2026-08-24)
- [x] Submit GCash ImaGnation Phase 1 entry via Google Form (3-slide PDF, 90s MP4, 5x CVs + Enrolment proofs) #hackathon #projects !high @2026-08-24  (done 2026-08-24)
- [x] Record 1-min 30-sec video pitch for GCash ImaGnation Challenge (exactly 90s, MP4) #hackathon #projects !high @2026-08-24  (done 2026-08-24)
- [x] Create 3-slide pitch deck for GCash ImaGnation Challenge using Andrei's Figma mockups and research debrief #hackathon #projects !high @2026-08-23  (done 2026-08-24)
- [x] Finalize proposed schedule for Term 1 (CCINOV8, STDISCM, THS-ST2, STELEC4, GE) in [Google Sheets](https://docs.google.com/spreadsheets/d/1qqaTvcyz40JvyTDyT8MXiOEjPVh57PAL96jb_967BJ4) ahead of Aug 25 enrollment — Successfully enrolled in locked 14u target plan (STSP002 S30A, STDISCM S03, CCINOV8 S03, GELITPH Y11, THS-ST2 S03), 100% aligned with Lui on Tue/Fri and 100% free Mon/Wed/Thu for ING & Thesis #school !high @2026-08-25  (done 2026-08-25)
- [x] Have Claude Code review [2026-08-23-asa-research-retrospective-startups-and-qa.md](http://100.106.210.38:8999/Code/GitHub/asa/docs/2026-08-23-asa-research-retrospective-startups-and-qa.md) in `asa` to update the orchestrator loop, SKILL.md, and enforce mandatory alethea fact-checking #agents #asa #arch !high @2026-08-24  (done 2026-08-24)
- [x] Complete the implementation of the new architecture of Asa #agents #collab #arch !high @2026-08-22  (done 2026-08-24)
- [x] Implement shared task_engine.py, native achiAgy /tasks handler, concurrency guards, and systemd fixes per [2026-08-21-tasks-and-systemd-architecture-audit.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-08-21-tasks-and-systemd-architecture-audit.md) #achios #achiagy !high @2026-08-22  (done 2026-08-24)
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
