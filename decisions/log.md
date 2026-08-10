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
