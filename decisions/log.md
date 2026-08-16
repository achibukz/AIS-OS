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
