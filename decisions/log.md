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

---

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

