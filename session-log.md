# Session Log

## 2026-08-28 07:41 [saved]
Goal: Author and file GitHub ticket achiAgy#29 for media dispatcher badge double-escaping and Tailscale web viewer link rendering.

Decisions:
- Authored and filed GitHub issue `achibukz/achiAgy#29` (`fix(media): resolve HTML double-escaping in media dispatcher badges and enforce Tailscale web viewer link rendering`) with explicit transformation table, root cause breakdown, and acceptance criteria.
- Added active tracking item in `tasks.md` for ticket #29.

Open:
- Hand ticket #29 to Aea in `#Aea` to implement test-first in `achiAgy`.

## 2026-08-28 07:33 [saved]
Goal: Finalize link verification validator and clean legacy documentation links for Tailscale web viewer protocol.

Decisions:
- Updated `scripts/verify_links.py` to strip code blocks and ignore markdown image tags (`(?<!!)\[...\](...)`) to eliminate false positives in illustrative examples.
- Cleaned historical doc files (`docs/2026-08-20-system-architecture-audit.md`, `docs/2026-08-18-feature-audit-tgdb-and-correction-harvester.md`, `docs/2026-08-21-tasks-and-systemd-architecture-audit.md`) to comply with Tailscale web viewer linking rules.
- Verified 100% compliance across all docs and agent instruction files via `python scripts/verify_links.py --check-all` (0 issues).

Open:
- Continue executing open roadmap tickets in achiAgy (#24, #1, #7, #4, #9).

## 2026-08-28 06:45 [saved]
Goal: Implement universal git pre-commit hook enforcing session-log updates on code changes (AIS-OS#1).

Decisions:
- Created executable pre-commit hook in `scripts/hooks/pre-commit` and synced to `.githooks/pre-commit`.
- Checked staged files via `git diff --cached --name-only` for significant file extensions and paths (`*.py`, `*.ts`, `*.js`, `*.json`, `*.sh`, `*SKILL.md`, `*AGENTS.md`, `agents/*.md`, `systemd/*`).
- Enforced staged `session-log.md` with a valid `## YYYY-MM-DD ... [saved]` entry matching today in Manila time (`Asia/Manila`, UTC+8) whenever significant files are staged.
- Allowed doc-only/task-only commits (`tasks.md`, `README.md`, `docs/*`, `research.md`) to pass without requiring session-log changes.
- Added bypass mechanisms for `SKIP_SESSION_CHECK=1` and `--no-verify`.
- Created idempotent installer script in `scripts/install_git_hooks.sh` that targets any repo path.
- Added unit tests in `tests/test_pre_commit_hook.py` (17 tests) covering clean runs, doc passes, stale date rejections, valid date accepts, pattern checks, installer idempotency, and bypass flags.
- Merged AIS-OS#2 (Universal git pre-commit hook) to `main`.
- Verified and synced workspace worktrees across all repositories:
  - `AIS-OS`: On `main` at `f954804`.
  - `achiAgy`: On `master` at `d660573` (PR #27 for Ticket #26 merged).
  - `review/achiAgy`: On `master` at `d660573`.
  - `schoolMem`: On `main` at `2d66bba`.
  - `asa`: On `phase-1.5-verification` at `65764a2`.
- Diagnosed and fully resolved broken `file:///` and local path links emitted across Telegram chats:
  1. Updated `achiAgy/src/formatters.py` to mechanically rewrite all local file paths (`/home/achibukz/...`, `~/...`), `file://` URIs, and backtick-wrapped links to Tailscale web viewer links (`http://100.106.210.38:8999/...`) in Telegram HTML output.
  2. Updated `achiAgy/AGENTS.md` and all agent personas (`agents/luna.md`, `agents/aea.md`, `agents/aurora.md`, `agents/atlas.md`, `agents/ari.md`, `agents/achimem.md`, `agents/schoolmem.md`) with explicit Tailscale Markdown (.md) Web Viewer Linking Rules banning `file:///` URLs.
  3. Shipped and merged achiAgy PR #28 (`ticket/28-web-viewer-links`), with 201 passing unit tests in `achiAgy`.
  4. Restarted `achi-agy.service` and verified `achi-viewer.service` running on port 8999.

Open:
- Continue executing open roadmap tickets in achiAgy (#24, #1, #7, #4, #9).
- Upgrade Claude Code session kick routines and integrate email notification dispatch.

## 2026-08-28 06:15 [saved]
Goal: Restart achiAgy bot daemons, scrub token leaks from disk logs, verify live polling state, and reconcile task register.

Decisions:
- Stopped `achi-agy.service` and killed tmux session servers (`achiagy` and `achiagy-hub`) to release file handles.
- Scrubbed raw Telegram bot token occurrences across all disk log files (`~/.local/state/achiagy-hub/achiagy-hub.log`, `~/Code/GitHub/achiAgy/achiagy.log`, etc.) using `src.log_redaction.redact_secrets`, reducing raw token hits to 0.
- Restarted `achi-agy.service` and started `tmux -L achiagy-hub` with all 8 topic windows (`daemon`, `general`, `atlas`, `schoolmem`, `achimem`, `aea`, `luna`, `aurora`).
- Verified live polling logs to confirm the active `SecretRedactingFilter` redacts outgoing Telegram API URLs to `bot[redacted]`.
- Reconciled [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md): moved achiOS Hub implementation, Ticket #22 (streaming timeouts), Ticket #23 (milestones), and Ticket #14/roadmap creation to `## Done`; added active task for executing open roadmap tickets.
- Added active task to upgrade Claude Code session kick routines (`kick_claude_session.sh` / `sessionclaude` skill) to use updated prompt templates and dispatch email notifications via achiOS notification pipeline upon session initialization.
- Completed grilling session on automated session logging hooks and authored/filed GitHub issues:
  1. `achibukz/achiAgy#26`: Daemon post-turn session stop hook continuation for unlogged edits (recorded in [roadmap.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/roadmap.md)).
  2. `achibukz/AIS-OS#1`: Universal git pre-commit hook to enforce `session-log.md` updates on code changes.
- Added active task to design and build a ticket-authoring skill / subagent (running on Gemini / Antigravity / Claude Sonnet) to create structured, unslop GitHub issues independently of Claude Opus.
- Diagnosed and fixed Telegram HTML link formatting bug in `achiAgy/src/formatters.py`: normalized outer backtick-wrapped markdown links (`` `[text](url)` `` -> `<a href="url">text</a>`) so Tailscale web viewer links always render as clickable hyperlinks rather than raw code blocks in Telegram.

Open:
- Design and build the ticket-authoring skill / subagent.
- Handoff Ticket #26 to Aea in achiAgy or Ticket #1 in AIS-OS.
- Upgrade Claude Code session kick routines and integrate email notification dispatch.
- Run an end-to-end PR code review test with Luna in thread 531, or proceed with Ticket #24 / #1 / #7.

## 2026-08-28 04:00 [saved]
Goal: Audit Asa research runtime failure modes and log plan for automated Muses re-run loop upon high Althea unsupported claim rates.

Decisions:
- Authored comprehensive audit report in [2026-08-28-asa-research-failure-modes-and-retry-loop-audit.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-08-28-asa-research-failure-modes-and-retry-loop-audit.md) detailing two runtime failure modes from the Whisper Flow research run:
  1. `asa status` crashed completely (`FileNotFoundError: meta.json`) when non-run subdirectories (`extracted_responses/`, `extracted_texts/`) were present in `~/.local/share/asa/runs/` because `sidecar.py` lacked defensive checks for missing metadata.
  2. High unsupported/contradicted claim rate in Althea (14 unsupported + 3 contradicted out of 23 = ~74%) caused by Muses citing marketing landing pages without explicit technical assertions in raw HTML, domain hallucination (`openwhisper.com`), composite claims, and numerical approximations.
- Added active task to [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) for Claude Code to author an implementation plan to: (1) patch the `asa status` crash, (2) enforce primary-source constraints in `muses.md`, and (3) add an automated Muses re-query/retry loop when unsupported claims exceed threshold (70-80%).

Open:
- Claude Code executing the plan to patch `asa/sidecar.py`, `asa/agents/muses.md`, and `asa/workflows/research.md`.

## 2026-08-28 03:43 [saved]
Goal: Dispatch Asa STORM multi-lens research on free and open-source alternatives to Whisper Flow (Wispr Flow).

Decisions:
- Recorded research inquiry in [research.md#9-whisper-flow--wispr-flow-free-and-open-source-alternatives-deep-dive](http://100.106.210.38:8999/Code/GitHub/AIS-OS/research.md#9-whisper-flow--wispr-flow-free-and-open-source-alternatives-deep-dive).
- Dispatched 5 parallel `asa` `muses` workers, synthesized findings via `athena` (`whisper-synthesis`), and audited citations via `althea` (`whisper-fact-check`).
- Fixed `asa status` crash by relocating non-run data directories (`extracted_responses/` and `extracted_texts/`) out of `~/.local/share/asa/runs/`.
- Authored final audited research dossier in [2026-08-28-whisper-flow-free-alternatives-deep-dive.md](http://100.106.210.38:8999/Documents/Obsidian/achiMem/raw/2026-08-28-whisper-flow-free-alternatives-deep-dive.md) and moved task to `## Done` in [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md).

Open:
- None. Research deliverable complete.

## 2026-08-28 02:55 [saved]
Goal: Add task for achiAgy ticket dependency flowchart and prioritization roadmap.

Decisions:
- Added active task to [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) for creating a ticket dependency graph and execution roadmap in `achiAgy` mapping issue relationships, priority order, and parallel workstreams.

Open:
- Write the ticket dependency DAG and roadmap document in `achiAgy`.

## 2026-08-27 23:20 [saved]
Goal: Clarify streaming pipe inactivity timeout root cause and author coherent ticket/plan for achiAgy keepalive architecture.

Decisions:
- Verified research audit logs ([2026-08-24-hermes-research-and-orchestrator-audit.md](http://100.106.210.38:8999/Code/GitHub/asa/docs/reports/2026-08-24-hermes-research-and-orchestrator-audit.md)) confirming `asa` workers ran without crashing or timing out, and that the failure occurred in `achiAgy`'s streaming pipe during silent idle waits on background tasks.
- Recorded architectural decision in [decisions/log.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/decisions/log.md).
- Updated [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) to have Claude Code write coherent tickets and implementation plans for: (1) fixing `achiAgy` streaming pipe inactivity timeouts during long background runs (!high, @2026-08-27), and (2) pushing intermediate orchestrator milestone summaries to Telegram in `achiAgy/src/bot.py` (!high, @2026-08-27).

Rejected:
- Framing the issue as an internal `asa` worker bug (rejected because workers ran healthily to completion on disk).
- Relying purely on client reconnections without keepalives (rejected because it terminates active Telegram turns with error messages).

Open:
- Claude Code authoring tickets and executing implementation plans for `achiAgy` streaming watchdog, keepalive architecture, and intermediate Telegram milestone streaming.

## 2026-08-27 22:55 [saved]
Goal: Plan and architect Centralized Documents & Media Store (`~/Documents/Files/`) via /grill-me.

Decisions:
- Completed 2-round /grill-me session settling 9 architectural points (D34–D38) for centralized cross-project document and media management.
- Defined storage root at `~/Documents/Files/` on Achibuntu and AchiBook Air (macOS) with domain-aligned taxonomy (`personal/{health,finance,legal}`, `academic/<course>`, `career/<company>`).
- Selected dedicated Syncthing folder ID `achi-files` (`~/Documents/Files/` <-> `AchiBook Air`) to isolate binary synchronization from Obsidian markdown text sync (`varww-m4imt`).
- Established ISO date-prefixed file naming (`YYYY-MM-DD-descriptor.ext`), Syncthing-only storage (no Git repository), `raw/` retirement and gitignoring in `achiMem` and `schoolMem`, and dual Tailscale web viewer / filesystem path referencing.
- Authored comprehensive implementation plan in [2026-08-27-centralized-documents-and-media-store-plan.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-08-27-centralized-documents-and-media-store-plan.md) and recorded decision in [decisions/log.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/decisions/log.md).
- Updated [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) with actionable Claude Code execution task.

Rejected:
- Keeping binary assets inside Obsidian `raw/` folders (rejected due to Git repo bloat).
- Using Git LFS for binary documents (rejected due to GitHub limits and merge complexity).
- Using symlinks inside Obsidian vaults (rejected due to cross-platform sync loops).

Open:
- Claude Code execution of implementation plan (scaffolding, syncthing wiring, asset migration, gitignore update).

## 2026-08-27 22:25 [saved]
Goal: Archive prescription image in achiMem vault and create structured health wiki tracking page.

Decisions:
- Archived prescription image to `~/Documents/Obsidian/achiMem/raw/prescriptions/2021-07-07-dr-arthur-roman-prescription.jpg`.
- Created structured wiki index in [prescriptions.md](http://100.106.210.38:8999/Documents/Obsidian/achiMem/wiki/personal/health/prescriptions.md) capturing doctor credentials (Dr. Arthur Dessi E. Roman), patient metadata, and exact medication instructions (Levocetirizine + Montelukast, Clobetasol).
- Rebuilt wiki index (`scripts/build_index.py`) and committed/pushed changes to `achiMem` remote origin.

Rejected:
- Storing unorganized images in temporary attachment cache.

Open:
- None.

## 2026-08-27 22:22 [saved]
Goal: Implement Outbound Server Media and Document Dispatch in achiAgy.

Decisions:
- Implemented `MediaDispatcher` in `src/media_dispatcher.py` to extract `![caption](<path>)` references, normalize three-tier paths (absolute, tilde expansion, workspace relative), enforce security blacklists (`~/.ssh`, `~/.config/achios`, `~/.gnupg`, `~/.hermes`), auto-escalate >10MB images to documents, and rewrite markdown tags to Tailscale web viewer links (`http://100.106.210.38:8999/...`).
- Integrated media extraction, link rewriting, and async Telegram media dispatch (`send_photo` / `send_document`) into `execute_agent_pipeline` in `src/bot.py`.
- Added 13 automated unit tests in `tests/test_outbound_media.py` covering path resolution, blacklist guards, extension routing, size limits, link rewrites, and mock Telegram dispatch (105/105 tests passing).
- Checked off Tasks 9, 10, and 11 in [telegram-supergroup-hub-plan.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/telegram-supergroup-hub-plan.md).

Rejected:
- Modifying or implementing unrelated tasks (delegation, workspace locks) during this scoped turn.

Open:
- None.

## 2026-08-27 22:18 [saved]
Goal: Complete /grill-me design session for Outbound Server Media & Document Dispatch and append architecture to achiOS Hub plan.

Decisions:
- Settled 7-point design tree (D27–D33) for outbound media delivery: standard markdown image syntax (`![caption](<path>)`), text first / streamed delivery followed by trailing media messages, smart extension routing (`send_photo` for images, `send_document` for docs/PDFs).
- Defined three-tier path normalization (absolute, tilde expansion, workspace relative) and security blacklist (`~/.ssh`, `~/.config/achios`, `~/.gnupg`, `~/.hermes`).
- Standardized markdown image rewriting to Tailscale web viewer links (`http://100.106.210.38:8999/...`) in final text response.
- Appended Section 12 (Outbound Server Media & Document Dispatch Architecture) and updated Section 4 / Section 10 in [telegram-supergroup-hub-plan.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/telegram-supergroup-hub-plan.md).
- Recorded architectural decision in [decisions/log.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/decisions/log.md).

Rejected:
- Custom tag syntax `[send_photo: path]` (which would require prompt retraining).
- Universal uncompressed document mode for raster photos.

Open:
- Implement Tasks 9–11 in `achiAgy` (media dispatcher parser, Tailscale link rewriter, and unit tests).

## 2026-08-27 21:30 [saved]
Goal: Complete /grill-me design session for Cross-Topic Delegation and append architecture to achiOS Hub plan.

Decisions:
- Settled 8-point design tree (D19–D26) for cross-topic handoffs: dual hybrid trigger (`/delegate` + `delegate_topic` tool), persistent thread session ingestion in `sessions.json`, non-blocking async dispatch with target live streaming and origin receipts, and any-to-any mesh topology.
- Authored shared subagent orchestration prompt mixin in [prompts/asa.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/prompts/asa.md) with structured payload schemas and error boundaries.
- Appended Section 11 (Cross-Topic Delegation & Multi-Agent Mesh Architecture) and updated Section 4 / Section 10 in [telegram-supergroup-hub-plan.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/telegram-supergroup-hub-plan.md).
- Enforced cycle detection (`caller_chain`) and recursion hop limits (`max_depth = 2`).
- Recorded architectural decision in [decisions/log.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/decisions/log.md).

Rejected:
- Synchronous blocking turns (which would freeze the origin chat during long-running tool tasks).
- Single-hop restriction without call chaining.

Open:
- Implement Tasks 6–8 in `achiAgy` (router mixin injection, `/delegate` handler, and unit tests).

## 2026-08-27 21:14 [saved]
Goal: Align topic registration, prompt header, and plan topology from #Admin to #Atlas in achiOS Hub.

Decisions:
- Configured `atlas` as the primary topic key and display name `#Atlas` in [topic_router.py](http://100.106.210.38:8999/Code/GitHub/achiAgy/src/topic_router.py) with `admin` as an alias in `TOPIC_ALIASES`.
- Updated [atlas.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/prompts/atlas.md) header and system description to reference `#Atlas`.
- Updated [telegram-supergroup-hub-plan.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/telegram-supergroup-hub-plan.md) with `#Atlas` topic, `atlas.log` stream, and `atlas` tmux window.
- Updated unit test assertions in `achiAgy/tests/test_topic_router_and_isolation.py` (92/92 tests passing).
- Committed and pushed changes to GitHub remote origin.

Rejected:
- Retaining `#Admin` in router display when Telegram topic was renamed to `#Atlas`.

Open:
- None.

## 2026-08-27 21:08 [saved]
Goal: Rename prompt file admin.md to atlas.md and update router and plan references.

Decisions:
- Renamed prompt catalog file `prompts/admin.md` to `prompts/atlas.md` in `achiAgy`.
- Updated `prompt_file="atlas.md"` for `#Admin` in [topic_router.py](http://100.106.210.38:8999/Code/GitHub/achiAgy/src/topic_router.py).
- Updated all links and references in [telegram-supergroup-hub-plan.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/telegram-supergroup-hub-plan.md) and [decisions/log.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/decisions/log.md).
- Verified full test suite passes (92/92 tests in `achiAgy`).
- Pushed commits to GitHub remote origin across both repos.

Rejected:
- Keeping prompt filename as admin.md when all other specialist personas use their name (agi.md, ari.md, aurora.md).

Open:
- None.

## 2026-08-27 20:58 [saved]
Goal: Configure and set official name for #Admin topic persona to Atlas in achiOS Hub.

Decisions:
- Renamed the `#Admin` system prompt header and persona description in [admin.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/prompts/admin.md) to Atlas (System Architecture & Infrastructure Specialist).
- Updated [topic_router.py](http://100.106.210.38:8999/Code/GitHub/achiAgy/src/topic_router.py) with display name `#Admin (Atlas)` and added `TOPIC_ALIASES` mapping `atlas` to `admin` for `/bind` commands.
- Updated [telegram-supergroup-hub-plan.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/telegram-supergroup-hub-plan.md) topic taxonomies.
- Updated unit tests in `achiAgy/tests/test_topic_router_and_isolation.py` (92/92 tests passing).
- Committed and pushed changes to GitHub remote origin.

Rejected:
- Using purely generic or unaligned names (Ops, Archie, Argus, Axel).

Open:
- None.

## 2026-08-27 20:43 [saved]
Goal: Push all local commits to remote origin and record auto-push rule in declarative user memory.

Decisions:
- Pushed all outstanding commits across `achiAgy` (`master`) and `AIS-OS` (`main`) to GitHub origin.
- Recorded standing preference in `~/.config/achios/USER.md`: "Git workflow: Always push to remote origin immediately whenever committing changes."

Rejected:
- Leaving commits local only.

Open:
- None.

## 2026-08-27 20:38 [saved]
Goal: Stress-test and specify terminal multiplexing, per-workspace concurrency locks, and Claude Code handoff runbook for achiOS Hub.

Decisions:
- Stress-tested multi-thread terminal output presentation and concurrent workspace safety using `/grill-me` (settled Q1–Q10).
- Updated [telegram-supergroup-hub-plan.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/telegram-supergroup-hub-plan.md) with Locked Decisions D15 (Terminal Multiplexing), D16 (Workspace Concurrency Lock), D17 (Atomic State Persistence), and D18 (Shared Register Fresh Read Invariant).
- Added Section 8 (Multi-Window Tmux Terminal Console Topology), Section 9 (Workspace Concurrency Control & State Protection Architecture), and Section 10 (Claude Code Implementation Runbook & Handoff Checklist).

Rejected:
- Single stdout stream with render mutex (blocks live streaming output during simultaneous turns).
- Uncoordinated parallel file writes (causes lost edits in shared registers).

Open:
- Hand off execution to Claude Code to implement `WorkspaceLockManager`, per-topic log files, and tmux window initialization.

## 2026-08-27 20:13 [saved]
Goal: Record Phase 1 test verification (92/92 unit tests passing) and context window test results in telegram-supergroup-hub-plan.md for Claude Code cross-audit.

Decisions:
- Updated [telegram-supergroup-hub-plan.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/telegram-supergroup-hub-plan.md) status to Phase 1 Implemented & Test Verified.
- Added Section 7 detailing automated test coverage (92/92 passing across all 14 test modules), verified thread isolation mechanics, context window tracking, and audit checkpoints for Claude Code.

Rejected:
- None.

Open:
- Run Claude Code cross-audit on `achiAgy` codebase changes.

## 2026-08-27 19:53 [saved]
Goal: Implement thread-scoped session isolation, topic routing, and admin persona in achiOS Hub (achiAgy).

Decisions:
- Implemented `TopicRouter` (`src/topic_router.py`) to manage bindings between Telegram forum threads (`message_thread_id`) and topic profiles (`admin`, `general`, `schoolmem`, `achimem`, `aurora`, `ari`).
- Created prompt catalogs in `achiAgy/prompts/{admin,agi,schoolmem,achimem,aurora,ari}.md` including the dedicated `#Admin` Infrastructure Specialist prompt.
- Refactored `SessionManager` (`src/session_manager.py`) to key sessions by composite `chat_id:thread_id`, maintaining isolated conversation histories, turns, models, modes, and reasoning efforts per topic.
- Updated `src/bot.py` command and callback handlers so changing models, modes, or resetting context in `#Admin` never alters `#General` or other topics.
- Added comprehensive unit tests in `tests/test_topic_router_and_isolation.py` (92/92 tests passing).

Rejected:
- Shared session state across forum threads (would cause turn counts and model settings to overwrite across distinct topics).

Open:
- Deploy and pair `achiAgy` in Telegram Supergroup with `/bind admin` and `/bind general`.

## 2026-08-27 19:43 [saved]
Goal: Sort session-log.md into consistent reverse-chronological order and clarify logging rule.

Decisions:
- Parsed and sorted all 40 historical entries in [session-log.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/session-log.md) into strict reverse-chronological order (newest first: 2026-08-27 down to 2026-08-17).
- Verified zero content loss across all reordered session blocks.
- Clarified logging instruction in [AGENTS.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/AGENTS.md) and [.agentrules](http://100.106.210.38:8999/Code/GitHub/AIS-OS/.agentrules) to explicitly specify prepending below `# Session Log`.

Rejected:
- Forward-chronological sorting (requires scrolling past entire history to read latest session state).

Open:
- None.

## 2026-08-27 19:33 [saved]
Goal: Correct agent role attribution and refine coding best practices guide specifically for Aea (coding subagent) under Asa (orchestrator).

Decisions:
- Clarified architectural distinction: Asa is the orchestrator framework, while Aea (`src/asa/agents/aea.md`) is our primary implementation coding subagent.
- Updated [coding-best-practices-and-asa-agent-skills-guide.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/coding-best-practices-and-asa-agent-skills-guide.md) to explicitly target Aea's toolset with language coding practices (TypeScript, Python, Swift, Go, Java, SQL) and context-envelope injection via Asa.

Rejected:
- Confusing Asa (the orchestrator) with Aea (the coding subagent).

Open:
- None.

## 2026-08-27 19:22 [saved]
Goal: Record user preference and add task to implement reflect skill in achiOS.

Decisions:
- Added active task to [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) to implement the `reflect` skill and 3-subagent transcript review loop in achiOS.

Rejected:
- None.

Open:
- None.

## 2026-08-27 19:10 [saved]
Goal: Audit and document pstack skills catalog to identify workflow improvements for achiOS and Asa.

Decisions:
- Audited 45 skills in `cursor/plugins/tree/main/pstack/skills` across orchestration, investigation, writing, and engineering principles.
- Created [pstack-skills-showcase.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/pstack-skills-showcase.md) highlighting top skills (`reflect`, `show-me-your-work`, `recall`, `blast-radius`, `why`, `how`, `technical-writing`, and the 20 `principle-*` skills).
- Outlined key architectural takeaways for Asa and achiOS subagent prompts.

Rejected:
- Installing skills immediately without browsing and evaluating first.

Open:
- None.

## 2026-08-27 19:04 [saved]
Goal: Add task for Matt Pocock skills integration into Asa using writing-for-agents standards.

Decisions:
- Added active task to [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) to implement Matt Pocock engineering and productivity skills into Asa with `writing-for-agents` prompt design standards.

Rejected:
- None.

Open:
- None.

## 2026-08-27 18:35 [saved]
Goal: Extend Unslop rules into global Antigravity configuration files.

Decisions:
- Appended strict Unslop rules to `~/.gemini/config/AGENTS.md` and `~/.gemini/config/GEMINI.md` to enforce anti-AI writing across all Antigravity CLI and IDE sessions globally.

Rejected:
- None.

Open:
- None.

## 2026-08-27 18:31 [saved]
Goal: Enforce Unslop rules across voice.md, achiMem voice, AGENTS.md, and user memory.

Decisions:
- Integrated `unslop` rules into `references/voice.md` and `achiMem/wiki/personal/identity/voice.md`.
- Added strict Unslop enforcement rule to `AGENTS.md` in `## How you work with Aki`.
- Updated `~/.config/achios/USER.md` Communication Style entry via `memory_engine.py` (2,403/2,500 chars).
- Recorded decision in `decisions/log.md`.

Rejected:
- Keeping unslop rules purely on-demand rather than as hard constitutional invariants.

Open:
- None.

## 2026-08-27 18:23 [saved]
Goal: Install and sync unslop skill via skillshare.

Decisions:
- Installed `unslop` skill from `cursor/plugins/pstack/skills/unslop` into global skillshare repository.
- Ran `skillshare sync` across all configured CLI targets (universal, antigravity, claude, codex, copilot, gemini, hermes).

Rejected:
- None.

Open:
- None.

## 2026-08-27 08:28 [saved]
Goal: Mark YouTube transcript extraction and Syncthing Obsidian tasks as Done in tasks.md.

Decisions:
- Moved YouTube transcript extraction to `## Done` (clarified as standalone direct ingestion into achiMem knowledge without Asa dependency).
- Moved Syncthing real-time sync research/setup to `## Done` (configured continuous sync between Achibuntu and MacBook Air for Obsidian vaults).
- Fixed all `file:///` markdown links across `tasks.md` and `research.md` to conform to the Tailscale web viewer link standard (`http://100.106.210.38:8999/...`).
- Updated `AGENTS.md` and `.agentrules` to note dynamic adaptability of `/tasks` semantic categories to active workstreams.

Rejected:
- Rigidly freezing category names when active workstream domains shift.

Open:
- None.

## 2026-08-27 08:25 [saved]
Goal: Lock in structured /tasks format preference across AGENTS.md, .agentrules, and user memory.

Decisions:
- Locked in the 4-category structured `/tasks` layout: (1) 🔥 **Immediate Deadlines & Today**, (2) 🎓 **DLSU Academics & schoolMem**, (3) 💼 **Career, ING Onboarding & Personal Finances**, and (4) 🛠️ **Systems & Engineering (achiOS / Asa / achiMem)**.
- Enforced `• ☐ **Title:** details (!priority, @date)` checklist item format with stripped hashtags, section dividers (`---`), and clickable Tailscale web viewer links (`http://100.106.210.38:8999/...`).
- Updated `AGENTS.md` and `.agentrules`.

Rejected:
- Flat unorganized task dumps or unstyled bullet lists.

Open:
- None.

## 2026-08-27 08:21 [saved]
Goal: Revert hardcoded 244% default zoom to clean 100% fit baseline for Reset and initial load.

Decisions:
- Reverted initial and reset scale to `1.0` (`100%`) in `scripts/achi_viewer.py`.
- Tapping `🔄 Reset` returns to `100%` centered overview.
- User can zoom in step-by-step (`➕ In`) or pinch-to-zoom as needed.
- Restarted `achi-viewer.service`.

Rejected:
- Hardcoding `244%` as the default reset zoom (oversized and caused excessive close-up framing).

Open:
- None.

## 2026-08-27 08:18 [saved]
Goal: Calibrate default Mermaid diagram scale to true 1:1 native viewBox dimensions.

Decisions:
- Extracted native `viewBox` coordinate dimensions from Mermaid SVGs on render and set `svg.style.width = nativeWidth + 'px'`.
- Ensured `100%` scale represents the true 1:1 coordinate scale where diagram text matches standard readable body font size (the exact comfortable scale previously at 244%).
- Restarted `achi-viewer.service`.

Rejected:
- Leaving SVGs without explicit width (which forced browser default ~300px downscaling on wide diagrams).

Open:
- None.

## 2026-08-27 08:16 [saved]
Goal: Fix flowchart dragging, button interactions, and fullscreen mode in achi-viewer.

Decisions:
- Replaced buggy external Panzoom library with a native PointerEvents engine using `setPointerCapture` for buttery-smooth mouse and touch dragging across the entire viewport.
- Implemented in-place CSS fullscreen expansion (`.fullscreen-mode`) directly on `.mermaid-card` to eliminate SVG cloning, duplicate ID conflicts, and broken arrow markers.
- Added live zoom percentage badge (`100%`, `125%`...) and verified direct zoom step buttons (`➕ In`, `➖ Out`, `🔄 Reset`, `⛶ Fullscreen` / `✕ Exit`).
- Added 2-finger multi-touch pinch-to-zoom and mouse-wheel zoom.
- Restarted `achi-viewer.service`.

Rejected:
- Cloned SVG modals (caused duplicate ID conflicts and broken markers in complex Mermaid SVGs).
- External Panzoom library containment constraints that blocked panning on SVGs.

Open:
- None.

## 2026-08-27 08:15 [saved]
Goal: Add interactive zoom, pan, and fullscreen lightbox for Mermaid flowcharts in achi-viewer.

Decisions:
- Integrated `@panzoom/panzoom` (4.5.1) into `scripts/achi_viewer.py`.
- Added interactive `.mermaid-card` toolbar with `➕ In`, `➖ Out`, `🔄 Reset`, and `⛶ Fullscreen` controls.
- Enabled native pan and pinch-to-zoom on mobile, mouse-wheel zoom (with Ctrl/Cmd or inside modal), and drag-to-pan.
- Added full-screen `#mermaid-modal` lightbox with high-magnification panzoom (up to 10x) and escape key dismissal.
- Set SVG `maxWidth: none` in viewports to prevent aggressive downscaling of wide multi-subgraph flowcharts.
- Restarted `achi-viewer.service`.

Rejected:
- Static image exports or server-side rendering (loses interactive client-side vector fidelity).

Open:
- None.

## 2026-08-27 08:12 [saved]
Goal: Fix Mermaid flowchart/diagram rendering in achi-viewer on Tailscale web viewer (port 8999).

Decisions:
- Replaced deprecated `marked.setOptions({ highlight })` in `scripts/achi_viewer.py` with `marked.use({ renderer: { code(token) ... } })`.
- Routed `lang === 'mermaid'` to `<pre class="mermaid">${code}</pre>` and invoked `mermaid.run({ nodes: ... })` with dark theme and loose security.
- Added responsive CSS styling for `.mermaid` container (dark background, border-radius, centering, horizontal auto-scroll).
- Saved `systemd/achi-viewer.service` to repo tracking and restarted `achi-viewer.service`.

Rejected:
- Leaving marked.js with deprecated options that failed to emit `.mermaid` containers.

Open:
- None.

## 2026-08-27 08:05 [saved]
Goal: Diagnose and fix achi-viewer hanging / connection issues on port 8999.

Decisions:
- Switched `achi_viewer.py` from single-threaded `HTTPServer` to `ThreadingHTTPServer`.
- Added explicit `Content-Length` headers across all responses (`render_file`, `render_directory`, `render_not_found`, raw binary).
- Added `HTTP/1.1` and `do_HEAD` support; ignored `BrokenPipeError` on mobile disconnections.
- Restarted `achi-viewer.service` and verified sub-second 200 OK responses on `http://100.106.210.38:8999/...`.

Rejected:
- Leaving single-threaded server in place.

Open:
- None.

## 2026-08-27 07:58 [saved]
Goal: Finalize and lock Tailscale web viewer linking protocol via /grill-me alignment.

Decisions:
- Locked in Option A for all four pillars: (1) All `.md` files link directly to `http://100.106.210.38:8999/<full_path>`, (2) non-MD files/symbols remain plain/backticked text with no links, (3) full path from `$HOME` in URLs, and (4) Option C enforcement across `MEMORY.md`, `.agentrules`, `AGENTS.md`, `CLAUDE.md`, `scripts/verify_links.py`, and `.githooks/pre-commit`.
- Configured git hooks path (`git config core.hooksPath .githooks`).

Rejected:
- `file:///` URLs (banned across all models/agents).
- Short slug paths (to prevent multi-repo filename collisions).

Open:
- None.

## 2026-08-27 07:50 [saved]
Goal: Enforce strict clickable linking and 1-tap mobile previewer rules across AGENTS.md, .agentrules, and CLAUDE.md.

Decisions:
- Added explicit linking section to `AGENTS.md`, `.agentrules`, and `CLAUDE.md` requiring `file:///` URLs for all referenced files/symbols and `http://100.106.210.38:8999/...` 1-tap mobile viewer links for all `.md` files.
- Banned bare unlinked path strings in chat output.
- Created `scripts/verify_links.py` to validate markdown file linking compliance.

Rejected:
- Relying on memory heuristics alone without explicit instruction file rules.

Open:
- None.

## 2026-08-27 07:48 [saved]
Goal: Full 3-lens audit of achiAgy (Core Engine, TGDB, Self-Learning Loop) for Supergroup Hub refactor.

Decisions:
- Audited all subsystems in parallel with dedicated subagents.
- Documented complete diagnostics, failure modes (TGDB dual-writer truncations, system-prompt title leaks, 99% memory saturation with `entries[0]` eviction risks, session key collisions in forum topics), and refactor solutions in Section 6 of `telegram-supergroup-hub-plan.md`.
- Confirmed all 83 unit tests passing in `achiAgy`.

Rejected:
- Proceeding to topic refactoring without isolating pre-existing memory eviction and TGDB collision bugs.

Open:
- Implement composite session keying (`chat_id:thread_id`) and topic router.

## 2026-08-27 07:42 [saved]
Goal: Configure achiAgy workspace to ~/Code/GitHub to resolve AIS-OS multi-agy collision.

Decisions:
- Repointed `achiAgy` daemon to `~/Code/GitHub` by adding `github` argument handling in `run-bot.sh` and updating `achi-agy.service`.
- Decoupled `@achiAgyOSBot` (now scoped across all GitHub repositories) from `@achiOSHubBot` / `@achiOSClaudeBot` (scoped to `AIS-OS`).
- Verified service reload and live polling on tmux socket `achiagy`. All 83 achiAgy pytest tests passing.

Rejected:
- Keeping `achi-agy` disabled permanently — leaves cross-repo Telegram queries unsupported.

Open:
- None.

## 2026-08-21 02:40 [saved]
Goal: Ship self-learning loop v2, verify it live, and fix the reliability gaps it exposed.

Decisions:
- Loop sources candidates from the raw `prompt`, never `full_prompt` — the latter carries the frozen MEMORY.md, which is what made v1 recursive. Pinned by a test.
- Trigger on a turn counter, not a timer, so no cron path can reach the loop.
- CLI writes logged as `source: cli` but excluded from the loop's daily budget, or the model could starve it.
- Retry only what a retry can fix: network, 429, 5xx. Other 4xx fail immediately.
- Redact the token from every error string; `requests` puts the URL in exceptions and that is how it reached journald.

Rejected:
- Tightening v1's regexes — the recursion was architectural, not a regex bug.
- Deleting the poisoned tgdb notes — inert now, rewriting vault history buys nothing.
- `Restart=always` on oneshot units — systemd forbids it, and it would mask real failures.

Open: second writer is logged but ungated; capture misses plain facts. See `docs/ROADMAP.md`.

## 2026-08-20 19:10 [saved]
Goal: Kill the v1 harvester and write the v2 implementation plan.

Decisions:
- Removed the harvest stage from `vault_inbox_sync.py`; verified by unchanged MEMORY.md checksum, not inspection.
- Smoke-tested the plan's own code first; caught a wrong constructor and a UTC/Manila bug that disabled the write cap.
- Loop gets `add` and `replace`, never `remove` — autonomous deletion is the wrong trial risk.

Rejected:
- Scrubbing the 6 poisoned tgdb notes — inert now, not worth rewriting history.
- Trusting plan code unrun — two real defects only surfaced by running it.

Open:
- Plan unexecuted; 8 tasks, subagent-driven.
- Trial audit due 2026-08-27.

## 2026-08-20 18:40 [saved]
Goal: Design self-learning loop v2 to replace the self-amplifying harvester.

Decisions:
- Candidates come from the in-process `prompt`, never tgdb — only `full_prompt` carries injected memory, so recursion becomes impossible.
- Cadence copies Hermes `background_review`: turn counter in a live conversation, never a timer.
- Gate is `agy --json-schema` + gemini-3.7-flash; verified it rejects all three items the regex wrongly harvested.
- Autonomous writes for a 7-day trial, rate-capped, ledger-backed.

Rejected:
- String-stripping the injected prompt — treats a symptom.
- Batched/cron gate — Hermes suppresses exactly that case.

Open: spec at `docs/superpowers/specs/2026-08-20-self-learning-loop-design.md`.

## 2026-08-20 18:10 [saved]
Goal: Audit TGDB, correction harvester, and self-learning loop.

Decisions:
- Loop is already automatic via `achios-vault-sync.timer`; Aki initiates nothing.
- Harvester is self-amplifying: it reads tgdb notes built from agy's brain log, which stores the prompt with MEMORY.md prepended.
- Substring dedup cannot catch it — each generation is strictly longer than the last.
- The advertised LLM gate was never implemented; it is pure regex.
- Hermes `background_review.py` **does** harvest automatically — my earlier "it has none" was wrong.

Rejected: repairing the regexes — the failure is structural, not pattern quality.

Open: findings in `docs/2026-08-20-opus-audit-learning-loop.md`.

## 2026-08-20 17:00 [saved]
Goal: Full Opus audit of achiOS + achiAGY infrastructure.

Decisions:
- Audited the live server, not the repos; where Gemini's manifest and the server disagreed, the server won.
- `/asa` is broken — its SKILL.md documents a CLI installed nowhere.
- 13 findings, 3 critical, all reproduced rather than inferred.
- Made no code changes; Aki asked for an audit and a fix list.

Rejected: handing judgment to agy — it does extraction only, per the model allocation rule.

Open:
- 4 jobs still `failed`; `@achiOSBot` token in journald.
- Report at `docs/2026-08-20-opus-audit-achios-achiagy.md`.

## 2026-08-20 08:42 [saved]
Goal: Ship self-learning engine plus live Antigravity quota in /usage.

Decisions:
- Surface backend error events from the Antigravity stream instead of completing silently — quota exhaustion had looked like success.
- Query `cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary` for live quota rather than estimating from local counters.
- `/usage` renders progress bars and refresh countdowns; raw numbers were unreadable on a phone.

Rejected: inferring quota from local token tallies — drifts from the backend.

## 2026-08-19 23:12 [saved] [superseded by 2026-08-20]
Goal: Audit TGDB, correction harvester, and self-learning loop.

Decisions:
- Root cause called as "overly permissive regex". **Superseded 2026-08-20: regexes were a
  symptom.** The harvester read tgdb notes built from agy's brain log, which stores the prompt
  with MEMORY.md prepended, so it ingested its own output. Tightening regexes could not fix it.
- Formalized model allocation: Opus audits and drafts plans, Gemini 3.7 Flash executes.
- Cleaned polluted `.agentrules` and `decisions/log.md` entries.

Rejected: relying on regex tightening alone — the loop re-formed within a day.

Open: superseded by the v2 spec; see 2026-08-20 entries.

## 2026-08-19 23:05 [saved]
Goal: Audit achiAgy with Claude Opus and apply critical reliability & UX fixes via TDD.

Decisions:
- Dispatched dual Claude Opus 4.6 (Thinking) subagents to audit systems reliability and Telegram UX.
- Fixed `session_manager.py` token metrics: stopped sliding-context accumulation (fixed bogus 1.65B token metric), added `peak_context_tokens` tracking, and prevented double turn-counting via `set_conversation_id()`.
- Added rich `MODEL_REGISTRY` in `config.py` with exact token context and output bounds.
- Added native Telegram autocomplete menu (`set_my_commands` in `post_init`) with 15 direct commands.
- Implemented proactive context health alerts at ≥75% (warning) and ≥90% (critical).
- Added stripped plaintext fallback on Telegram HTML `BadRequest` errors.

## 2026-08-19 22:42 [saved]
Goal: Refine Asa architectural vision and task scope with Telegram integration.

Decisions:
- Updated Asa task scope in `tasks.md` to define Asa as a universal, bidirectional multi-agent orchestrator connecting Claude Code, Antigravity (AGY), and Codex.
- Added native Telegram integration to Asa: build a Telegram Gateway & Interactive Channel enabling tri-agent dispatch, cross-model consensus discussion, and subagent supervision from mobile.

## 2026-08-19 22:05 [saved]
Goal: Schedule Google One subscription cancellation and Google AI Pro Student discount purchase.

Decisions:
- Created Google Calendar events on `Personal` calendar:
  - 2026-10-13: Cancel current Google One subscription
  - 2026-10-14: Subscribe to Google AI Pro Student Discount (₱275/mo via SheerID)
- Added low-priority tasks to `tasks.md` with dates @2026-10-13 and @2026-10-14.

## 2026-08-19 18:20 [saved]
Goal: Upgrade email digest cron with smart VIP context, noise filtering, and LLM synthesis cards.

Decisions:
- Hybrid triage pipeline: Heuristic filtering strips routine AM/PM HDAs, LinkedIn/Indeed job blasts, promo marketing, and Laguna-only notices before passing to LLM (`agy -p` in `~/.local/share/achios/llm`).
- Structured 3-tier clean cards: `⚡ HIGH PRIORITY & VIP`, `📚 COURSES & ACADEMICS` / `💼 WORK & RECRUITING`, and `📬 UPDATES & GENERAL`.
- Embedded key personal context: Dr. Briane Samson (thesis), recommendation letter replies, Manila suspensions/typhoon advisories, ING Retail Tech internship onboarding, and critical bank/security alerts.
- Personal email scanning enabled for high-value financial/security alerts only, staying completely silent when clean.
- Deterministic fallback builder ensures reliable message formatting if LLM times out or is offline.
- Created full test suite in `tests/test_email_digest.py` (19 passing unit tests).

Rejected:
- Raw subject-only lists — lacked context on actions needed.
- LLM-only unconstrained parsing — too slow and wasted tokens on generic spam.

Open:
- Finalize elective/GE section by 2026-08-23, ahead of 2026-08-25 enrollment.
- Research & design Asa as universal bidirectional multi-agent orchestrator (Claude Opus, AGY, Codex) (`!high`).

## 2026-08-19 17:53 [saved]
Goal: Configure /tasks structured formatting convention.

Decisions:
- Standardized `/tasks` output format across Antigravity and achiOS agents: 4-tier structured layout (Immediate Deadlines, DLSU Academics, Career/Finances, Systems & Engineering) with markdown checkboxes and file links.
- Updated `AGENTS.md`, `.agentrules`, and `decisions/log.md`.

## 2026-08-19 05:50 [saved]
Goal: Bot separation (Finance + School), SSH Termius setup, ETF schedule optimization, weekly recap cron.

Decisions:
- Split one-way bots by domain: `@achiETFBot` (market digests), `@achiSchooNounceBot` (DLSU email), keeping `@achiOSBot`/`@schoMemBot` as before. `telegram_notify.py` parametrized with `env_path` to support this.
- Re-tuned ETF schedule to 08:00 + 22:00 Manila; added Sunday 18:00 weekly ETF recap.
- Termius on iPhone connected to achibuntu via Tailscale.
- Fixed a bash interpolation bug by using script-file payloads instead of quoted string interpolation.

## 2026-08-18 20:10 [saved]
Goal: CasaOS dashboard setup, DLSU schedule planner, ID 123 enlistment appointment.

Decisions:
- CasaOS live on achibuntu; Code-Server :8085, Filebrowser :8082. Webview ServiceWorker blocker fixed via Chrome insecure-origin flag, not self-signed certs.
- DLSU Term 1 planner built in Google Sheets (`1qqaTvcyz40JvyTDyT8MXiOEjPVh57PAL96jb_967BJ4`).
- Golden 14-unit load: online Tuesday + one Friday on-campus block, keeping Mon/Wed/Thu/Sat free for the ING internship.
- ID 123 2nd DL enrollment added to `DLSU` calendar, Tue 2026-08-25 11:30-12:30. Codex eval rescheduled to 2026-10-29.

Rejected:
- Monday/Thursday electives (`HCI2000`) — extra campus days conflict with internship hours.

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
