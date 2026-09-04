# Systems & Engineering Task Backlog

Modular register for achiOS, achiCore, infrastructure, and engineering sub-tasks. Linked from master [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md).

## Active Tasks

- [ ] Audit and design end-to-end cohesion across achiOS daemons, email digest parser, task register, and calendar auto-sync with Claude Code #achios #audit #arch !high @2026-08-27
- [ ] Audit and refine ~/.config/achios/USER.md and MEMORY.md with Claude Code to optimize structure, conciseness, and 2,500-char budget utilization #achios #memory #audit !high @2026-08-27
- [ ] Build Google Sheets Schedule Planner skill for Claude Code / achiOS based on Hermes OAuth and Sheets v4 API spec in [2026-08-24-google-sheets-schedule-planner-skill-spec.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-08-24-google-sheets-schedule-planner-skill-spec.md) #skills #automation #achios !high @2026-08-27
- [ ] Execute prioritized open tickets in achiAgy per [roadmap.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/roadmap.md) starting with #24 (read-only lock bypass), #1 (atomic persistence), #7 (per-topic defaults), #4 (orchestration mixin), and #9 (Atlas persona) #achiagy #engineering !high @2026-08-28
- [ ] Design and build AI-Assisted Learning Architecture project using achiMem and schoolMem as ground-truth knowledge bases with Claude Code / agy / asa subagents (adapted from amosblomqvist/learn DAG and probing mechanics) #achios #learning #arch #schoolmem #achimem !high @2026-08-30
- [x] Handle Codex diagnostic stderr without failing turn and document rm -f exec policy restrictions (achiCore #89, PR #101) #achicore #codex #bug !high (done 2026-09-05)
- [ ] Implement AUTO Zoom Leaver Windows port tickets #1-#4 #projects #windows #engineering !high
- [x] Plan and implement automated weekly Google OAuth token refresh for achiOS — resolved via GCP OAuth Production mode promotion, eliminating 7-day token cap #achios #infra #automation !high (done 2026-09-05)
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
- [ ] Allow permitted subdirectories beneath protected roots in write boundary (~/.config/gws-*) (achiCore #131) #achicore #security #bug !high
- [ ] Automate completed GitHub PR and issue sync into tasks.md and evening debrief (AIS-OS #11) #achios #automation #telegram !high
- [ ] Add show-me skill to Aea and Luna and mandate visual architecture diagrams in PR descriptions and reviews (achiCore #133-#134) #achicore #agents #ux !med
- [ ] Fix Claude Code quota and auto-refresh stale provider tokens in /usage (achiCore #135-#136) #achicore #ux #bug !high
