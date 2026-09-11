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
- One primary area is required: `#school`, `#projects`, `#personal`, `#career`, or `#systems`
- Other subject and repository tags may follow the primary area
- `!high` `!med` `!low` optional. Missing means `!med`
- `@YYYY-MM-DD` optional due date. Overdue and due-today are called out in the brief
- `<!-- task-id: value -->` is optional internal identity and never appears in rendered views
- Research inquiries must be paired with an entry in [research.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/research.md) detailing lenses and deliverable, linked via anchor.

Move finished items to `## Done` with the completion date appended. Don't delete them.

## Active
- [ ] Implement the dependency chain AIS-OS #6, AIS-OS #13, then achiCore #148 in isolated worktrees #systems #achios #achicore !high
- [ ] Fix shared Telegram message splitting through [AIS-OS #34](https://github.com/achibukz/AIS-OS/issues/34), preserving long-message tails without duplicate prefixes #systems #bug !med
- [ ] Fix false-positive delegation failure receipts on trailing agy stream disconnects, filed as [achiCore #167-#168](https://github.com/achibukz/achiCore/issues/167) #achicore #bug !high
- [ ] Retry transient git fetch failures in standby so a stalled fetch stops stranding a worker pair, filed as [achiCore #171](https://github.com/achibukz/achiCore/issues/171) #achicore #bug !high
- [ ] Suppress the stream drop truncation warning when the recovered delegation report is complete, filed as [achiCore #172](https://github.com/achibukz/achiCore/issues/172) #achicore #bug !med
- [ ] Tap Recheck and release on the achiCore #6 status card in #Atlas to free aea1 and luna1 #achicore !high
- [ ] Review [AIS-OS PR #21](https://github.com/achibukz/AIS-OS/pull/21) and exercise assisted-live-testing on the next eligible PR, checking the Markdown interaction record and posted PR comment #systems #testing !med
- [ ] Hold a separate planning session for a control board or Kanban frontend connecting the Astra workflow and learning records, per [astra-plan.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md#follow-up-planning-session-for-a-control-board) #achios #achicore #planning !med
- [ ] Discuss privileged testing, conflict handling, /towork workflow audit, TGDB overhaul, worker engine optimization, and write boundary constraints with Astra per [astra-plan.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md#follow-up-discussion-topics-with-astra-privileged-testing-conflict-handling-towork-audit-tgdb-overhaul-and-worker-optimization) #systems #achicore #planning !med
- [ ] Start the next Astra implementation session on self-learning foundations: [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13) for stable task/Calendar operations and [achiCore #56](https://github.com/achibukz/achiCore/issues/56) for memory/persona precedence #systems #achios #achicore !high
- [ ] After the foundations, connect ordinary requests through achiCore #148 and corrections through AIS-OS #14, then continue the remaining T1-T9 learning slices in dependency order #systems #achios #achicore !high
- [ ] Prepare AIS-OS #18 replay fixtures during early learning work; run its real Flash acceptance later with assisted-live-testing, a Markdown interaction record and a PR comment #systems #achios #testing !high
- [ ] Fix Claude Code quota and auto-refresh stale provider tokens in /usage (achiCore #135-#136) #achicore #ux #bug !high
- [ ] Build a sync script so global agent instructions propagate from ~/.claude/CLAUDE.md to Antigravity (~/.gemini/config/GEMINI.md, AGENTS.md) and Codex (~/.codex/AGENTS.md) automatically (needs design discussion: shared-core file vs generated marker blocks vs symlink; current state is one-time manual copy done 2026-09-05) #systems #tooling !med
- [ ] Implement the approved Canvas first release through [#24](https://github.com/achibukz/AIS-OS/issues/24), with current-term subjects [#25](https://github.com/achibukz/AIS-OS/issues/25) and client/queries/notifications [#26](https://github.com/achibukz/AIS-OS/issues/26), [#28](https://github.com/achibukz/AIS-OS/issues/28), [#29](https://github.com/achibukz/AIS-OS/issues/29) merged via [PR #33](https://github.com/achibukz/AIS-OS/pull/33). Phone login [#27](https://github.com/achibukz/AIS-OS/issues/27) passed Google login with the Mac closed and authenticated Ubuntu session replacement; [PR #35](https://github.com/achibukz/AIS-OS/pull/35) awaits review; achiCore integration #173 and deployment [#30](https://github.com/achibukz/AIS-OS/issues/30) remain pending. #school #automation #infra !med
- [ ] Audit and design end-to-end cohesion across achiOS daemons, email digest parser, task register, and calendar auto-sync with Claude Code #achios #audit #arch !high @2026-08-27
- [ ] Audit and refine ~/.config/achios/USER.md and MEMORY.md with Claude Code to optimize structure, conciseness, and 2,500-char budget utilization #achios #memory #audit !high @2026-08-27
- [ ] Build Google Sheets Schedule Planner skill for Claude Code / achiOS based on Hermes OAuth and Sheets v4 API spec in [2026-08-24-google-sheets-schedule-planner-skill-spec.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-08-24-google-sheets-schedule-planner-skill-spec.md) #skills #automation #achios !high @2026-08-27
- [ ] Execute prioritized open tickets in achiAgy per [roadmap.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/roadmap.md) starting with #24 (read-only lock bypass), #1 (atomic persistence), #7 (per-topic defaults), #4 (orchestration mixin), and #9 (Atlas persona) #achiagy #engineering !high @2026-08-28
- [ ] Design and build AI-Assisted Learning Architecture project using achiMem and schoolMem as ground-truth knowledge bases with Claude Code / agy / asa subagents (adapted from amosblomqvist/learn DAG and probing mechanics) #achios #learning #arch #schoolmem #achimem !high @2026-08-30
- [ ] Implement AUTO Zoom Leaver Windows port tickets #1-#4 #projects #windows #engineering !high
- [ ] Ship the Google auth lifecycle and /tasks renderer batch, AIS-OS #3 to #8 plus achiCore #57, per [the plan](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-08-29-google-auth-lifecycle-and-tasks-renderer-plan.md) #achios #infra !high
- [ ] Implement reflect skill and 3-subagent transcript review loop in achiOS (adapted from pstack/reflect) #achios #skills #learning !high
- [ ] Build Tauri v2 desktop GUI for achiOS, achiCore, and achiMem connecting to Achibuntu over SSH/Tailscale per [2026-08-30-tauri-desktop-gui-architecture-and-blueprint.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-08-30-tauri-desktop-gui-architecture-and-blueprint.md) #achios #achicore #ui #infra !med
- [ ] Build cron job that scans all repos for open GitHub tickets and surfaces the single most important one to action — Telegram message must include clickable links to each ticket so Aki can jump directly to it #achios #infra #engineering !med
- [ ] Hold a grill-me session and implement model escalation fallback in achiCore to upgrade to a higher-tier model when a lower model fails #achicore #models #planning !med
- [ ] Add codebase inspection skill to Aurora in achiCore #achicore #agents !med
- [ ] Require @achibukz and @luna-achiCore on Aea PRs and @achibukz and @aea-achiCore on Luna reviews (achiCore #77) #achicore #github !med
- [ ] Test fallback mechanism when Gemini 3.7 Flash and Codex hit quota limits #achicore #testing #models !med
- [ ] Change Telegram command /newtopics to make /new the first command in autocomplete #achicore #telegram !med
- [ ] Repair tests/test_daily_brief.py, all 44 tests fail against the refactored daily_brief module (no attribute parse_tasks, tasks_message, schedule_message, color_dot, polish_with_claude) #infra #testing !med
- [ ] Test whether `ssh -L` port-forward re-auth works for gws on achibuntu, so the four logins run server-side and no credential copy is needed #achios #infra !med
- [ ] Write `references/model-selection.md` — research-grounded model tier hierarchy and use-case reference guide (Opus, Sonnet, Flash, Flash-lite, etc. across achiOS, achiAgy, Asa, and daily tasks), then update AGENTS.md model guidance sections to match — current AGENTS.md mentions are undetailed and not grounded in research #achios #reference #arch !med
- [ ] Allow permitted subdirectories beneath protected roots in write boundary (~/.config/gws-*) and restore stock gws 0.22.5 (achiCore #131, rejecting PR #164 custom fork) #achicore #security #bug !high
- [ ] Automate completed GitHub PR and issue sync into tasks.md and evening debrief (AIS-OS #11) #achios #automation #telegram !high
- [ ] Add show-me skill to Aea and Luna and mandate visual architecture diagrams in PR descriptions and reviews (achiCore #133-#134) #achicore #agents #ux !med
- [ ] Audit CLI tools and integrations against Landlock write boundary constraints (gh, git, systemd, gcloud, uv) to prevent silent Permission denied failures per [astra-plan.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md#write-boundary-inventory-and-downstream-feature-impact) #achicore #infra #security !high
- [ ] Audit Hermes research retrospective and orchestrator findings with Claude Code in asa [2026-08-24-hermes-research-and-orchestrator-audit.md](http://100.106.210.38:8999/Code/GitHub/asa/docs/reports/2026-08-24-hermes-research-and-orchestrator-audit.md) #asa #audit !high @2026-08-27
- [ ] Audit and plan integration of Matt Pocock workflows (Wayfinder, Grilling, Codebase Design) with asa SCAN/STORM research pipeline in Claude Code per [2026-08-24-matt-pocock-workflow-integration-and-wayfinder-asa-audit.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-08-24-matt-pocock-workflow-integration-and-wayfinder-asa-audit.md) #achios #asa #workflows #audit !med @2026-08-27
- [ ] Benchmark Althea fact-checking on gemini-3.1-pro-high vs gemini-3.7-flash-high across claim granularity, latency, and tool fidelity in asa #asa #eval #benchmark !med @2026-08-27
- [ ] Execute the new implementation plan created with Claude Code #asa #arch !med @2026-08-27
- [ ] Audit Asa research failure modes and author implementation plan with Claude Code per [2026-08-28-asa-research-failure-modes-and-retry-loop-audit.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-08-28-asa-research-failure-modes-and-retry-loop-audit.md): (1) fix crashing `asa status` caused by unhandled FileNotFoundError on non-run directories in `~/.local/share/asa/runs/`, and (2) add automated Muses re-run loop when Althea unsupported claims exceed threshold (70-80%) #asa #audit #workflows #planning !high @2026-08-28
- [ ] Update Asa research workflow to mandate an exhaustive sources and citations appendix at the end of all generated markdown files and deliverables #asa #workflows #research !high
- [ ] Implement Matt Pocock skills into Asa skills library and apply writing-for-agents standards to improve subagent prompt quality #asa #skills #agents !high
- [ ] Hold a grill-me session and design an Asa skill/workflow for prior art discovery, competitive market analysis, and idea viability evaluation (check if an idea already exists, analyze competitors, and assess market viability) #asa #skills #research #planning !med
- [ ] Cancel current Google One subscription ahead of renewal #finances #personal !low @2026-10-13
- [ ] Subscribe to Google AI Pro Student Discount (₱275/mo for up to 4 years via SheerID verification) #finances #personal !low @2026-10-14
- [ ] Fix conflict-repair budgets and Atlas repair/merge-queue status through [achiCore #155](https://github.com/achibukz/achiCore/issues/155) #achicore #infra #ux !high
- [ ] Invalidate worker probes after virtualenv deletion or replacement through [achiCore #156](https://github.com/achibukz/achiCore/issues/156) #achicore #infra !high
- [ ] Ship specific-repo sync across AIS-OS #12 and achiCore #145 (/sync <repo>) #achios #achicore #infra !med
- [ ] Unify Gemini Flash models with reasoning effort submenu in /topicmodels ([achiCore #162](https://github.com/achibukz/achiCore/issues/162)) #achicore #ux !med
- [ ] Hold grill-me session to design and build GitHub trending repos scanner cron (star surge tracking, adoption driver analysis, workflow integration) #automation #tooling #infra !med
- [ ] Check Google OAuth tokens after 7 days to verify permanent production validity without re-auth #infra #security #achicore !med @2026-09-12
- [ ] Write a ticket for /sync to support a configurable repo include/exclude list, so it stops syncing repos that don't need it #achios #tooling !med
- [ ] Have Astra audit whether open AIS-OS and achiCore tickets are still accurate against current code #systems #achios #achicore #planning !med
- [ ] Audit slash commands and scripts for vendor lock-in (e.g. /tasks unavailable outside Claude Code), starting with LLM-calling scripts, and design a fallback so they work across AI vendors #systems #achios #arch !med
- [ ] Write a ticket: when a loop finishes a ticket without success after 3 tries, add a button to switch the model working the ticket #achicore #ux !med
- [ ] Restore stock gws 0.22.5 and grant write access to ~/.config/gws-* under Landlock write boundary per [achiCore #131](https://github.com/achibukz/achiCore/issues/131) (cancelling PR #164 custom fork) #achicore #infra #security !high
- [ ] Upgrade sync-repos --repo/-r to accept multiple repo names in one call (e.g. /sync achiCore, AIS-OS) #achios #tooling !med
- [ ] Discuss how to do smart model routing in daily conversations in Telegram for achiCore #achicore #planning !med


## Blocked

## Done

- [x] Submit signed 5-month ING Internship Agreement Form to Vans by 1:00 PM (scheduled email queued; Aki and parent signatures done; coordinator signature & notarization to follow) #career #school !high @2026-09-11 (done 2026-09-09)
- [x] Review and approve the Canvas implementation plan with incremental tickets. #school #automation (done 2026-09-08)
- [x] Send AY 2026-2027 Term 1 EAF to Ethan Burayag (ethan_burayag@dlsu.edu.ph) #school #thesis !high (done 2026-09-07)
- [x] Create new BPI account and fund for ING onboarding proof #finances #career !high @2026-09-07 (done 2026-09-07)
- [x] Remove legacy Google tokens (~/.config/achios/google_token*.json and stale ~/.config/gws) through [AIS-OS #7](https://github.com/achibukz/AIS-OS/issues/7) #infra #security !med (done 2026-09-06)
- [x] Undergo Physical Exam at an outside clinic and obtain "Fit to Work" Medical Certificate for ING (DLSU clinic only issues for school-required practicum) #career !med (done 2026-09-06)
- [x] Align and copy global instructions from Claude (CLAUDE.md) to Antigravity and Codex #systems #tooling !med (done 2026-09-05)
- [x] Capture the reusable Telegram testing hub, audit the worker-test lessons and create [assisted-live-testing](http://100.106.210.38:8999/.config/skillshare/skills/assisted-live-testing/SKILL.md) for CLI/backend and other human acceptance, with Markdown records and PR comments; source review in AIS-OS PR #21, issue #20 #systems #testing (done 2026-09-05)
- [x] Merge achiCore PR #154, deploy `bbb8fb7`, restart the main hub and close #153 at Aki's request; partial acceptance and follow-ups remain in the deployment record #systems #achicore !high (done 2026-09-05)
- [x] Audit Telegram, achiCore, achiOS, achiMem and worker test environments; replace the [Astra plan](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md) with implementation slices #systems #achios #achicore !high (done 2026-09-05)
- [x] Ship achiCore #138-#139: register Astra as a Codex model and add the effort step to /model #achicore #ux !med  (done 2026-09-05)
- [x] Integrate Claude Code foundation into achiCore as third engine with subscription OAuth (ticket 119, PR 126), scoped config directories, and prompt attachment handling #achicore #claude #arch !high  (done 2026-09-05)
- [x] Promote achiclaude GCP OAuth consent screen to In Production to eliminate 7-day token expiration cap, re-auth 4 profiles, and verify Google Drive access #achicore #infra #security !high  (done 2026-09-05)
- [x] Configure per-topic model selection and fallback models with custom effort levels via Telegram UI in achiCore (tickets 106, 108, 118, 125) #achicore #ux !med  (done 2026-09-05)
- [x] Report Codex account allowance and remaining quota in achiCore /usage command (tickets 42, 112, 114, 116) #achicore #ux !med  (done 2026-09-05)
- [x] Handle Codex diagnostic stderr without failing turn and adapt to rm -f exec policy in achiCore (ticket 89, PR 101) #achicore #codex #bug !high  (done 2026-09-05)
- [x] Document Project Astra audit plan across workflow review, second brain audit, and evergreen project inspection in docs/astra-plan.md #arch #planning !med  (done 2026-09-05)
- [x] Create and sync the shared `telegram-image-sender` skill for sending local images through achiOS Telegram media dispatch #achios #skills #telegram #media !med (done 2026-09-02)
- [x] Pause automatic TGDB transcript export and commits while the self-learning loop is discussed in achiCore #83 #achios #achicore #achimem !high  (done 2026-08-31)
- [x] Autostart achiCore hub daemon with topic windows on system boot via systemd (achiCore #79, #80) #achicore #infra !med @2026-08-31  (done 2026-08-31)
- [x] Research: Subagent-optimized CI/CD, automated testing gates, and PR verification architecture #systems #ci #agents #research !high @2026-08-30  (done 2026-08-30)
- [x] Do PR 60 of achiCore #achicore !high  (done 2026-08-30)
- [x] Fix conflicting --effort flag dispatch for agy Gemini models in achiCore (achiCore #58) #achicore #bug !high  (done 2026-08-30)
- [x] Create Ara — personal writer agent for achiOS (name chosen, scope built out as skill) #achios #agents !med  (done 2026-08-29)
- [x] Rename achiAgy repo and codebase to an OS-agnostic name (candidates: achiAgent, achicore, achihub) — update repo name on GitHub, README, AGENTS.md, CLAUDE.md, systemd units, service names, config keys, and any achiOS references that hardcode "achiAgy" #achiagy #achios #engineering !med  (done 2026-08-29)
- [x] Add tests for `frontmatter_flag`, `orchestrates`, and the mixin branch of `get_persona_prompt` in `src/topic_router.py` — Luna's PR #36 review found these new methods shipped with zero test coverage; three live agents use the mixin path on every turn (agi, aurora, ari) #achiagy #testing !high @2026-08-28  (done 2026-08-29)
- [x] Have Claude Code plan and research how to implement Codex in achiAgy, then write a ticket for it #achiagy #codex #planning !high  (done 2026-08-29)
- [x] Enable global Codex unslop SessionStart hook; configuration installed and command output tested, awaiting Aki's trust approval through `/hooks` and a session-start check #achios #codex !med  (done 2026-08-29)
- [x] Maybe buy Codex — align its billing to the Claude subscription renewal once ING internship / thesis workload ramps up #achios !low @2026-09-29  (done 2026-08-29)
- [x] File a dedicated ticket for the orchestration mixin feature that landed unreviewably inside PR #36 (`ORCHESTRATION_MIXIN_FILE`, `_TRUTHY`, `frontmatter_flag`, `orchestrates`, mixin concatenation in `get_persona_prompt`) — no ticket, no spec, no targeted review #achiagy #engineering #planning !med  (done 2026-08-29)

- [x] Research Codex integration in achiOS, topic 10, covering all six lenses; delivered [Markdown](http://100.106.210.38:8999/Documents/Obsidian/achiMem/raw/2026-08-28-codex-in-achios-workflow-and-model-hierarchy.md) and [PDF](http://100.106.210.38:8999/Documents/Files/projects/achios/2026-08-28-codex-in-achios-workflow-and-model-hierarchy.pdf). Finished directly, not through Asa STORM; final source audit stopped at Aki's request #achios #achiagy #codex #research !high  (done 2026-08-29)
- [x] Execute achiAgy ticket #35: display active topic, model, effort, mode, and skills in /new reset message (PR #36 merged) #achiagy #telegram #ux !med @2026-08-28  (done 2026-08-28)
- [x] Ticket-authoring skill shipped as `/agy-tickets`, a copy of `to-issues` carrying Aki's ticket format, label creation so `gh issue create` stops failing on `needs-triage`, and a Recommended model section routing each slice to `gemini-3.7-flash-high` or Sonnet. Committed to [SKILL.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/references/skills/agy-tickets/SKILL.md) #skills #agents #tickets #tooling !high @2026-08-28  (done 2026-08-28)
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
- [x] Rotate `@achiOSBot` Telegram token via BotFather (GitHub Secret Scanning alert #2), update `~/.config/achios/telegram.env`, and push redaction in [2026-08-20-opus-audit-achios-achiagy.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-08-20-opus-audit-achios-achiagy.md) #security #achios !high @2026-08-21  (done 2026-08-25)
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
- [x] Run full system architecture audit with Claude Opus across achiOS daemons, achiAgy, crons, and notification routing per [2026-08-20-system-architecture-audit.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-08-20-system-architecture-audit.md) #audit #achios #achiagy !high @2026-08-20  (done 2026-08-20)
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

- [x] Run system architecture audit on Universal TGDB Vault Archive & Exporter with Claude Opus per [2026-08-18-feature-audit-tgdb-and-correction-harvester.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-08-18-feature-audit-tgdb-and-correction-harvester.md) — Audited transcript exporter, TGDB logger, secret sanitization, intermediate tool/XML stripping, bot identity detection, and Obsidian vault note formatting #audit #tgdb #achios !high @2026-08-20
- [x] Implement Hermes-inspired Self-Learning Loop for achiAgy and achiOS per [2026-08-19-self-learning-loop-implementation.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/superpowers/plans/2026-08-19-self-learning-loop-implementation.md) — Created MemoryEngine with 2.5k-char budget per file, CLI mutations, /learn authoring engine, harvester routing to MEMORY.md/USER.md/.agentrules/decisions, and 25 passing unit tests; merged to main/master #achiagy #achios !high @2026-08-20
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
