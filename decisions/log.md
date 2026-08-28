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
