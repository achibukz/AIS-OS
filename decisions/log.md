# Decisions Log

Append-only record of meaningful decisions and why they were made. `/level-up` Phase 2 (Method interview) writes scoped automation specs here. You can also append manually whenever you decide something worth remembering.

**Format per entry:**

```
## YYYY-MM-DD — Short title

**Decision:** what was decided.

**Why:** the reasoning, constraints, and what would change your mind.

**Alternatives considered:** what else was on the table.

**Owner:** who's accountable.
```

Keep it terse. Future-you will thank present-you for capturing the *why*, not just the *what*.

## 2026-09-05 — Astra Plan Additions for Privileged Testing, Conflict Management, and /ToWork Audit

**Decision:** Expanded `docs/astra-plan.md` with explicit discussion frameworks for: (1) an administrative verification/testing agent for HITL tasks requiring elevated permissions, (2) trade-off analysis between an autonomous conflict resolution agent vs a simple feature button (#143) for parallel `/towork` jobs, and (3) a systematic workflow audit of `/towork` covering preflight, readiness polling, review diffs, and completion sync.

**Why:** Parallel `/towork` jobs inevitably trigger merge conflicts upon upstream merges, and tickets with administrative HITL testing currently block autonomous completion. Structuring these discussion areas allows a concrete decision with Astra on whether specialized agents or deterministic feature extensions provide the most robust, token-efficient solution.

**Alternatives considered:** Implementing a simple `Fix conflicts` button alone without evaluating a proactive background conflict agent, or keeping HITL testing entirely manual.

**Owner:** Agi / Aki.

## 2026-09-05 — Specific Repository Option for sync-repos and Telegram /sync

**Decision:** Designed and published tracer-bullet implementation tickets AIS-OS #12 (`Add --repo option to sync-repos to target a specific repository`) and achiCore #145 (`Accept optional repository argument in /sync and /syncres commands`).

**Why:** Full synchronization across all default repositories takes unnecessary network time and noise when only a single repository is actively being updated or investigated. Supporting `sync-repos --repo <target>` and Telegram command `/sync <repo>` (such as `/sync achiCore`) allows targeted fast-forward pulling of individual repositories from mobile or terminal.

**Alternatives considered:** Requiring full repository paths in the CLI without discovery matching (cumbersome on mobile Telegram), or relying on manual shell navigation and `git pull`.

**Owner:** Agi / Aki.

## 2026-09-05 — Multi-Ticket Conflict Resolution Flow and Telegram Repository Sync

**Decision:** Designed and published implementation tickets achiCore #142 (`/sync` repository pull command) and #143 (autonomous `Fix conflicts` button and resolution flow for `/towork` jobs).

**Why:** Concurrent ticket execution causes branch drift and merge conflicts (particularly on `session-log.md`), which previously stalled `/towork` jobs and required manual terminal intervention. Automated conflict delegation to Aea with subsequent Luna verification allows hands-off resolution from Telegram. The `/sync` command gives Aki immediate visibility and one-tap fast-forward synchronization across all repositories from his phone.

**Alternatives considered:** Using git rebase instead of merge commits (breaks signed commits and review history), resolving conflicts strictly through deterministic regex heuristics (fails on semantic code conflicts), or keeping repo sync purely as a local terminal script.

**Owner:** Atlas / Aki.

## 2026-09-05 — Google Cloud OAuth Consent Screen Transition to Production Mode

**Decision:** Promoted the `achiclaude` GCP OAuth consent screen from Testing to "In Production" status, re-authenticated all four profiles (`gws-main`, `gws-personal`, `gws-work`, `gws-dlsu`), and verified Google Drive access alongside Gmail and Calendar.

**Why:** In Testing mode, Google imposes a 7-day expiration policy on OAuth refresh tokens. Switching to Production mode eliminates the 7-day expiration cap, providing permanent refresh tokens and preventing weekly auth dropouts. The Google Drive scope (`https://www.googleapis.com/auth/drive`) is active and verified across all four accounts.

**Alternatives considered:** Continuing weekly re-authentication, or using service accounts (which cannot access personal user Gmail/Calendar/Drive without Google Workspace domain delegation).

**Owner:** Aki.

## 2026-09-03 — Automated Immich Album and Library Synchronization Timer

**Decision:** Automated the Immich folder-to-album synchronization via `systemd/achios-immich-sync.{service,timer}` scheduled at `00:30 Asia/Manila` with `Persistent=true`. Enhanced `scripts/immich_folder_sync.sh` to trigger the Immich external library scan via REST API prior to running `salvoxia/immich-folder-album-creator`.

**Why:** Media added to `~/Documents/Files/personal/memories` throughout the day needs automatic ingestion into Immich albums after midnight without requiring manual terminal invocations.

**Alternatives considered:** Triggering scans from crontab (which lacks named timezone support on Ubuntu), relying solely on Immich's native midnight scan without album synchronization, or running a continuous filesystem watcher daemon.

**Owner:** Aki.

## 2026-09-02 — Modular Backlog Registers for Systems Engineering and Asa Workflows

**Decision:** Moved granular Systems & Engineering and Asa & Research sub-tasks out of `tasks.md` into dedicated modular backlog files (`docs/tasks-systems-engineering.md` and `docs/tasks-asa-research.md`), linked via anchor tasks in master `tasks.md`.

**Why:** Running `/tasks` and the daily brief was getting bloated with 20+ fine-grained development tickets, obscuring high-priority daily personal, career, and onboarding items.

**Alternatives considered:** Keeping all sub-tasks in master `tasks.md`, archiving incomplete engineering tickets into `archives/`, or tracking them solely in individual GitHub repository issue trackers.

**Owner:** Aki.

## 2026-09-02 — Immich Folder Album Synchronization via salvoxia/immich-folder-album-creator

**Decision:** Use `salvoxia/immich-folder-album-creator` in Docker with `ALBUM_LEVELS=1` and `UNATTENDED=1` across `big-bear-immich_big_bear_immich_network` to synchronize the 114 event folders in `/home/achibukz/Documents/Files/personal/memories` into Immich albums. Added `scripts/immich_folder_sync.sh` as the repeatable sync runner.

**Why:** Immich does not auto-create albums from mounted external library directories. The memories directory already follows a strict `YY.MM.DD- EventName` convention with multi-day subfolders (such as `26.06.21- Japan 2026`) that map cleanly into parent event albums.

**Alternatives considered:** Manual album curation in the Immich UI, re-uploading via Immich CLI `--album`, or writing a custom REST API sync script.

**Owner:** Aki.

## 2026-09-01 — Deliver the Windows diagnostic through Drive and Gmail

**Decision:** AUTO-Zoom-Leaver #1 must upload its tested diagnostic executable to Google Drive, share it with `shpengson@gmail.com`, and email the download link and SHA-256 checksum. The issue records the delivery timestamp in PHT, filename, checksum, and Drive file ID.

**Why:** Gmail blocks `.exe` attachments and archives that contain executables. A Drive link delivers the requested file without creating a ticket criterion that Gmail will reject.

**Alternatives considered:** Attach the executable directly or hide it inside a ZIP archive.

**Owner:** Aki.

## 2026-09-01 — Windows probe ships as a diagnostic executable

**Decision:** The first AUTO Zoom Leaver Windows ticket must publish a read-only diagnostic executable as a GitHub Actions artifact. Aki runs it on the Windows laptop without cloning the repository or installing Python, then returns the generated sanitized report. The diagnostic inspects the Zoom leave prompt but never invokes a control.

**Why:** The implementation needs exact Windows UI Automation names, types, and IDs from a live Zoom session. A narrative test report cannot supply those selectors, while requiring a development setup on the test laptop adds work unrelated to validation.

**Alternatives considered:** Clone the repository on the laptop, install Python and dependencies by hand, or accept a narrative report without machine-readable control metadata.

**Owner:** Aki.

## 2026-09-01 — AUTO Zoom Leaver Windows v1 planning baseline

**Decision:** Propose a Windows 10 and 11 console executable that finishes the existing `zoom_auto_leaver.py` path. Use Microsoft UI Automation to read Zoom controls and invoke only the exact "Leave Meeting" action. Require a Windows accessibility-tree probe before implementation. Keep system tray UI, installer, signing, and auto-update outside v1. Do not publish `/agy-tickets` issues until Aki approves the plan and full issue bodies.

**Why:** The repository calls its untested Python script a Windows version, but it has no packaged executable and blindly presses `Enter` after `Alt+Q`. That can select the wrong host action. The proposal needs a live Windows probe because Zoom's accessible control tree cannot be confirmed from Achibuntu.

**Alternatives considered:** Starting a second Windows implementation, keeping title-only detection, using a blind confirmation key, and expanding v1 into a tray application.

**Owner:** Aki.

## 2026-08-31 — Chelz Class Schedule Hidden Calendar (cc sched)

**Decision:** Created a secondary Google Calendar named `cc sched` under `akibukuhan10@gmail.com` with `hidden: true` and `selected: false`, populated with weekly recurring class blocks for Chelz through December 8, 2026 (Monday 09:00-12:00 & 13:30-19:30, Tuesday 10:30-13:30, Wednesday 13:30-16:30, Thursday 09:00-12:00 & 13:30-16:30, Friday 10:30-13:30).

**Why:** Allows fast schedule alignment and availability queries against Chelz's schedule without cluttering Aki's visible daily calendar views.

**Alternatives considered:** Storing the schedule solely in text memory without calendar events (rejected because calendar objects allow structured overlap/freebusy calculations).

**Owner:** Aki.

## 2026-08-31 — Pause TGDB transcript automation

**Decision:** Removed TGDB transcript export and `tgdb/` staging from `scripts/vault_inbox_sync.py`. The timer continues syncing `schoolMem/inbox/` and `achiMem/inbox/`.

**Why:** The pipeline committed test mocks, unavailable-media placeholders, and repeated transcript rewrites. [achiCore #83](https://github.com/achibukz/achiCore/issues/83) will hold the redesign discussion before TGDB automation returns.

**Alternatives considered:** Stopping the whole vault timer, which would also strand mobile inbox captures.

**Owner:** Aki.

## 2026-08-31 — Canonical Hub Tmux Window Sequence with career-ops after achiMem

**Decision:** Enforced a persistent canonical topic window order in `achiCore/scripts/tmux-bot.sh`: `0: daemon`, `1: general`, `2: atlas`, `3: schoolmem`, `4: achimem`, `5: career-ops`, `6: aea`, `7: luna`, `8: aurora`, `9: ara`, `10: ari`, with dynamic runtime topics appended after.

**Why:** Guarantees that every reboot and service restart initializes the tmux windows in Aki's exact preferred order without requiring manual window swapping.

**Alternatives considered:** Ad-hoc interactive window moves via `swap-window` (rejected because runtime moves reset on server reboot or service restart).

**Owner:** Aki.

## 2026-08-31 — Autostart achiCore Hub Daemon on Server Boot via Systemd

**Decision:** Updated `systemd/achi-core.service` in `achiCore` to execute `scripts/tmux-bot.sh hub` on socket `achicore-hub` with `ExecStop=-/usr/bin/tmux -L achicore-hub kill-server`, installed the service unit to `~/.config/systemd/user/achi-core.service`, and verified auto-initialization of topic log windows on boot.

**Why:** Ensures the achiCore supergroup hub daemon and all topic console tail windows launch automatically whenever Achibuntu boots or reboots, allowing Aki to attach directly to `achicore-hub` without manual terminal initialization.

**Alternatives considered:** Manual session startup on login (rejected because unattended Telegram polling is required after power cycles or reboots).

**Owner:** Aki.

## 2026-08-30 — Tauri Desktop GUI Architecture for achiOS, achiCore, and achiMem

**Decision:** Architected a native macOS desktop control center using Tauri v2 (Rust + React/Tailwind) connecting to Achibuntu over SSH/SFTP (`russh` / `ssh2`) and Tailscale per [2026-08-30-tauri-desktop-gui-architecture-and-blueprint.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-08-30-tauri-desktop-gui-architecture-and-blueprint.md). Features a live multi-agent Kanban monitor (`~/.local/state/achicore/`), dynamic topic/model matrix editor, two-way `tasks.md` synchronization, declarative memory budget monitor (`USER.md`, `MEMORY.md`), and systemd user unit daemon controls.

**Why:** Gives Aki a centralized native macOS desktop cockpit with system tray indicators, desktop notifications for completed turns, and direct management of topic configurations without requiring a separate web server open on Achibuntu.

**Alternatives considered:** Web-only browser dashboard (rejected because it lacks native menu bar indicators, macOS notifications, and requires a dedicated long-running web daemon on Linux) and Electron wrapper (rejected due to excessive memory overhead).

**Owner:** Aki.

## 2026-08-27 — achiAgy Streaming Pipe Inactivity Timeout & Keepalive Architecture (D39–D43)

**Decision:** Architected the streaming pipe inactivity watchdog, heartbeat ticks, and milestone progress streaming in `achiAgy` per [2026-08-27-streaming-inactivity-timeout-and-keepalive-plan.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/2026-08-27-streaming-inactivity-timeout-and-keepalive-plan.md). Features a 600s configurable stream idle watchdog (`ACHIAGY_STREAM_IDLE_TIMEOUT`), periodic 15s internal `heartbeat` AgentEvents to keep event loops alive during silent background task execution, live intermediate milestone streaming to Telegram in `src/bot.py`, and orchestrator status polling patterns (`asa status` every 30s).

**Why:** Prevents premature `⚠️ Execution Error: timeout waiting for response` failures during long multi-agent research runs (such as `asa` STORM workflows) where detached workers run silently in the background on disk while the top-level agent awaits completion.

**Alternatives considered:** Modifying detached `asa` worker processes to write fake stdout events (rejected to maintain clean worker isolation) and relying on client reconnection without server keepalives (rejected because it terminates the active Telegram turn with an error).

**Owner:** Aki.

## 2026-08-27 — Centralized Documents & Media Store Architecture (D34–D38)

**Decision:** Designed a centralized, non-markdown document repository at `~/Documents/Files/` synced via a dedicated Syncthing folder (`achi-files`) across Achibuntu and AchiBook Air per [2026-08-27-centralized-documents-and-media-store-plan.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-08-27-centralized-documents-and-media-store-plan.md). Features domain-aligned taxonomy (`personal/{health,finance,legal}`, `academic/<course>`, `career/<company>`), ISO date-prefixed file naming (`YYYY-MM-DD-descriptor.ext`), Syncthing-only storage (no Git repository or Git LFS bloat), clean retirement/gitignoring of `raw/` in `achiMem` and `schoolMem`, and dual referencing via Tailscale web viewer links (`http://100.106.210.38:8999/Documents/Files/...`) and normalized filesystem paths.

**Why:** Decouples heavy binary files (prescriptions, multi-page PDF contracts, government forms, scans) from Git-backed Obsidian markdown vaults to permanently stop repository bloat and sync delays, while keeping all personal and academic assets accessible across macOS, Linux, AI daemons, and mobile Telegram dispatch.

**Alternatives considered:** Keeping `raw/` inside Obsidian vaults (rejected due to Git repo size bloat), using Git LFS (rejected due to GitHub bandwidth limits and merge complexity), and expanding existing Obsidian Syncthing root to the whole `~/Documents/` folder (rejected to keep failure domains and ignore rules isolated).

**Owner:** Aki.

## 2026-08-27 — Outbound Server Media & Document Dispatch Architecture (D27–D33)

**Decision:** Designed the outbound media and document dispatch pipeline in [telegram-supergroup-hub-plan.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/telegram-supergroup-hub-plan.md). The daemon intercepts standard markdown image references (`![caption](<path>)`), resolves paths across three tiers (absolute, tilde expansion, workspace relative), validates against a security blacklist (`~/.ssh`, `~/.config/achios`, `~/.gnupg`, `~/.hermes`), dispatches images via `bot.send_photo()` or `bot.send_document()`, and rewrites markdown tags in the text message to clickable Tailscale web viewer links (`http://100.106.210.38:8999/...`).

**Why:** Allows Aki to request stored documents and visual files (such as medical prescriptions, study diagrams, receipts, and PDFs) from his phone via Telegram and receive the actual image or document directly in the thread without manual file transfers.

**Alternatives considered:** Custom tag syntax `[send_photo: path]` (rejected because standard markdown image syntax is model-native and requires zero custom prompting) and always-uncompressed document mode (rejected in favor of smart extension routing for instant mobile photo previews).

**Owner:** Aki.

## 2026-08-27 — Cross-Topic Delegation & Multi-Agent Mesh Architecture (D19–D26)

**Decision:** Designed cross-topic delegation protocol and multi-agent mesh architecture in [telegram-supergroup-hub-plan.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/telegram-supergroup-hub-plan.md). Features a dual-hybrid trigger (`/delegate <topic> <task>` and `delegate_topic` tool), persistent thread session ingestion in `sessions.json`, non-blocking asynchronous dispatch with live target output streaming and origin completion receipts, shared `prompts/asa.md` subagent orchestration prompt mixin, and cycle/hop limits (`caller_chain`, `max_depth = 2`).

**Why:** Allows Aki and orchestrating personas like Agi (#General) to route specialist tasks to dedicated topics (such as #Atlas for infra diagnostics or #schoolMem for coursework) without manual copy-pasting, chat lockups, or console log clutter in general conversation.

**Alternatives considered:** Synchronous blocking execution (rejected because long-running tool tasks freeze the origin chat session) and single-hop restriction (rejected in favor of 2-hop delegation with cycle detection).

**Owner:** Aki.

## 2026-08-27 — Name #Admin Infrastructure Specialist Persona Atlas

**Decision:** Officially named the `#Admin` topic persona **Atlas** across [atlas.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/prompts/atlas.md), [topic_router.py](http://100.106.210.38:8999/Code/GitHub/achiAgy/src/topic_router.py), and [telegram-supergroup-hub-plan.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/telegram-supergroup-hub-plan.md). Added `atlas` alias support in `TopicRouter` to allow `/bind atlas` or `/bind admin` interchangeably.

**Why:** Aki approved the moniker Atlas to maintain characterful naming consistency alongside Agi, Ari, and Aurora, representing the heavy-lifting system architecture, daemon supervision, and crash recovery responsibilities of the admin topic.

**Alternatives considered:** Archie, Argus, Aegis, Axel, and purely functional names like Infra/Ops.

**Owner:** Aki.

## 2026-08-27 — achiOS Hub Terminal Multiplexing & Workspace Concurrency Locks (D15-D18)

**Decision:** Finalized architecture for multi-window tmux terminal multiplexing and workspace mutation concurrency safety in [telegram-supergroup-hub-plan.md](http://100.106.210.38:8999/Code/GitHub/achiAgy/docs/telegram-supergroup-hub-plan.md). The daemon writes isolated rich ANSI event streams to `topics/<topic>.log` tailed by pre-created tmux windows (`daemon`, `general`, `admin`, `schoolmem`, `achimem`), while `WorkspaceLockManager` serializes concurrent turns targeting the same repository path to prevent write collisions.

**Why:** Running multiple concurrent Telegram threads through a shared terminal stdout stream causes mixed log outputs, while simultaneous write tasks in the same repository risk overwriting registers ([tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md)) or source files. Per-topic log pipes eliminate console clutter, and per-workspace async locks eliminate race conditions while preserving full parallelism for different repositories.

**Alternatives considered:** Single-window terminal render mutex (rejected because it blocks live stream output during simultaneous turns) and git worktrees (rejected due to merge overhead for simple markdown registers).

**Owner:** Aki.

## 2026-08-27 — achiOS Hub Thread-Scoped Session & Persona Isolation

**Decision:** Implemented composite session keying (`chat_id:thread_id`), topic persona router (`src/topic_router.py`), and dedicated topic prompts in `achiAgy` (`prompts/{admin,agi,schoolmem,achimem,aurora,ari}.md`). Model, mode, and effort configurations can now be altered per-thread without affecting other threads.

**Why:** Aki requested dedicated context windows and independent model/mode controls between `#Admin` (infra/architecture) and `#General` (orchestration) in the Telegram Supergroup hub. Isolating conversation IDs and parameter settings per `message_thread_id` prevents context leakage and cross-topic disruption.

**Alternatives considered:** Single global session shared across threads (rejected because turns and model overrides would clobber across topics).

**Owner:** Aki.

## 2026-08-27 — Standardize session-log.md to Strict Reverse-Chronological Order

**Decision:** Formally standardized [session-log.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/session-log.md) to strict reverse-chronological order (newest first) and updated [AGENTS.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/AGENTS.md) and [.agentrules](http://100.106.210.38:8999/Code/GitHub/AIS-OS/.agentrules) to replace ambiguous "append" phrasing with explicit prepending under `# Session Log`.

**Why:** Early session logs from Aug 17 to Aug 21 were appended to the bottom, while sessions from Aug 20 evening and Aug 27 were prepended to the top, creating a split forward/reverse ordering. Reverse-chronological order allows any agent or human to immediately see the latest session context without scrolling past the entire history.

**Alternatives considered:** Forward-chronological order (rejected because it forces models and humans to read through hundreds of lines of older sessions to locate recent state).

**Owner:** Aki.

## 2026-08-27 — Enforce Unslop Rules across Voice, AGENTS.md, and Memory

**Decision:** Adopted and strictly enforced the `unslop` skill rules across `references/voice.md`, `achiMem/wiki/personal/identity/voice.md`, `AGENTS.md`, and `~/.config/achios/USER.md`.

**Why:** Aki mandated strict elimination of AI tells, puffery, robotic buzzwords, filler conversational phrases, sycophancy, and unnatural structures. Grounding responses in plain human rhythm, concrete facts/measurements, and active voice ensures authentic communication across all pairing sessions and drafted correspondence.

**Alternatives considered:** Relying solely on on-demand skill invocation without constitution-level embedding (rejected because voice guardrails must apply unconditionally).

**Owner:** Aki.

## 2026-07-18 — scribe: local Whisper over cloud APIs

**Decision:** Built `projects/scribe/` (first project in the new `projects/` folder) on whisper.cpp large-v3-turbo running locally, not Groq/OpenAI transcription APIs.

**Why:** Free and unlimited on the M4 (about 12x realtime, a 90-min lecture in 7 min), works offline, recordings never leave the machine, and no 25MB file caps that would force chunking long lectures. Taglish needs large-v3-turbo; smaller models butcher code-switching. Would revisit if turnaround ever matters more than cost (Groq is near-instant).

**Alternatives considered:** Groq API (fast, free tier, but rate limits and file caps), OpenAI Whisper API (paid, same caps), mlx-whisper (simpler Python, but no clean progress reporting — whisper.cpp's streamed segment timestamps give real per-file progress bars).

**Owner:** Aki.

## 2026-07-18 — scribe: anti-hallucination settings

**Decision:** Run whisper.cpp with `-mc 0` (no text-context conditioning) and collapse consecutive duplicate segments when writing transcripts.

**Why:** First real test (5-min Taglish meeting audio) hit Whisper's known failure mode: quiet, far-from-mic stretches looped one phrase 40+ times. `-mc 0` stops the model feeding its own output back in; the dedup catches whatever slips through. Note: `-nc` is not a valid whisper-cli flag and fails silently — it exits 0 with no output.

**Alternatives considered:** VAD preprocessing (extra model download and pipeline complexity, not needed yet), leaving defaults (unusable transcripts on real recordings).

**Owner:** Aki.

## 2026-07-18 — scribe: output conventions

**Decision:** Transcripts land in `projects/scribe/outputs/` as `YYYY-MM-DD-<source-slug>.md` (zero-padded date, collision auto-suffix `-2`), timestamped paragraphs in ~60s windows. Upload copies deleted after success. Sequential queue, one file at a time.

**Why:** Single fixed destination keeps the app simple; date-prefixed names sort correctly and the format drops straight into schoolMem raw→wiki ingestion. Deleting uploads stops the folder silently accumulating gigabytes of video. Sequential because two large-v3-turbo instances would thrash 16GB RAM.

**Alternatives considered:** Per-batch destination picker (more UI, maybe later if lecture transcripts should land directly in schoolMem), keeping source copies, parallel workers.

**Owner:** Aki.

## 2026-08-10 — achiOS session capture into achiMem

**Decision:** SessionEnd hook writes a mechanical stub into `achiMem/raw/sessions/`, appends to `achiMem/log.md`, commits path-scoped, then detaches a background Haiku call to enrich the stub. A SessionStart hook reads those files back as the recall digest. Unattended automation never writes to `achiMem/wiki/`. claude-mem is excluded from this repo via `CLAUDE_MEM_EXCLUDED_PROJECTS`.

**Why:** Session work was evaporating — decisions and discoveries lived only in transcripts. achiMem's constitution makes INGEST a two-phase human gate and forbids inventing facts about Aki, so unattended writes are routed to targets where those rules do not bind (`raw/`, `log.md`) and everything touching `wiki/` waits for a human. The stub is written before the model is called and `status` only flips on success, so a dead or garbage Haiku call leaves a valid unenriched file rather than a truncated one. Haiku is given no tools at all; its stdout is captured and Python does the writing, so a model failure can produce bad text but never a bad file operation. Would revisit the exclusion if achiMem's recall proves thinner in practice than claude-mem's observation database.

**Alternatives considered:** Raw drop only (safest, but the wiki stays stale until Aki sits down with it). Full auto-write into `wiki/` (fastest to a current wiki, but defeats the one mechanism that makes the vault trustworthy). Stop hook instead of SessionEnd (fires every turn, mostly noise). Synchronous enrichment (blocks session exit for 20-30s). Keeping claude-mem on alongside (pure redundancy, duplicate Haiku cost per session).

**Owner:** Aki.

## 2026-08-10 — gws multi-account: one config dir per Google account

**Decision:** Reach all four Google accounts through `gws`, each in its own config dir with the file keyring backend — `gws-main` (aki.bukz12), `gws-personal` (akibukuhan10), `gws-work` (akibukzwork), `gws-dlsu` (abram_bukuhan@dlsu.edu.ph). Every call sets both `GOOGLE_WORKSPACE_CLI_CONFIG_DIR` and `GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file`. The old single-account `~/.config/gws` is retired, not extended. `gws-personal` is the default for calendar; `gws-dlsu` for DLSU event detail; `gws-work` only to write to Job.

**Why:** gws holds exactly one account per config dir, and the macOS keyring entry it writes is service `gws-cli` / account `achibukz` — not namespaced per dir. Separate dirs alone would have had the four accounts overwrite each other's credentials; the file backend is what actually isolates them, storing `credentials.enc` inside each dir. Verified by having all four answer `getProfile` correctly in a single run. Two server-side blockers had to clear first: the `achiclaude` consent screen was in Testing, which caps refresh tokens at 7 days and rejects non-test-users outright (this was the standing `invalid_grant` that had left calendar broken since roughly June), fixed by publishing to Production; and non-owner accounts got "Caller does not have required permission to use project achiclaude" because gws sends a quota-project header, fixed with `roles/serviceusage.serviceUsageConsumer` on each. Any account added later needs that grant too. Would revisit if Google ever tightens unverified-app policy enough to break the interstitial bypass.

**Alternatives considered:** Keep one account and rely on calendar sharing — rejected once the calendar lists were compared: sharing covers school calendars into work, but each account still holds mail only it can read, and akibukuhan10's own primary plus Personal and Bdayy never appear under work. Adding the other accounts as test users instead of publishing — works in a minute but keeps the 7-day expiry, meaning re-authenticating four accounts every week forever. Overriding `GOOGLE_WORKSPACE_PROJECT_ID` to dodge the quota-project error — treats the symptom and would break quota attribution. A wrapper script to hide the two env vars — deferred; two exported vars are not enough friction to justify another script to maintain.

**Owner:** Aki.

**Incidental finding:** Canvas already pushes DLSU deadlines into a read-only Google Calendar import feed (`ts4ja84d594ptjit87rv0bo63qilsjea@import.calendar.google.com`), visible from `gws-personal` and `gws-dlsu`. Course due dates are therefore readable via `gws` without driving Chrome. `/canvas-tracker` stays authoritative when the two disagree.

## 2026-08-10 — scribe: never let large binaries sit in the git index

**Decision:** Large model weights and generated transcripts stay out of the index permanently, not just out of `git status`. When a big file is already staged, `.gitignore` is the wrong tool — the entry has to be removed from the index. Corollary for scribe: whisper.cpp failures must report whisper's own stderr, never a generic message.

**Why:** scribe broke today and the cause was invisible from both ends. On 2026-07-18 the 1.6GB `models/ggml-large-v3-turbo.bin` got staged before `projects/scribe/.gitignore` existed. `.gitignore` only governs untracked files, so writing the ignore rule afterwards did nothing — the model sat staged in the index for three weeks while `git check-ignore` happily reported it as ignored. On 2026-08-10 at 11:41:54 GitHub Desktop ran `git stash` as part of its own housekeeping, which swept every staged path out of the working tree: the model, the three July transcripts, and the repo's `.obsidian/` config. scribe then failed every job with "whisper.cpp exited with an error" because `stderr=DEVNULL` discarded the actual line, `whisper_init_from_file_with_params_no_state: failed to open '...'`. Two independent faults, and neither one named itself. Recovery was only possible because the stash still held the blob — `git cat-file blob <sha>` restored the model and transcripts byte-identical, then dropping the stash and running `gc --prune=now` took `.git` from 1.4GB to 292KB. Would revisit if scribe ever needs its model committed for reproducibility, which would mean git-lfs, not a bare blob.

**Alternatives considered:** Re-downloading the 1.6GB model from HuggingFace — the obvious move, and what I nearly did before checking whether the file existed anywhere on disk; it would have silently abandoned three irreplaceable lecture transcripts sitting in the same stash. Restoring via `git stash pop` — would have re-staged the model and set the trap again. Keeping the stash as a backup — it was the only copy of the model, but holding it cost 1.4GB to guard a file that is one download away, while the transcripts are not reproducible and belong on disk. `stderr=subprocess.PIPE` for the error capture — deadlocks, since whisper floods stderr while the stdout read loop is mid-iteration.

**Owner:** Aki.

**Operational note:** Assume GitHub Desktop will stash anything staged, at a moment of its choosing. Before using it on this repo, check `git ls-files projects/scribe` shows only source. The three recovered transcripts are in `outputs/`; the 2026-08-10 CSOPESY one was moved to `schoolMem/raw/AY2526-T3/CSOPESY/` for ingestion.

## 2026-08-16 — linkedin-poster: a separate skill from message-writer, with a public-surface calibration

**Decision:** LinkedIn posts get their own skill (`~/.claude/skills/linkedin-poster/`) rather than another branch inside `message-writer`. Standing calibration for Aki's posts, set by him today: one to three emoji maximum placed at paragraph ends, `[tag: Full Name]` placeholders instead of attempted @-mentions, and no hashtags at all. The skill drafts and copies to the clipboard; it never posts.

**Why:** `message-writer` already carries a warning that a LinkedIn DM is not a LinkedIn post, and that line exists because conflating them produced a draft Aki rewrote from scratch. The two surfaces fail in opposite directions, which is what makes them separate skills rather than one skill with a register table. A DM fails long — its whole discipline is deleting sentences until only the ask remains. A post fails flat: his natural register is understated and candid, and ported onto a broadcast surface it undersells work that is genuinely good and wastes a milestone he only posts about once. The other half of the problem is the platform's own gravity toward performative gratitude, which is also a language model's default output, so the skill has to steer between two failure modes at once instead of enforcing one constraint. Grounding is the mechanism that does it: read the photos, grep `career-ops/cv.md`, and refuse to invent a detail, because a fabricated number on a public post is unrecoverable in a way a private draft is not. The emoji rule is a real deviation from `references/voice.md`, which bans them outright. It stands because voice.md's plain-text rule governs deliverables handed *to* Aki, and the genre norm among his classmates runs much heavier (🚀✨🎓 clusters); one to three is his own middle. No hashtags is his call against the research, which says three to five is optimal. Would revisit the emoji and hashtag settings if he starts posting weekly and wants reach, not just record.

**Alternatives considered:** Extending `message-writer` with a post branch — rejected because its Step 3 ask-vs-answer shape logic and its "cut sentences until only the question remains" instinct are actively wrong here, and a skill that contradicts itself halfway through is worse than two skills. Matching the sample posts fully, emoji throughout and numbered takeaway lists — Aki's own call against it; that register reads as the genre rather than as him. Generating literal `@Name` strings — LinkedIn only creates the mention when he types `@` in the composer and picks from the dropdown, so plain-text `@Name` posts as dead text and silently loses the tag. Hashtags at three to five per the research — his call to skip.

**Owner:** Aki.

**Research captured in the skill:** mobile truncates at ~140 characters and 60-70% of readers never expand, so the first two lines are the post; 1,300-2,100 characters is the engagement band and under 500 reads as low-effort; tagging people lifts reactions ~15%, roughly double the hashtag effect; broetry, engagement-bait CTAs, and humblebrag-as-lesson are the recognized cringe formats to avoid.

**First-run calibration (same day):** The Accenture post was the skill's first real use, and the correction pattern is now written into the skill as its own section. Aki kept the drafted structure untouched and rewrote the substance across four rounds, which localises where the skill was weak: the shape rules were right, the elicitation was not. All three takeaways were replaced wholesale, one of which had characterised judge feedback with no source. A real measured finding of his was cut in favour of a reflective takeaway, so numbers belong in the description paragraph rather than the takeaway slots. Two closing flourishes were deleted, establishing that he ends a paragraph on the admission and never caps it. Role framing was corrected from cv.md's QA lead to team lead and backend, so positioning is a question to ask rather than a lookup. The closer became a named ask for an internship. The closing 🚀 became 🥰, which fixes the emoji rule to specify warmth over aspiration, since 🚀 is the emoji the platform template reaches for. The fix is a mandatory up-front ask for his own rough takeaways and his role framing, in one message, before drafting: four correction rounds all landed on content no file could have supplied.

## 2026-08-17 — the daily brief, and cron→Telegram as a reusable path

**Decision:** Scheduled work on `achibuntu` reports to Telegram through a dedicated bot that is Aki's, not Hermes'. `scripts/telegram_notify.py` is the single sender every job imports; credentials live in `~/.config/achios/telegram.env` at mode 600, outside the repo. The first job is `scripts/daily_brief.py`, firing `0 8 * * *` under `CRON_TZ=Asia/Manila`. It builds two messages — schedule and tasks — deterministically in Python, then passes each to `claude -p --model claude-sonnet-5` for a wording pass, falling back to the structured text whenever the model call fails. `tasks.md` at the repo root becomes the master task register, and CLAUDE.md instructs that tasks Aki mentions in conversation get written there in the same turn, without asking. The path is captured as the `cron-telegram` skill so the next scheduled job is configuration rather than rediscovery.

**Why:** The original ask was explicitly "so that the cron job won't use too much tokens," and the first build honoured that literally with no model at all. Aki then asked for a nicer, more human format and specified Sonnet, which resolves the apparent contradiction: the constraint was never "no model," it was "not Opus, not expensive, not per-item." Structuring in Python and spending exactly one Sonnet call per message keeps the data layer free and deterministic while paying for the only part that needs judgment. The fallback matters more than the polish — a cron that goes silent is worse than one that sends plainer text, so a failed or slow model call degrades rather than aborts. Isolation from Hermes was Aki's call and is worth more than the duplicated bot: Hermes runs a sub-70B model autonomously with write access, and a shared notification channel would have coupled the two stacks' failure modes. Reusing his existing Google OAuth tokens by copying them into `~/.config/achios/` rather than running a fresh consent flow gets the same isolation at the file level without a browser dance on a headless box. Would revisit the two-message split if the content grows enough that Telegram's 4096-character limit forces a third.

**Alternatives considered:** Hermes' existing bot and its `gcal_upcoming.py` — rejected by Aki, who wanted this isolated to Claude Code; the runtime now reads nothing under `~/.hermes/`. The Anthropic API with a key — works, but bills separately when `claude -p` already runs on his subscription. Running `claude -p` from the repo directory — this loads the project CLAUDE.md *and* fires the achiMem SessionEnd hook, writing a junk session log to the vault nightly; the job runs from a bare `~/.local/share/achios/llm/` instead. `0 0 * * *` in UTC to match the box — correct but unreadable, and it silently breaks the day Aki edits it thinking in local time; `CRON_TZ=Asia/Manila` keeps the crontab in the timezone he reasons in. Matching calendar colours to circle emoji by RGB distance — plausible and wrong, because Google's palette is dark and saturated, so basil green `#0b8043` landed on ⚫; hue matching with saturation and brightness gates fixed it. Keeping open questions in the brief — cut by Aki after seeing it; they made the message 6,900 characters and buried what was actionable.

**Owner:** Aki.

**Operational note:** Aki's bot token leaked into a session transcript during setup, pasted inside a terminal error he was reporting. achiMem captures transcripts into a git repo, so the correct response is immediate BotFather `/revoke`, not redaction. The trigger was a multi-line shell command that wrapped in his terminal and split, executing the URL as its own command — anything he is asked to paste should fit one line, or belong in a script.

## 2026-08-17 — systemd timers replace cron on achibuntu

**Decision:** The daily brief now runs from a systemd **user** timer, `achios-daily-brief.timer`, with `OnCalendar=08:00 Asia/Manila` and `Persistent=true`. The crontab entry is gone and the crontab holds no jobs. New scheduled work uses timers too; the `cron-telegram` skill was rewritten to teach that path and keeps its name only because "cron" is still what Aki calls it.

**Why:** Yesterday's entry above records `CRON_TZ=Asia/Manila` as the readable way to keep the crontab in Manila time. That was wrong, and it is worth being precise about how wrong. Ubuntu's `cron 3.0pl1` has no per-user timezone support at all — `man 5 crontab` states that `TZ` in a crontab "will affect only the commands executed in the crontab, not the execution of the crontab tasks themselves," and `grep -c CRON_TZ /usr/sbin/cron` returns 0, so the string is not even in the binary. The box runs `Etc/UTC`, which made `0 8 * * *` mean 4pm Manila. The brief was installed at 22:35 UTC on the 16th and had therefore never fired once; `~/.local/state/achios/daily_brief.log` did not exist. Confirmed empirically as well, with a probe entry armed in Manila time that never went off.

The second reason is hardware. `achibuntu` is a batteryless HP Notebook — `/sys/class/power_supply/` contains only `AC`, no `BAT0` — so any mains interruption is an instant power-off with no shutdown sequence. It lost power at 02:30 UTC on the 17th and came back at 06:40 UTC, and the journal for that boot simply stops mid-operation. Cron has no concept of a missed run, so on that class of failure a brief is lost permanently. `Persistent=true` delivers it on next boot instead. One mechanism fixes the timezone and the power-loss gap together, which is why this is a replacement rather than a corrected crontab line.

Fixing the schedule also surfaced a second, independent bug that the wrong schedule had been hiding: `daily_brief.py` called `polish_all`, which was never defined, so the job would have crashed at any hour. It is now implemented as a thread pool over `polish_with_claude` with per-message fallback to the structured text, matching what CLAUDE.md already described, and covered by three tests.

**Alternatives considered:** Changing the crontab to `0 0 * * *` UTC with a comment — correct on the timezone and one line to change, but it keeps the crontab in a timezone Aki does not think in, which is the exact trap that produced this bug, and it still cannot recover a run missed to power loss. Wake-on-LAN so the box restarts itself — a dead end here: `enp2s0` has no carrier, the machine is on wifi (`wlp3s0`), and WoWLAN from a full power-off does not work in practice. `rtcwake` to schedule a power-on — the alarm has to be armed before shutdown, and a hard mains cut skips any shutdown hook, so it fails precisely in the case that matters. A system-level unit instead of a user unit — would need the secrets in `~/.config/achios/` and the npm-global `claude` reached across users for no gain; linger is already enabled, so the user timer runs with Aki logged out.

**Owner:** Aki.

**Still needs Aki at the keyboard:** the real fix for unattended power loss is in the BIOS, not Linux. On next reboot, enter setup (F10 on HP, BIOS F.31) and set AC power recovery / "after power loss" to **Power On**, so the box comes back by itself when mains returns. Logged in `tasks.md`.

## 2026-08-17 — units live in the repo; achibuntu's firmware cannot auto-power-on

**Decision:** The systemd units are version-controlled in `systemd/` and installed by `scripts/install_units.sh`, which substitutes `@REPO@` for the repo root and leaves `%h` for systemd to expand. `~/.config/systemd/user/` holds generated copies that are never hand-edited. Separately: the plan to fix unattended power loss in the BIOS is abandoned, and the fix is a battery or a small UPS instead.

**Why:** The units encoded `/home/achibukz` five times and existed only on one box, so nothing in git described how the brief was scheduled — a rebuilt server would have lost it silently. `%h` costs nothing and removes the home-directory hardcoding; `@REPO@` needs the installer because the repo root is not derivable from `%h`. Verified by tearing the hand-written units down completely and reinstalling from the script, then reading back `ExecStart` to confirm the specifiers expanded rather than being taken literally — `StandardOutput=append:%h/…` was the doubtful one and it does expand.

The BIOS reversal is the more important correction. The previous entry recommended setting AC power recovery in firmware; the evidence says that setting does not exist on this machine. It is an Insyde consumer BIOS (F.31, 2020) on a generic `HP Notebook`, SKU `T5R50PA#UUF`, chassis type 10. The `hp-bioscfg` driver is loaded and exposes exactly two attributes, `Sure_Start` and `pending_reboot`, where HP business hardware exposes dozens, and the firmware's WMI metadata contains no string matching AC recovery, auto-power-on or RTC wake. `/proc/acpi/wakeup` has no `RTC` entry either. Restore-on-AC-loss is a desktop and workstation feature: laptop firmware assumes a battery buffers power loss, so it is not offered. Ubuntu is irrelevant to the question — the setting is applied before any bootloader — but the option is not there to set.

Also established that the box did not recover by itself on the 17th. It booted at 06:40:33 UTC and took a local TTY login at 06:42:55, class `user`, not SSH, so Aki was physically present and pressed the power button. There is no evidence of any automatic recovery path to build on.

**Alternatives considered:** Leaving the units only on the box — how it worked until now, and the reason the schedule was undocumented. Hardcoding `/home/achibukz` in the committed unit — works today, but the same class of mistake was just cleaned out of the ported skills. Deriving the repo root from `%h/Code/GitHub/AIS-OS` and dropping the installer — fewer moving parts, but it silently breaks if the repo is ever cloned elsewhere, and the installer is nine lines. A system-level unit — needs the `~/.config/achios/` secrets and the npm-global `claude` reached across users for no benefit. Flashing modified firmware to add the missing setting — not worth the brick risk on the machine that runs his scheduled work. `rtcwake` — already rejected in the previous entry and the missing `RTC` wakeup entry now confirms it.

**Owner:** Aki.

**Operational note:** verifying the log-append path required a real run, so Aki received two identical briefs on the 17th. Any future unit change that needs end-to-end proof should be checked against `Result=success` and the log line count rather than by sending again, unless he is warned first.

## 2026-08-17 — cloud routines notify by push, not Telegram

**Decision:** Scheduled *cloud* routines (claude.ai, `RemoteTrigger`) reach Aki's phone through the built-in push channel — `notifications.channel.push: true` — and he reads the result in the linked claude.ai session. They do not send Telegram. Telegram remains the delivery path for jobs on `achibuntu` only. Push is now enabled on all four existing routines.

**Why:** Aki asked whether cloud routines could send to Telegram. They cannot, and the reasons are structural rather than missing configuration. The routine notification channel offers exactly `email`, `push` and `slack`. Cloud routines run in an isolated sandbox with no access to local files or environment, so `~/.config/achios/telegram.env` and the Google OAuth tokens are unreachable by design. There is no secrets field anywhere in the routine API, which leaves inlining the bot token in the prompt — and prompts are stored in the routine config and replayed by `get_run_log`, so that is a deliberate credential leak, made worse by the fact that this token already leaked into a transcript once.

The decisive finding came from firing a routine to test push: the sandbox sits behind a **network egress proxy with a domain allowlist**, which returned `EGRESS_BLOCKED` for both `coinmarketcap.com` and `finance.yahoo.com`. Arbitrary outbound HTTP does not work, so `api.telegram.org` would fail regardless of how the token were supplied. That closes the question rather than leaving it as an untested risk. Aki explicitly rejected the split pattern (cloud commits, local box sends), so push is the whole answer.

Two smaller notes worth keeping. `notifications` is absent from the documented update fields but the server does accept and persist it, verified against `updated_at`. And cloud cron is UTC-only with a one-hour minimum interval — no named timezones, so it carries the same trap that cost the daily brief its first firing; 08:00 Manila is `0 0 * * *` there too.

**Alternatives considered:** A Telegram MCP connector — none is connected, and it would add a third-party dependency for something push already does. Inlining the token in the prompt — rejected on leak grounds before egress ruled it out anyway. The split pattern — rejected by Aki. Email or Slack channels — available, but push is what actually reaches a phone he is holding.

**Owner:** Aki.

**Unrelated defect found while testing:** the "Review the price of Bitcoin" routine fabricates its citations. Both `WebFetch` calls were egress-blocked, yet it reported precise figures and a "Sources: CoinMarketCap, Yahoo Finance, Coinbase" list for pages it never read. It has run daily since May, so its history is unreliable. Any routine that reports figures needs its prompt to forbid citing unfetched sources.

## 2026-08-17 — sync-repos fast-forwards only, never merges

**Decision:** `scripts/sync-repos.sh` (on PATH as `sync-repos`) fetches every repo under `~/Code/GitHub`, `~/Documents/Obsidian` and `~/.hermes`, then fast-forwards only. Divergence, tracked-file changes, and fetch failures are reported and the repo is left untouched. Untracked files do not block a pull.

**Why:** This runs unattended at the start of a session across repos Aki edits on two machines, so any operation that can rewrite or discard work is off the table — no merge, no rebase, no stash, no push. A fast-forward is the one operation that cannot lose a commit. Untracked files are exempt because a fast-forward leaves them alone and aborts by itself if an incoming file would clobber one, and blocking on them meant a repo with one scratch file never updated. Exit code 1 on failure so it composes into a longer startup script. Would revisit if he ever wants it to push too, but that needs a different safety argument.

**Alternatives considered:** `git pull --rebase` everywhere (rewrites local commits unattended — the same reason `achimem_capture.py` aborts a conflicting rebase rather than resolving it); auto-stash before pulling (silently hides work he was mid-way through); a hardcoded repo list (a new clone would be silently skipped); including `~/.claude` as a root (skills dir has no remote, and plugin marketplaces are `/plugin`'s job).

**Owner:** Aki.

## 2026-08-17 — one Telegram bot per vault, not one bot for both

**Decision:** schoolMem gets its own Telegram bot (`@schoMemBot`) and its own always-listening Claude Code session, separate from the achiOS bot. The plugin's `TELEGRAM_STATE_DIR` env var gives each instance its own token, allowlist and pairing state — achiOS on the default `~/.claude/channels/telegram`, schoolMem on `~/.claude/channels/telegram-schoolmem`. Each session is launched from its own repo so that repo's `CLAUDE.md` loads. Paired and confirmed working the same day.

**Why:** The two vaults have different agents. schoolMem's `CLAUDE.md` makes the session a wiki agent bound to the raw→wiki provenance rules; achiOS's makes it Aki's operator. A single bot would have to hold both instruction sets at once and route by guesswork, and whichever repo it was launched from would win — silently applying the wrong rules to the other vault's content. Two bots means the routing decision is made by which chat he opens, which is unambiguous and needs no logic. The cost is a second always-on process and a second entry in every access list, which is the cheaper half of the trade.

**Alternatives considered:** One bot switching context by keyword or command prefix (routing is a guess, and a misroute writes to the wrong vault under the wrong rules); one bot with both `CLAUDE.md` files loaded (doubles context on every message and leaves the provenance gate ambiguous); running schoolMem through the existing achiOS bot and having achiOS shell into the vault (loses the vault's own agent instructions entirely).

**Owner:** Aki.

## 2026-08-17 — the schoolMem bot is write-blocked from wiki/ by a hook, not by instruction

**Decision:** The schoolMem Telegram bot runs unattended as a systemd user unit inside its own tmux server, on `sonnet`, with `--permission-mode bypassPermissions`, restarting daily at 04:00 Manila. It fast-forwards the vault before each start. It may read `wiki/` freely and may never write to it: `scripts/schoolmem_wiki_guard.py` is a PreToolUse hook that denies `Write`/`Edit`/`MultiEdit`/`NotebookEdit` by resolved path and the obvious mutating `Bash` shapes. Captures land in a new tracked `schoolMem/inbox/` for promotion by a real INGEST later.

**Why:** Aki asked for bypass permissions and, in the same breath, that the bot never write to the wiki. Those are contradictory if the wiki ban is only a line in `CLAUDE.md` — bypass removes the gate, and what remains is the model choosing to obey an instruction, unattended, indefinitely. schoolMem's whole value is that a wiki page is trustworthy because a human was present when it was written, so that gate has to be mechanical. A PreToolUse hook is the mechanism, and it was verified rather than assumed: a real `claude -p --permission-mode bypassPermissions` run was told to write into `wiki/`, the hook denied it, and no file appeared. Permission mode and hooks are independent layers, which is the finding the design rests on.

The wrapper arms the guard on every start and **exits rather than launching** if it cannot, because a bot that comes up unguarded with bypass permissions is worse than no bot. A failed `sync-repos` only warns — a stale vault gives poorer answers, but no bot at all is worse, and sync failures are usually transient network.

tmux is a requirement, not a preference: `claude` detects the absent TTY under systemd and falls back to `--print`, which was confirmed by running it that way and watching it demand a prompt argument. The unit uses `tmux -L schoolmem` so it owns its own server and stopping the unit cannot take down an interactive tmux.

`inbox/` is new and tracked on purpose. The vault's designed inbox is `raw/`, but `raw/` and `output/` are both gitignored and `raw/` does not exist on achibuntu at all, so a note captured from his phone would have been stranded on the server and never appeared in Obsidian on the Mac — which defeats the point of capturing from a phone.

**Alternatives considered:** Trusting `CLAUDE.md` to hold the line under bypass (not a guarantee, just a hope); a narrower permission mode like `acceptEdits` (Aki chose bypass, and it would still not protect `wiki/` specifically while adding prompts nobody is there to answer); `chmod -R a-w wiki/` (blocks the owner as intended, but also blocks `git` fast-forwards that touch wiki files, breaking the daily sync); running the bot as a separate unix user with read-only `wiki/` (the genuinely airtight answer, and the one to reach for if the Bash heuristic ever proves insufficient — deferred as disproportionate today); `RuntimeMaxSec` + `Restart=always` instead of a restart timer (does not compose with the oneshot+tmux shape).

**Known limit:** Bash under bypass is narrowed, not closed. The guard catches redirects, `rm`/`mv`/`cp`/`tee`/`sed -i`/`dd` and destructive `git` subcommands aimed at `wiki/`. A determined or unlucky shell construction can still get through. Stated plainly here so the guarantee is not overclaimed.

**Owner:** Aki.

## 2026-08-17 — the achiOS bot writes; one wrapper drives both

**Decision:** achiOS gets its own always-on Telegram session too — `achios-bot`, `tmux -L achios`, cwd this repo, `sonnet`, `bypassPermissions`, restarting daily at 04:10 Manila. Unlike schoolMem it carries **no write guard**: editing `tasks.md`, adding calendar events, appending to `decisions/log.md` and committing are the job. Both bots now run one script, `scripts/telegram-bot.sh`, configured per-unit through `BOT_NAME` / `BOT_CWD` / `BOT_STATE_DIR` / `BOT_GUARD` / `BOT_MODEL`. `scripts/schoolmem-bot.sh` is deleted.

**Why:** The second bot made the per-bot script a template rather than a one-off, and the two differ only in configuration — same sync, same tmux shape, same launch flags. Two near-identical scripts would have drifted, and the half that matters most is the fail-closed guard install, which must not exist in two versions. The guard is now optional rather than assumed, which is what let the achiOS bot reuse the same path without pretending to be guarded.

Restart times are staggered ten minutes apart on purpose: both fetch before launching, and the box has one uplink.

**Known and accepted:** the achiOS bot's blast radius is genuinely wider. Push to `origin` is pre-authorised on achibuntu, so a Telegram message can reach GitHub with no human at a keyboard. Aki asked for read and write knowingly. The one place this rubs against an existing guarantee is the logging contract, which says unattended writes may never reach `achiMem/wiki/` — that rule is now documented-but-unenforced for this bot. The plumbing to fix it is already there: point `BOT_GUARD` at a guard for that path. Deliberately not done today, because he asked for an unrestricted achiOS bot and the contradiction is worth stating rather than silently resolving against his instruction.

**Alternatives considered:** A second standalone script (drifts, and duplicates the fail-closed guard logic); one bot serving both repos (settled the other way in the entry above, and writes make a misroute worse, not better); guarding the achiOS bot's `achiMem/wiki/` writes anyway (would have quietly overridden an explicit instruction — raised instead); a shared library sourced by two thin scripts (more moving parts than env vars, for two callers).

**Owner:** Aki.

**Renamed same day:** "operator" was dropped for "achiOS" across the unit, tmux socket, `BOT_NAME` and log — `achios-bot.service`, `tmux -L achios`, `achios_bot.log`. Aki names things for himself and types the socket name; `operator` was a word only this file used. The old unit was disabled and its symlinks removed rather than left shadowing the new one.

## 2026-08-17 — no bot token in the plugin's default channel dir

**Decision:** The achiOS bot's Telegram state moves from `~/.claude/channels/telegram/` to `~/.claude/channels/telegram-achios/`, set through `BOT_STATE_DIR` in its unit. The default path must stay empty. A regression test in `tests/test_telegram_bot.py` asserts no unit's `BOT_STATE_DIR` ends in `/channels/telegram`.

**Why:** Aki messaged the bot and nothing arrived. The bot was healthy — unit active, tmux alive, pane at the prompt, his id in `allowFrom` — and Telegram reported `pending_update_count: 0`, meaning the message had been fetched and acked by *something*. That something was an ordinary terminal session in this repo.

The telegram plugin is enabled globally in `~/.claude/settings.json`, so every Claude Code session anywhere on the box spawns its `server.ts`. With no `TELEGRAM_STATE_DIR` in the environment that server resolves to `~/.claude/channels/telegram/`, loads whatever token it finds there, reads `bot.pid`, SIGTERMs the holder if it looks like a `server.ts`, and starts polling. That stale-holder kill exists for a good reason — an orphaned poller otherwise holds the token's single `getUpdates` slot forever — but it cannot tell a zombie from the live bot.

The failure is silent in both directions. The hijacking session logs `Channel notifications skipped: server plugin:telegram:telegram not in --channels list for this session` and injects nothing, so the message vanishes. The bot session sees no error at all; it simply stops receiving. Nothing surfaces on Aki's phone either — the message sends normally and is never answered. The MCP log under `~/.cache/claude-cli-nodejs/<cwd-slug>/mcp-logs-plugin-telegram-telegram/` is the only place the takeover is visible, and only by comparing `Channel notifications registered` against `skipped` across two sessions.

A named state dir is reachable only when `TELEGRAM_STATE_DIR` is set, and only the two units set it. With the default dir empty, an ordinary session's server exits at the missing-token check, which happens before it reads or writes `bot.pid` — so it cannot touch either bot. schoolMem was never vulnerable; it has been on a named dir since it was built, which is why only achiOS went deaf.

**Known and accepted:** every ordinary session on this box now shows the telegram MCP server as failed to connect, because there is no token at the default path. That noise is the price of the isolation and is cheaper than a bot that stops answering without saying so.

**Alternatives considered:** Disabling the telegram plugin globally (the bot needs it enabled to accept `--channels`); scoping the plugin per project (the bot and Aki's terminal share the same cwd, so project settings cannot separate them); leaving the token in place and restarting the bot after each session (treats the symptom, and the next session steals it back); a wrapper that re-claims the token on a timer (two processes fighting over one `getUpdates` slot, which is the bug rather than a fix).

**Residual risk:** nothing prevents a future `/telegram:configure` run from writing a token back into the default dir. If that happens the symptom returns exactly as before — silence, no error.

**Owner:** Aki.

---

## 2026-08-18 — Systemd OnFailure crash alerts and multi-ETF digest

**Decision:**
1. Attached `OnFailure=achios-failure-alert@%n.service` across all systemd user units (`achios-bot`, `achios-schoolmem-bot`, `achi-agy`, `achios-daily-brief`, `achios-voo-digest`), invoking `scripts/service_failure_alert.py`.
2. Added exit code traps in `scripts/telegram-bot.sh` and `achiAgy/scripts/run-bot.sh` so process crashes inside tmux trigger Telegram alerts to `achinouncements`.
3. Created multi-ETF digest (`scripts/voo_digest.py`) tracking VOO, VXUS, and QQQM, scheduled twice daily at 04:30 (US market close) and 08:00 (morning brief) Asia/Manila.

**Why:** A crashed bot or failed cron previously produced only silence. The `OnFailure` template unit guarantees immediate, automated notification with recent journal/file logs dispatched to `achinouncements` whenever any service aborts. Sensitive bot tokens and API keys are dynamically redacted with regex filters before reaching Telegram.

**Alternatives considered:** Polling daemon for process status (wasteful CPU cycles; systemd's native `OnFailure` handles event-driven triggers instantly).

**Owner:** Aki.

## 2026-08-18 — Telegram Notification Token Precedence & Routing Isolation

**Decision:** `telegram_notify.load_config()` must strictly prioritize credentials defined in `~/.config/achios/telegram.env` (`@achiOSBot`) over ambient process environment variables (`os.environ["TELEGRAM_BOT_TOKEN"]`).

**Why:** When scheduled scripts (e.g. `evening_debrief.py`, `voo_digest.py`) or manual tests are executed interactively by an AI agent running inside a pair-programming bot daemon (such as `achiAgy` on `@achiAgyOSBot` or Claude on `@achiOSClaudeBot`), the parent daemon exports its own `TELEGRAM_BOT_TOKEN` into the subshell environment. If environment variables take precedence, system briefings and failure alerts get hijacked and delivered into the active pair-programming chat rather than to the dedicated `@achiOSBot` (`achinoucements`) chat. Prioritizing `telegram.env` enforces strict routing isolation.

**Alternatives considered:** Unsetting `TELEGRAM_BOT_TOKEN` in every subshell before running scripts (fragile and easily forgotten in new scripts; fixing it at the common `telegram_notify.py` entrypoint protects all callers permanently).

**Owner:** Aki.

## 2026-08-19 — Dedicated Finance Bot & Multi-Bot Notification Support

**Decision:** Extended `telegram_notify.py` to support custom credential environment files via `env_path: Path | str | None = None`. Updated `voo_digest.py` to route ETF market digests (VOO, VXUS, QQQM) to a dedicated finance bot configured at `~/.config/achios/telegram_finance.env`, while falling back gracefully to `telegram.env` if the custom file is absent.

**Why:** Aki separated financial and market notifications from general system announcements (`@achiOSBot`). Adding optional `env_path` parameter support across `read_env()`, `load_config()`, and `send()` enables multi-bot dispatch without duplicating Telegram API sending logic or splitting message routines.

**Domain:** `infra`
**Owner:** Aki.

## 2026-08-19 — School Announcements Bot (@achiSchoNounceBot) Separation

**Decision:** Configured `scripts/email_digest.py` to route DLSU school email debriefs to `@achiSchoNounceBot` using credentials from `~/.config/achios/telegram_school.env`, preserving `@schoMemBot` purely for two-way interactive schoolMem querying.

**Why:** Separating school announcements into a dedicated one-way bot keeps `@schoMemBot`'s interactive session clean and isolates academic notifications from personal/work briefings.

**Domain:** `school`
**Owner:** Aki.

## 2026-08-19 — Bash Interpolation Safeguard & Live Market Data Verification

**Decision:** Scripts and CLI commands dispatching currency and financial cards to Telegram must never pass raw dollar signs (`$710`, `$-0.38`) inside double-quoted bash strings, as bash parameter interpolation expands them to empty strings or option flags (`$-` -> `hBc`). Scripts must be written to standalone Python files or pass single-quoted literal payloads. Furthermore, market digests must always be generated from live query data with explicit date verification.

**Why:** Prevents formatting corruption and ensures 100% price accuracy across automated and manual Telegram broadcasts.

**Domain:** `infra`
**Owner:** Aki.

## 2026-08-19 — ETF Schedule Optimization (8am/10pm Daily + Sunday 6pm Weekly Recap)

**Decision:** Re-tuned ETF market timing:
1. `voo_digest.py` (`achios-voo-digest.timer`): Fires at **08:00 AM Manila** (Morning Market Close Summary) and **10:00 PM Manila** (Evening Market Opening Pulse, 30m after US market open).
2. `etf_weekly_digest.py` (`achios-etf-weekly-digest.timer`): Dedicated weekly performance recap firing every **Sunday at 18:00 Manila (6:00 PM)**, calculating 5-day net price movements ($ and %), weekly high/low trading ranges, 1-year returns, and overall market trend indicator.

**Why:** Replaced redundant 4:30 AM/8:00 AM duplicate pings with actionable trading cycle milestones (Morning review + Evening open pulse), and provided a specialized high-level portfolio wrap-up during Sunday evening planning.

**Domain:** `finances`
**Owner:** Aki.

## 2026-08-19 — Contextual Email Debrief Synthesis & Noise Filtering

**Decision:** Revamped `scripts/email_digest.py` into a hybrid architecture: aggressive heuristic noise filtering (routine PM/AM HDAs with no emergency/suspension, LinkedIn/Indeed automated job blasts, marketing, and Laguna-only notices) followed by an LLM synthesis pass (`agy -p` in `~/.local/share/achios/llm`) with a deterministic fallback. Messages are formatted with contextual 3-tier headers (`⚡ HIGH PRIORITY & VIP`, `📚 COURSES & ACADEMICS` / `💼 WORK & RECRUITING`, `📬 UPDATES & GENERAL`) and indented 1-line action takeaways. Personal account is scanned for critical security/banking alerts and stays silent when clean.

**Why:** The previous script surfaced raw subjects indiscriminately, falsely tagging routine HDAs, Grammarly, and automated LinkedIn spam as priority while burying high-signal professor recommendation replies, Manila campus class suspensions, and ING internship onboarding details.

**Alternatives considered:** LLM-only pipeline (higher token latency/cost on pure spam), purely deterministic regex keyword matching (misses nuanced action takeaways and contextual synthesis).

**Owner:** Aki.

## 2026-08-19 — /tasks Structured Format Established

**Decision:** When Aki invokes `/tasks` or queries his tasks, always use the 4-tier structured format:
1. 🔥 **Immediate Deadlines** (grouped by timeline/urgency)
2. 🎓 **DLSU Academics & Enrollment**
3. 💼 **Career & Finances Next Steps**
4. 🛠️ **Systems & Engineering (achiOS / Asa / achiAgy)**
Format with interactive checkboxes (`- [ ] **Title:** details`) and links to `tasks.md`.

**Why:** User confirmed preference for clean categorized view with markdown checkboxes over raw parsing or unformatted dumps.

**Domain:** `tasks`
**Owner:** Aki.

## 2026-08-19 — Google One Student Plan Transition Plan (₱275/mo)

**Decision:** Schedule cancellation of current Google One subscription on 2026-10-13 and transition to Google AI Pro Student Plan (₱275/mo, 75% off for up to 4 years via DLSU SheerID verification) on 2026-10-14 when current plan cycle concludes. Added all-day events to `Personal` calendar.

**Why:** Maximizes current paid period while locking in the ₱275/mo student discount before the 2026-12-31 campaign cut-off.

**Domain:** `finances`
**Owner:** Aki.

## 2026-08-19 — AI Model Allocation: Claude Opus for Auditing/Planning vs Gemini 3.7 Flash for Execution

**Decision:** Formally split agent workload roles across model architectures:
1. **Auditing, Code Reviews, & Feature Planning:** Use **Claude Opus** (or Claude 3.5 Sonnet / flagship deep reasoning models) for exhaustive codebase audits, gap analysis, and system architecture planning.
2. **Execution, Tool Runs, & Code Implementation:** Use **Gemini 3.7 Flash** (via Antigravity / `agy`) for rapid implementation, file editing, tool calling, unit test runs, and background tasks.

**Why:** Claude Opus excels at high-level reasoning, identifying edge cases, architectural gaps, and synthesizing complex multi-file plans without hallucinating constraints; Gemini 3.7 Flash provides lightning-fast speed, low latency, and efficient tool calling for implementing code changes and running execution loops.

**Domain:** `architecture`
**Owner:** Aki.

## 2026-08-20 — Voice Register Adjustment

**Decision:** Keep responses concise, humble, candid, and direct; use Taglish for reasoning and English for conclusions; avoid corporate buzzwords.

**Why:** User requested less formal communication style aligned with natural voice profile.

**Domain:** `voice`
**Target Store:** `memory`
**Owner:** Aki.

## 2026-08-20 — Antigravity Stream Error Propagation & Quota Limit Surfacing

**Decision:** Captured `error` from `result` and `error_message` events in `AgyClient` so when a model hits individual quota or rate limits (e.g. Claude Opus 5-hour limit), the Telegram daemon renders a clear error banner with reset countdowns instead of silently completing with an empty message.

**Why:** Prevents silent failures and gives immediate visibility into backend quota exhaustion.

**Domain:** `achiagy`
**Target Store:** `memory`
**Owner:** Aki.

## 2026-08-20 — Antigravity Models & Quota Live Dashboard in /usage

**Decision:** Connected `/usage` command to `https://cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary` and Google OAuth userinfo to display live account email, Gemini Models weekly/5h limits, Claude/GPT Models weekly/5h limits, progress bars, and countdowns formatted as `Xd Xh Xm`.

**Why:** Mirrors the Antigravity CLI `/usage` modal directly inside Telegram for effortless quota monitoring.

**Domain:** `achiagy`
**Target Store:** `memory`
**Owner:** Aki.

## 2026-08-20 — Hermes Dual-Track Self-Learning Engine Deployment & TGDB Audit

**Decision:** Deployed `MemoryEngine` in `src/memory_engine.py` with 2.5k character budgeting, atomic writes, and CRUD mutations for `~/.config/achios/MEMORY.md` and `USER.md`. Connected `/learn` authoring prompt and updated `extract_corrections.py` to route to memory, `.agentrules`, and `decisions/log.md`. Verified TGDB archive and exporter with 29 passing unit tests in `achiAgy` and 61 passing tests in `AIS-OS`.

**Why:** Fulfills the self-learning loop plan while preserving prefix cache safety and eliminating noisy conversational rule pollution.

**Domain:** `architecture`
**Target Store:** `memory`
**Owner:** Aki.

## 2026-08-20 — Shared concerns must cross the AIS-OS / achiAgy repo boundary

**Decision:** The three concerns that keep breaking — sending to Telegram, writing to a
protected path, and persisting state — get one implementation that both repos import,
rather than one per bridge. `telegram_notify.py` already states this rule for sending
("Import it rather than re-implementing the send"); `achiAgy` never inherited it because
it was built as a separate repo. Extending the rule across the repo boundary is the change.

**Why:** The 2026-08-20 audit found the same defect class repeated per component: two
independent Telegram send paths with different chunking and escaping; a `wiki/` guard that
exists for the Claude bot and not the agy one; token accounting fixed for `input_tokens`
and left broken for its two neighbours; `sessions.json` living in two places, one stale.
Each was fixed once and did not propagate. A fifth bridge would reintroduce all of them.

**Alternatives considered:** (a) Merge achiAgy into AIS-OS — rejected, the runtimes and
dependency sets are genuinely different and the split is not the problem. (b) Fix each
site individually — rejected, that is what produced the current state. (c) Leave it,
single-user system — rejected specifically because of P0-3: the vault's anti-hallucination
guarantee is currently false, and "one guard per runtime" is what made it false.

**Owner:** Aki. Sequenced in `tasks.md` after the P0 fixes.

**What would change my mind:** if achiAgy turns out to be short-lived — if the agy bridge
is an experiment Aki expects to retire once Claude Code's own mobile story improves, then
a shared core is premature and the right move is just the path guard.


## 2026-08-20 — Automated memory writes require a model gate, not a regex

**Decision:** No unattended process may write to `MEMORY.md`, `USER.md`, `.agentrules`, or
`decisions/log.md` on the strength of a regex match alone. A model call must classify each
candidate as a durable preference or a one-off before it is persisted, and the harvester's
own output shape is never a valid input to itself.

**Why:** The 2026-08-20 audit found `extract_corrections.py` running every 15 minutes,
re-ingesting the memory that achiAgy injects into each prompt, and writing it back with a
doubled prefix each pass. Three generations reached `MEMORY.md` and 54 of 86 entries in
`decisions/log.md` are now machine noise. The file's own docstring claims an LLM gating
filter; none was ever implemented. A regex cannot tell "I prefer X" from "buy X on Oct 14",
and both are now permanent operating rules.

**Alternatives considered:** (a) Tighten the regexes — rejected, that was tried on 08-19 and
the loop re-formed within a day; the failure is structural, not a pattern-quality problem.
(b) Drop the harvester and rely on `/learn` alone, which is what Hermes does — genuinely
tempting and still the fallback if the gate proves unreliable, but it gives up passive
capture entirely. (c) Keep regex as a *candidate generator* and gate on a cheap batched
Haiku call — chosen, because it keeps passive capture while putting judgment in the loop.

**Owner:** Aki. Sequenced in `tasks.md`: cut the recursion first, then clean, then gate.

**What would change my mind:** if the gate's false-positive rate stays high after a week of
dry runs, delete the harvester and keep `/learn` only. Hermes ships without one for a reason.

## 2026-08-21 — Two writers reach declarative memory, only one is audited

**Decision:** Recorded as an open finding, not yet resolved. Flagged during the Task 8
live test of self-learning loop v2.

**What happened:** The live test passed, but `MEMORY.md` gained an entry the loop never
wrote. Bot log shows the agy model called `memory_engine.py add --target memory` itself
at 18:03:46, 105 seconds before the turn-10 review fired and wrote its own version to
`USER.md`. Same preference, two files, two phrasings.

**Why it matters:** `build_frozen_system_prompt()` exposes a `manage_memory` tool
(`achiAgy/src/bot.py:164-167`), so the model can write to memory at will. That path has
no ledger record, no gate classification, no rate cap, and no provenance guard — it
bypasses every control v2 was built to provide. It also makes the 2026-08-27 audit's
precision and recall figures wrong, because the ledger cannot see those writes.

**Alternatives:**
- Remove `manage_memory` from the system prompt. Single writer, fully auditable, but
  `/learn` depends on it and "remember this" would no longer take effect immediately.
- Instruct the model not to write unprompted. Unenforced, and the audit stays blind.
- Record every write in the ledger inside the `memory_engine.py` CLI entrypoint, so any
  writer is logged regardless of origin. Preferred: keeps both paths working and makes
  the audit honest.

**Owner:** Aki to choose before the 2026-08-27 audit, since the audit's numbers depend on it.

## 2026-08-21 — CLAUDE.md and AGENTS.md resynced to the built system

**Decision:** Both instruction files now document the v2 self-learning loop, achiAgy, the
one-way notification bots, and the telegram_notify retry/redaction contract, plus a Future
work section pointing at `docs/ROADMAP.md`.

**Why:** AGENTS.md still described `extract_corrections.py` as live infrastructure a day
after it was deleted, and CLAUDE.md had never mentioned achiAgy at all — an always-on bot
with write access to this repo and pre-authorised push. An agent reading either file would
have been working from a false map.

The self-learning section deliberately explains *why v1 died* rather than only what v2 does.
The failure mode was subtle and architectural, and an agent that does not understand it could
reintroduce it in one refactor by collapsing `prompt` and `full_prompt`.

**Alternatives:** Keeping one file and symlinking the other was rejected — the Agent
Separation Rule exists because agy maintains AGENTS.md and must not touch CLAUDE.md, and a
symlink erases that boundary. Trimming both to a short index was rejected too: the
non-obvious operational facts here are the whole value, and they are not recoverable from
the code.

**Owner:** Aki. Revisit after the 2026-08-27 audit, when the second-writer question resolves.

## 2026-08-26 — /tasks dynamic semantic grouping and clean unicode format

**Decision:** Formatted `/tasks` queries with dynamic domain category headers synthesized by LLM from active tasks, using `• ☐` checkboxes, sorted by due date then priority (`!high` > `!med` > `!low`), with raw hashtags stripped for a clean, concise view, showing active tasks only. Persisted in `~/.config/achios/USER.md`.

**Why:** Reduces text-heavy output and repetitive hashtags across task queries while grouping related items into clear contextual buckets.

**Alternatives considered:** Flat raw markdown list under `### Active` (too verbose with duplicate tags), hardcoded static categories (rigid when new tag areas emerge).

**Owner:** Aki.

## 2026-08-26 — DLSU AY2627-T1 Academic Calendar Adjustment

**Decision:** Updated DLSU Google Calendar and course schedules per Provost Roleda memo: Term 1 start shifted from Sep 3 to Sep 7, 2026; Enlistment extended to Sep 6; ILW confirmed as Oct 29 – Nov 4; Grade Consultation Day set to Dec 15; recurring Friday/Saturday course sessions adjusted to first meeting dates (Sep 11 / Sep 12).

**Why:** Grounds calendar and class reminders in the official DLSU Provost adjustment memo and eliminates phantom early course reminders ahead of the true term start.

**Alternatives considered:** Manual individual date edits without recurring series shift (leaves orphan class reminders on Sep 4/5).

**Owner:** Aki.

## 2026-08-27 — achiAgy workspace pointed to ~/Code/GitHub

**Decision:** Configured `achiAgy` daemon and `achi-agy.service` to pass `github` as the target argument, establishing `BOT_CWD=/home/achibukz/Code/GitHub` instead of `AIS-OS`.

**Why:** Running both `@achiAgyOSBot` and `@achiOSHubBot` in `~/Code/GitHub/AIS-OS` resulted in workspace collisions and duplicate bot handlers. Repointing `achiAgy` to `~/Code/GitHub` cleanly decouples the pair: `@achiOSHubBot` (and `@achiOSClaudeBot`) manages `AIS-OS`, while `@achiAgyOSBot` provides cross-repo development, inspection, and tooling across all repositories under `~/Code/GitHub`.

**Alternatives considered:** Permanently disabling `achi-agy.service` (loses the Antigravity Telegram pair for general code tasks), scoping strictly to `achiAgy` repo (too limited for cross-project work).

**Owner:** Aki.

## 2026-08-27 — achiAgy Multi-Subsystem Audit & Hub Refactor Baseline

**Decision:** Conducted an end-to-end 3-lens audit across `achiAgy` (Core Engine, TGDB, and Self-Learning Loop) and documented architectural findings, failure modes, and refactor requirements in `docs/telegram-supergroup-hub-plan.md`.

**Why:** Preparing to migrate interactive bot pairs to a unified Telegram Supergroup with Forum Topics required auditing live subsystem health. The audit uncovered critical pre-refactor bugs: TGDB dual-writer truncations, system prompt leak in note titles, 99% memory store saturation with `entries[0]` eviction risks, and `chat_id` keying collisions across forum threads.

**Alternatives considered:** Direct refactoring without holistic audit (would have inherited hidden TGDB overwrites and memory eviction bugs into the Supergroup Hub).

**Owner:** Aki.

## 2026-08-27 — Mandatory Clickable Linking & 1-Tap Mobile Viewer Enforcement

**Decision:** Enforced strict clickable linking protocols across [AGENTS.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/AGENTS.md), [.agentrules](http://100.106.210.38:8999/Code/GitHub/AIS-OS/.agentrules), and CLAUDE.md: all `.md` files must include 1-tap mobile viewer links (`http://100.106.210.38:8999/...`), and bare unlinked paths are strictly banned. Created `scripts/verify_links.py` to validate compliance.

**Why:** Mobile-first operating UX on Telegram and Obsidian requires zero friction: tapping a file or plan must immediately open the target file or rendered mobile viewer without manual path copying or searching.

**Alternatives considered:** Soft guideline without automated validator script (drifted in previous turns).

**Owner:** Aki.

## 2026-08-27 — Tailscale Markdown (.md) Web Viewer Linking Protocol (/grill-me Finalized)

**Decision:** Formatted all Markdown (`.md`) file links strictly as clickable Tailscale web viewer links (`http://100.106.210.38:8999/<full_path_from_home>`). Banned `file:///` URLs entirely. All non-MD files (`.py`, `.sh`, `.json`, `.toml`) and code symbols remain standard plain/backticked text without links. Locked in `MEMORY.md`, `.agentrules`, `AGENTS.md`, and `CLAUDE.md`, validated via `scripts/verify_links.py` and `.githooks/pre-commit`.

**Why:** Aki reads notes and plans primarily on mobile Telegram over Tailscale. Pointing `.md` links directly to `http://100.106.210.38:8999/...` renders fully styled Markdown, mermaid diagrams, and syntax highlighting in 1 tap without IDE file prompt dialogues or broken local desktop URLs.

**Alternatives considered:** Dual links (`file:///` + web viewer — rejected as cluttered), short fallback paths (rejected to avoid cross-repo filename collisions).

**Owner:** Aki.

## 2026-08-27 — achi-viewer Concurrency & Content-Length Fix

**Decision:** Upgraded `scripts/achi_viewer.py` from single-threaded `HTTPServer` to `ThreadingHTTPServer`, added explicit `Content-Length` headers across all responses, enabled `HTTP/1.1` and `do_HEAD` support, and wrapped socket writes to catch client disconnects gracefully.

**Why:** Single-threaded execution caused socket blocking and request hanging whenever mobile browsers opened persistent keep-alive connections or parallel asset requests. Missing `Content-Length` headers left clients waiting indefinitely on socket closure.

**Alternatives considered:** Running under gunicorn/uvicorn (unnecessary dependency overhead when stdlib `ThreadingHTTPServer` handles concurrent mobile requests perfectly).

**Owner:** Aki.

## 2026-08-27 — achi-viewer Mermaid Diagram Rendering Engine Fix

**Decision:** Upgraded `scripts/achi_viewer.py` Markdown parsing engine from deprecated `marked.setOptions({ highlight })` to `marked.use({ renderer: { code(token) } })`, capturing `mermaid` code fences directly into `<pre class="mermaid">${code}</pre>`, added dedicated `.mermaid` responsive dark container styling, and configured `mermaid.run()` on DOM mount.

**Why:** Modern Marked.js (v5+) ignores legacy `highlight` option hooks in `setOptions`, preventing code blocks tagged with ````mermaid` from generating `.mermaid` elements. Without `.mermaid` nodes, Mermaid.js never hydrated the raw text into visual vector flowcharts.

**Alternatives considered:** Client-side regex substitution (brittle on nested code blocks), server-side SVG pre-rendering (requires headless Chromium/puppeteer dependency on Achibuntu).

**Owner:** Aki.

## 2026-08-27 — achi-viewer Interactive Diagram Zoom, Pan & Fullscreen Modal

**Decision:** Integrated `@panzoom/panzoom` into `scripts/achi_viewer.py`, added an interactive floating toolbar (`➕ In`, `➖ Out`, `🔄 Reset`, `⛶ Fullscreen`) to every Mermaid diagram card, enabled pinch-to-zoom and drag-to-pan, removed aggressive SVG downscaling constraints (`maxWidth: none`), and added a high-magnification fullscreen lightbox overlay.

**Why:** Large, complex architectural diagrams (such as multi-subgraph Telegram Supergroup routing) scale down to fit container width, rendering labels unreadably small on mobile and narrow desktop views. Interactive pan/zoom and fullscreen inspection allow 1-tap magnification up to 10x with zero vector degradation.

**Alternatives considered:** Static CSS horizontal scrolling without zoom controls (cumbersome on mobile touchscreens), opening SVG in separate browser tab (breaks in-app reading workflow).

**Owner:** Aki.

## 2026-08-27 — achi-viewer Native PointerEvents Drag & In-Place Fullscreen Mode

**Decision:** Replaced external Panzoom library with a native PointerEvents engine using `setPointerCapture` on `.mermaid-viewport`, enabled multi-touch pinch-to-zoom and mouse wheel scaling, added live zoom percentage indicators, and converted fullscreen mode to an in-place CSS overlay (`.fullscreen-mode`).

**Why:** External Panzoom caused dragging deadzones on SVGs and its containment rules blocked panning. Cloning Mermaid SVGs into a modal duplicated element IDs, breaking arrowheads and marker definitions. In-place CSS fullscreen expansion preserves the original SVG DOM, guaranteeing zero ID collisions and 100% responsive gesture tracking.

**Alternatives considered:** Fixing external Panzoom configuration (still suffered from SVG transparent click deadzones), iframe isolation (unnecessary overhead).

**Owner:** Aki.

## 2026-08-27 — achi-viewer Native ViewBox Coordinate Scale Calibration

**Decision:** Calibrated `scripts/achi_viewer.py` to extract the native coordinate dimensions from each Mermaid SVG (`viewBox.baseVal.width`) upon render and set `svg.style.width = nativeWidth + 'px'`, making `100%` scale represent the true 1:1 readable baseline.

**Why:** Without an explicit CSS width, the browser defaulted wide Mermaid SVGs (1391px viewBox) to narrow container widths (~350px-500px), causing the 14px node text to shrink to ~3-5px micro-text at `100%`. Binding the SVG pixel width to its native viewBox width ensures that `100%` is immediately rendered at the true, crisp, comfortable reading scale (matching the 244% zoomed appearance).

**Alternatives considered:** Manual zoom multipliers on load (clunky percentage badges).

**Owner:** Aki.

## 2026-08-27 — achi-viewer 100% Standard Scale Baseline

**Decision:** Reverted initial and reset zoom scale in `scripts/achi_viewer.py` to `1.0` (`100%`), keeping diagrams framed cleanly within the viewport upon initial load and reset.

**Why:** Hardcoding a 244% zoom on reset caused excessive magnification where only 1-2 nodes filled the entire card viewport. A clean 100% baseline allows users to see the diagram structure immediately and zoom in step-by-step (`➕ In` / pinch) when desired.

**Alternatives considered:** Fixed 244% scale (too zoomed in).

**Owner:** Aki.

## 2026-08-27 — /tasks Structured Layout & Semantic Categorization Lock

**Decision:** Standardized and locked the `/tasks` query output specification across `AGENTS.md`, `.agentrules`, and `USER.md` into 4 strict semantic categories: (1) 🔥 **Immediate Deadlines & Today**, (2) 🎓 **DLSU Academics & schoolMem**, (3) 💼 **Career, ING Onboarding & Personal Finances**, and (4) 🛠️ **Systems & Engineering (achiOS / Asa / achiMem)**.

**Why:** Consistent, scannable, and clean visual grouping with `• ☐ **Title:** details (!priority, @date)`, section dividers (`---`), stripped hashtags, and clickable Tailscale web viewer links (`http://100.106.210.38:8999/...`) provides maximum clarity across mobile Telegram and desktop pair-programming sessions.

**Alternatives considered:** Flat chronological lists, standard unformatted markdown checkboxes without section grouping.

**Owner:** Aki.

## 2026-08-28 — Binary documents leave the vaults for ~/Documents/Files, but raw/ stays in Git

**Decision:** Built the centralized store at `~/Documents/Files/` with the planned taxonomy and a
dedicated Syncthing folder `achi-files` shared between achibuntu and AchiBook Air. Migrated the five
binary documents out of `achiMem/raw/` and rewrote every `sources:` frontmatter entry and viewer link
that pointed at them. Then **departed from the plan's Step 5**: instead of removing `raw/` from Git and
gitignoring the whole directory, achiMem now gitignores binary extensions under `raw/` and keeps the
markdown tracked.

**Why:** `achiMem/raw/` had 89 tracked files and only 6 were binaries, together about 6.4 MB. The other
83 are research notes, transcripts, and the session stubs in `raw/sessions/` that `achimem_recall.py`
reads back. Worse, every wiki page's `sources:` frontmatter cites a `raw/...` path, so that directory is
the vault's provenance layer. Untracking it wholesale would trade the anti-hallucination guarantee and
all GitHub history for those notes against a 6.4 MB bloat problem. Extension globs solve the bloat and
cost nothing. schoolMem needed no change at all: its `raw/` has been gitignored and untracked since
before this plan was written.

**Also corrected:** the plan said to hand-edit `~/.local/state/syncthing/config.xml` and restart.
Syncthing rewrites that file from memory on shutdown, so the edit would have been silently discarded.
Used the REST API on `127.0.0.1:8384` instead. And Step 5 of the plan (teach `MediaDispatcher` about
`Documents/Files/`) was already satisfied: the dispatcher resolves any path under `$HOME` generically,
verified classifying the new jpg as `photo` and the new pdf as `document`.

**Alternatives considered:** Git LFS for the binaries (rejected earlier, GitHub quota); untracking all
of `raw/` per the plan (rejected, breaks provenance); migrating `schoolMem/raw/` too (rejected, those
183 MB are ingest-pipeline input, not documents, and are already outside Git).

**Owner:** Aki.

## 2026-08-28 — Grill outcomes for the document store: viewer blocking, Files/raw boundary, term-based academic tree

**Decision:** Settled ten open questions on the centralized store through a `/grill-me` session and
implemented all of them.

- **`personal/legal` and `personal/finance` are off the web.** Added both to `BLOCKED_PATTERNS` in
  `scripts/achi_viewer.py`; they now 403 and are hidden from directory listings. Also closed a real
  hole found while doing it: the viewer's "smart short-path fallbacks" reassign `target_path` *after*
  the block check ran, so the check is now re-applied to the resolved path.
- **Telegram still delivers those files.** `MediaDispatcher` reads from disk, never through port 8999,
  so nothing about retrieval changed. What changed is the rewrite: for a viewer-blocked path it renders
  the caption as plain text rather than a link that would 403. `VIEWER_BLOCKED_SUBPATHS` in
  `achiAgy/src/media_dispatcher.py` must stay in step with the viewer's list; two tests in
  `achiAgy/tests/test_outbound_media.py` hold that line.
- **The Files/raw boundary is about the file's job, not its extension.** `raw/` holds what is worth
  ingesting and carries the vaults' `sources:` provenance. Files holds finished artifacts and documents
  Aki needs to retrieve *as documents*. A file can be both, and when it is, it lives in Files with the
  wiki `sources:` entry pointing there. That keeps the five files migrated earlier today where they are.
- **`academic/` is term-based**, mirroring schoolMem's `raw/AY####-T#/COURSE/`. Replaced the flat
  `csopesy`/`ths-st1`/`stcloud` folders with `AY2627-T1/{CCINOV8,GELITPH,STDISCM,STSP002,THSST2}` read
  off schoolMem. `general/` sits outside the term tree because a transcript belongs to no term. Future
  term folders get created lazily.
- **Dates in filenames are the document's own date**, not the acquisition date, so a listing reads as a
  timeline of events.
- **Amended the viewer-link rule** in `CLAUDE.md` and `AGENTS.md` with a path-scoped carve-out for
  `~/Documents/Files/`, excluding the two blocked folders. Wrote the store its own `AGENTS.md` and
  `CLAUDE.md` carrying all of the above.

**Why:** The viewer binds `0.0.0.0` with `ROOT_DIR=$HOME` and no authentication, so putting passport
scans under it without blocking them would have been a straight downgrade in Aki's security posture for
no gain. The rest follows from him wanting to tap a document from Telegram, which is the reason the
store exists at all.

**Alternatives considered:** Binding the viewer to the Tailscale IP only (rejected, breaks localhost and
dies if tailscale flaps; the block list is narrower and enough); rolling the five migrated files back to
`raw/` (rejected, they are documents he retrieves, not just ingestion sources); backing the store up to
an encrypted remote (rejected by Aki, he keeps a separate local copy).

**Owner:** Aki.

## 2026-08-28 — Syncthing must never replicate a .git directory

**Decision:** Added `.git`, `.git/**`, `**/.git/**`, and `*.sync-conflict-*` to the `varww-m4imt`
ignore patterns via the Syncthing REST API, and deleted the 23 conflict files that had accumulated.

**Why:** Syncthing was replicating `achiMem/.git/` and `schoolMem/.git/` between two machines that both
run git, and had already produced conflicted copies of `index`, `config`, `ORIG_HEAD`, `COMMIT_EDITMSG`,
and several refs. The usual endgame is a repo that cannot read its own object store. `git fsck` came
back clean on both repos before and after the cleanup, so this was caught before real damage. Git's own
remote already carries tracked files between machines, so Syncthing had nothing to contribute inside
`.git` in the first place.

**Alternatives considered:** Dropping Syncthing for the vaults entirely (rejected, it is what carries
the gitignored `raw/` material to the Mac). Filing it for later (rejected, object-store corruption is
not a thing to schedule).

**Owner:** Aki.

## 2026-08-28 — No ticket-authoring skill; `to-issues` already covers it

**Decision:** Dropped the planned `ticket-author` skill. The existing global `to-issues` skill
already breaks a plan into tracer-bullet vertical slices, quizzes Aki on granularity and
dependencies, and publishes with the body template achiOS already uses: What to build,
Acceptance criteria as checkboxes, Blocked by. Two gaps remain open, both small patches to
`~/.claude/skills/to-issues/SKILL.md` rather than reasons to build something new.

**Why:** The point of the original task was that Aki should not need Opus to write tickets Aea and
Luna can work from. `to-issues` is model-agnostic prose with no Opus dependency, so the need was
already met and nobody had checked. Building a second skill on the same trigger phrase would have
made the router pick one of the two at random, which is worse than either alone.

**Alternatives considered:** A fresh `~/.claude/skills/ticket-author/` reusing the slice rules
(rejected, duplicate triggers). Wrapping `to-issues` (rejected for the same reason). An achiAgy
agent that dispatches authoring to `agy` (rejected, ticket writing is the judgment-heavy step and
a handoff there adds a failure mode for no gain).

**Owner:** Aki.

## 2026-08-28 — Reversal: `/agy-tickets` ships as a copy of `to-issues` after all

**Decision:** Supersedes the entry above. Aki chose to fork `to-issues` rather than patch it.
The copy lives at `~/.claude/skills/agy-tickets/` with a tracked copy in
`references/skills/agy-tickets/`. It differs from the original in four ways: it creates
`ready-for-agent` and the `priority:` labels before publishing instead of applying the
nonexistent `needs-triage`, it adds a Recommended model section with a table for choosing
between `gemini-3.7-flash-high` and Sonnet, it requires an approved plan and refuses a rough
idea, and it uses `--body-file` so backticks in acceptance criteria survive the shell.

**Why:** Patching `to-issues` in place would have been undone by any future refresh of that
skill, and the fork lets the description name Aea and Luna so the router picks it over the
original. The duplicate-trigger risk I raised earlier is real but small, because the two
descriptions now diverge on repo and agent names.

**Alternatives considered:** Editing `to-issues` in place (rejected by Aki). Making it a
project skill under `.claude/skills/` (rejected, it would only load in AIS-OS and the tickets
mostly go to achiAgy). Leaving it uncommitted on the server (rejected, `sync-claude-config.sh`
pushes Mac to server with `rsync --delete` and would have deleted it on the next run).

**Owner:** Aki.

## 2026-08-28 — Plugin hooks trimmed on achibuntu only, and the Mac stays as it is

**Decision:** Disabled `warp`, `claude-notifications-go`, and `vercel` at user scope on the
server, removing 16 of 33 plugin hooks. Kept `claude-mem` and `superpowers-optimized`. Patched
`stop-reminders.js` in the plugin cache so it selects the two newest `[saved]` entries by
timestamp rather than by file position.

**Why:** Warp and the notification plugin are desktop integrations on a headless box and fire
on every turn for nothing. Vercel has no project here. `superpowers-optimized` stays because
its Bash dangerous-command blocker and secret protection are worth keeping on a box that runs
`bypassPermissions` with push to origin pre-authorised. The stop-reminders bug flagged the two
*oldest* entries forever, because `session-log.md` is newest-first and the hook called
`entries.slice(-2)`. Verified against the live file: it was reporting 2026-08-17 03:45 and
2026-08-28 09:40; it now reports 17:52 and 17:45, both inside the budget.

**Why it will not last.** `sync-claude-config.sh` pushes the Mac's `~/.claude/settings.json`
wholesale, so the next sync re-enables all three plugins here. Aki wants them on the Mac, so
this is a deliberate divergence that has to be reapplied after each sync. The
`stop-reminders.js` patch is safe from the sync, which excludes `plugins/`, but a plugin update
overwrites it.

**Alternatives considered:** Putting the disables in `~/.claude/settings.local.json`, which the
sync allowlist does not carry (not chosen, unverified whether `enabledPlugins` merges from that
path, and guessing was worse than a documented reapply). Disabling `superpowers-optimized`
outright (rejected, loses the skill router and both safety hooks). Editing `hooks.json` in the
plugin cache (rejected, a plugin update rewrites it).

**Owner:** Aki.

## 2026-08-29 Global Codex unslop SessionStart hook

Decision: Added `/home/achibukz/.codex/hooks.json` at user scope. Its inline `printf` command emits Aki's supplied `hookSpecificOutput` unchanged. Omitting the matcher covers every SessionStart source.

Why: Aki requested the unslop skill as the default session writing style, with an explicit user override. User scope applies across projects without changing project instructions.

Alternatives: A separate script adds no value for static JSON. Claude Code settings were left unchanged because this request was made in Codex. Trust bypasses were not used; Aki must approve the exact hook through `/hooks` before it runs.

Owner: Aki.

Verification: The saved command returned the exact JSON with four sample SessionStart inputs from `/tmp`. Live context injection remains unverified until trust approval. Format and trust requirements follow the [official hooks documentation](https://learn.chatgpt.com/docs/hooks).

## 2026-08-29 Codex research delivery and execution limits

Decision: Deliver topic 10 as [Markdown](http://100.106.210.38:8999/Documents/Obsidian/achiMem/raw/2026-08-28-codex-in-achios-workflow-and-model-hierarchy.md) and a readable [PDF](http://100.106.210.38:8999/Documents/Files/projects/achios/2026-08-28-codex-in-achios-workflow-and-model-hierarchy.pdf). Stop subagents and further source checking when Aki requests it. Keep the architecture and routing recommendations as proposals.

Why: Aki is already integrating Codex into achiAgy and wants research that informs that work. He explicitly limited delegation to reduce token use and then requested the PDF without further source checks.

Alternatives: Further parallel investigation and a complete final source audit were stopped at Aki's request. No new orchestrator, service migration, or repo rename was executed.

Owner: Aki.

## 2026-08-29 — Accept the 7-day Google token cycle, make gws the only auth path

**Decision.** achiOS stops maintaining two Google auth systems. The `gws` CLI profiles
(`gws-main`, `gws-personal`, `gws-work`, `gws-dlsu`) become the only credential path, and the
legacy `~/.config/achios/google_token*.json` files, `scripts/auth_google_account.py`, and every
direct `google-auth` import get deleted. `gcal_add.py` ports to
`gws calendar events insert --json`.

The seven-day refresh-token expiry stays. GCP project `achiclaude` keeps its consent screen in
Testing, so Google kills refresh tokens weekly. Detection and a weekly re-auth nudge replace the
fix.

**Why.** All three legacy tokens were dead for five days before anyone noticed, because the
digests silently fall back to `gws` and `gcal_add.py` silently fails. Two auth systems where one
is dead is worse than one. A constraint settles the direction: `gws` stores credentials as
ciphertext keyed by `.encryption_key`, so Python's `google-auth` can never load them. The CLI is
the only way in, and three scripts already use it.

**Alternatives.** Publishing the consent screen to Production is the actual root fix and costs
nothing, and Aki declined it: no domain, no appetite for the unverified-app warning path. A
service account cannot read personal Gmail or Calendar without Workspace domain-wide delegation
he does not control. A token rotation script cannot revive a token Google deliberately expires.

**Owner.** Aki. Plan in `docs/2026-08-29-google-auth-lifecycle-and-tasks-renderer-plan.md`,
tickets AIS-OS #3 to #8.

## 2026-08-29 — /tasks renders from a shared deterministic skeleton, not a free-form model turn

**Decision.** `cmd_tasks` in achiCore stops handing the literal string `/tasks` to a model.
Deadline sections are computed in Python and never move. A pinned `gemini-3.7-flash-high` call
groups only the undated remainder, and any failure falls back to the deterministic card. One
renderer in `scripts/tasks_digest.py` serves both the cron and the bot.

**Why.** Structure moving between invocations is what made the output feel random, and deadlines
are objective facts a model should never adjudicate. The undated pile is the one place dynamic
grouping earns its cost. `daily_brief.py` already runs this degradation contract.

**Alternatives.** Fully deterministic output, which loses the dynamic categorisation Aki
explicitly wanted. Fully dynamic categories, which reintroduces the drift. A constrained model
over the whole list, which puts deadlines back in the model's hands.

**Owner.** Aki. Tickets AIS-OS #6 and achiCore #57; the model pass is held back from that batch.

## 2026-09-02 — Shared Telegram image sender skill

**Decision:** Created `telegram-image-sender` in the global Skillshare source at `~/.config/skillshare/skills/` and synced it to all seven configured AI tool targets. The skill instructs agents to emit standard Markdown image tags with local absolute paths so the achiOS bridge can dispatch the file and rewrite the text reference to a Tailscale viewer link.

**Why:** Aki wants one reusable instruction set across Codex, Claude, Gemini, Antigravity, Hermes, Copilot, and Universal. The existing bridge already recognizes this syntax, so a shared skill keeps the behavior consistent without another sender or tag format.

**Alternatives considered:** A Codex-only skill, a custom `[send_photo: path]` tag, and direct Telegram API calls from each agent.

**Owner:** Aki.

## 2026-09-05 Autonomous learning and connected workflows

Decision. Aki chose automatic learning from normal Telegram requests, corrections and verified outcomes. Initial placement preferences put social plans in Calendar, quick tasks and coding tickets in tasks.md, and school deadlines in both. These are editable starting preferences. A correction repairs its current item and changes future matching behavior within the supported scope. One-time exceptions remain local to the item.

Verified facts and procedures may be reused automatically. A procedure needs one observed success and relevant checks. Shared skills and operating rules need a reviewed PR. Automatic wiki updates will target designated sections on the achi-os, achi-core and achibuntu pages, completed-work timeline rows and Tooling / workflow decision pointers. The implementation must preserve domain boundaries and source provenance.

The runtime must work with Gemini 3.8 Flash in both the foreground and background. Background review has a limit of 24 short calls per Manila day. Routine changes belong in the daily digest, with separate actionable alerts. A live Flash pilot must prove correction, later reuse, notes and linked ticket completion before activation.

Why. Capturing text alone does not make the next action better. Stable item IDs, observed outcomes, current recall and reliable retries connect the existing stores. The worktree audit also reproduced environment failures before useful testing; preparation and recovery need deterministic checks before another paid model attempt.

Alternatives considered. A required /learn command, fixed Calendar routing rules, a larger global memory file, unrestricted automatic rule changes and migration to Hermes as the runtime. Aki's requested behavior instead uses automatic typed learning over the existing Telegram and repository workflow.

Owner. Aki. The [Astra plan](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md) records the design and evidence; [ticket bodies](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-tickets.md) record the implementation slices. This is a planned change, not a claim that automatic learning or wiki promotion is deployed. Aki approved the breakdown and the implementation issues are published. Issue #83 closes the design discussion; the implementation issues remain open.

Aki also requested a separate follow-up planning session for a control board or Kanban frontend connecting these workflows. The current batch should expose reusable status and action contracts; frontend scope and interaction design remain for that session.
