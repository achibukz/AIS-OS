# achiOS → achiMem auto-logging

Date: 2026-08-10
Status: approved, not yet implemented

## Problem

Work done in achiOS (`~/Code/GitHub/AIS-OS/`) leaves no trace in achiMem
(`~/Documents/Obsidian/achiMem/`), the knowledge base that is supposed to be the memory
layer of the whole system. Decisions, discoveries, and shipped work live only in the
session transcript and are gone once the session closes.

Two additional problems surfaced while scoping this:

1. **`sync-achimem` is broken, not merely stale.** It writes to `wiki/work/`, a folder that
   does not exist. The vault uses `wiki/personal/`, `wiki/studies/`, `wiki/general/`.
   Running it today would create an orphan folder outside the schema.
2. **achiMem itself flagged the ownership question as unresolved.** `wiki/personal/achi-os.md`
   records: *"achiOS and achiMem both have a `decisions/` concept and both claim to hold
   context. Canonical ownership needs deciding."* This design resolves it.

## Constraints

achiMem's `CLAUDE.md` is a strict constitution and the design must not undermine it:

- **INGEST is a two-phase human gate.** Surface takeaways, stop, wait for page selection,
  then write. Anything reaching `wiki/` prose goes through it.
- **Never invent a fact about Aki.** Every `wiki/personal/` fact carries a provenance tag
  (`[stated]` / `[document]` / `[inferred]`).
- **Pointers, not copies.** One canonical home per fact. Bridge pages may hold dated
  snapshots under a `> [stale?]` marker; a snapshot is never an answer.

The design's central move is to route all unattended writes to targets where these rules
do not apply (`raw/`, `log.md`), and gate every `wiki/` write behind a human.

## Decisions

| Decision | Choice |
|---|---|
| Write policy | Hybrid: raw drop for everything, narrow append-only allowlist beyond that |
| Trigger | SessionEnd hook (automatic) + skill (manual, mid-session) |
| Scope | AIS-OS repo only. Hook lives in `AIS-OS/.claude/settings.json` |
| Summarizer | Mechanical stub written first, then background Haiku enrichment, with a SessionStart nudge as fallback |
| Noise filter | Capture only if files were written, a commit was made, or turns ≥ 6 |
| Decisions ownership | Split by kind, with a promotion rule |
| Skill | Rewrite `sync-achimem` in place |
| Skill depth | Capture immediately, then offer INGEST Phase 1 |
| Version control | `git init` achiMem, hook commits its own writes |
| claude-mem | Exclude AIS-OS, replace its recall with an achiMem-sourced SessionStart digest |

## Write allowlist

The allowlist is split by *who is writing*, which is a refinement on the original decision.

| Target | Unattended (hook + Haiku) | In session (skill / me) |
|---|---|---|
| `raw/sessions/*.md` | yes | yes |
| `log.md` | yes | yes |
| `wiki/personal/timeline.md` | no | yes, append row |
| `wiki/personal/decisions.md` | no | yes, append row |
| `wiki/personal/achi-os.md` | no | yes, snapshot block |
| `wiki/**` everything else | no | INGEST only |
| `index.md` | no | yes, when a page is created |

Rationale: `raw/` and `log.md` sit outside `wiki/`, so a bad entry is noise. A bad row in
`wiki/personal/` is a fabricated fact about a real person in the one place the vault
promises there are none. Nothing is lost by deferring: the SessionStart nudge surfaces
pending sessions so those rows get written with a human present.

**Haiku never writes files.** The enrichment subprocess is invoked with no tools and its
markdown output is captured from stdout; the wrapper script performs the write. An LLM
failure can therefore produce bad *text*, never a bad *file operation*.

## Architecture

Four components. Two hooks, one skill, one config change.

### 1. `scripts/achimem_capture.py` — SessionEnd hook

Python 3, stdlib only. Reads hook JSON on stdin (`session_id`, `transcript_path`, `cwd`,
`reason`).

```
1. Guard: exit 0 if ACHIMEM_CAPTURE=1 or CLAUDE_MEM_INTERNAL=1   (recursion)
2. Parse transcript JSONL:
     - assistant turn count
     - tool_use blocks named Edit | Write | NotebookEdit  → files touched
     - Bash blocks matching 'git commit'                  → commits made
     - first user message
3. Gate: exit 0 silently unless
     files_touched OR commits_made OR turns >= 6
4. Write stub → achiMem/raw/sessions/YYYY-MM-DD-achios-<short-id>.md
     status: unenriched
5. Build a condensed transcript digest (user messages + assistant text +
   tool names/paths), truncate to ~50k chars
6. Spawn detached:  ACHIMEM_CAPTURE=1 CLAUDE_MEM_INTERNAL=1 \
                    claude -p --model claude-haiku-4-5-20251001
   Capture stdout, rewrite the body, flip status: enriched
7. git add <the two paths we wrote> && git commit
```

Stub format:

```markdown
---
title: "achiOS session — 2026-08-10"
type: session
status: unenriched
session_id: a1b2c3…
transcript: /Users/…/a1b2c3.jsonl
branch: main
created: 2026-08-10
tags: [achios, session]
---

## Mechanical record
- Files touched: CLAUDE.md, scripts/achimem_capture.py
- Commits: none
- Turns: 14
- Opening ask: "<first user message, truncated to 300 chars>"
```

Enriched body replaces `## Mechanical record` with: what was done, decisions made, open
threads, files touched. The frontmatter is preserved and `status` flips.

Git staging is path-scoped, not `git add -A`, so the hook never sweeps up Aki's own
unsaved Obsidian edits.

### 2. `scripts/achimem_recall.py` — SessionStart hook

Stdlib only, no LLM call, no network. Reads `raw/sessions/` only — not `log.md`, which is
vault-wide and mostly unrelated to achiOS. Emits `hookSpecificOutput.additionalContext`:

```
── achiMem recall ──
Last 3 sessions:
  2026-08-09  wired achimem capture hook
  2026-08-08  fixed sync-achimem paths
Open threads: 2
Unenriched logs: 0
```

Sources, precisely: the three most recent files by filename date, using each file's `title`
line; the count of bullets under `## Open threads` across the last five enriched files; and
the count of files with `status: unenriched`.

This replaces the claude-mem digest inside AIS-OS. If unenriched logs exist, the count is
the nudge and I offer to process them.

### 3. `~/.claude/skills/sync-achimem/SKILL.md` — rewritten

Three modes, dispatched by what Aki says:

- **capture** (`/log-achimem`, "log this to achimem") — writes the `raw/sessions/` file and
  the in-session allowlist rows now, then runs achiMem INGEST Phase 1: surface 3–8
  candidate pages, **stop**, wait. On selection, write them properly with provenance tags,
  update `index.md`, add backlinks, append to `log.md`.
- **process pending** — enrich `status: unenriched` stubs with the transcript available.
- **sync** — existing internship-pipeline behaviour, with `wiki/work/` corrected to
  `wiki/personal/`.

Per Aki's standing rule, the rewrite goes through the `skill-creator` workflow.

### 4. claude-mem exclusion

`~/.claude-mem/settings.json`:

```json
"CLAUDE_MEM_EXCLUDED_PROJECTS": "~/Code/GitHub/AIS-OS,~/Code/GitHub/AIS-OS/**"
```

The matcher (`worker-service.cjs`, functions `fL` and `ebt`) is a comma-separated list of
globs, each compiled to an anchored regex (`^…$`) with `~` expanded, `*` → `[^/]*`,
`**` → `.*`, and tested against both the full cwd and its basename. Because it is anchored,
the bare pattern `AIS-OS` would match only the repo root and miss every subdirectory —
hence both entries. No other project is affected.

## Decisions ownership, resolved

`AIS-OS/decisions/log.md` is canonical for **build and tooling** decisions: prose format,
full "alternatives considered", per-project.

`achiMem/wiki/personal/decisions.md` is canonical for **life and strategy** decisions:
table format, categorized (Financial, Career, …). It gains a `## Systems` category.

**Promotion test:** a build decision is promoted to achiMem only if it changes how Aki
works, spends, or decides *outside the repo*. Promotion writes a one-line row linking back
to the AIS-OS entry. The reasoning is never duplicated.

- "Use `-mc 0` on whisper to stop repetition" — stays in AIS-OS.
- "achiOS auto-logs to achiMem" — promoted.

This closes the open question filed in `achi-os.md` on 2026-08-10.

## achiMem CLAUDE.md amendments

1. **Folder layout** — document `raw/sessions/` as the automated capture destination,
   distinct from the hand-dropped sources in `raw/`.
2. **Behavior rule 1** — currently reads "Never modify files in `raw/`." The enrichment step
   rewrites its own stub, which violates this as written. Amend to: never modify
   hand-dropped sources in `raw/`; `raw/sessions/` is machine-owned and the capture pipeline
   may rewrite a file it created while `status: unenriched`. Once `enriched`, it is
   immutable like any other source.
3. **New section: Automated writes** — the allowlist table above, verbatim, plus the rule
   that everything else requires INGEST.
4. **Frontmatter** — add `status: unenriched | enriched` and `type: session`.
5. **Log format** — add `session` to the action list.
6. **decisions.md** — add the `## Systems` category and the promotion test.
7. **achi-os.md** — mark the decisions-ownership open question resolved, and record the
   capture pipeline in the agent-layer table.

## AIS-OS CLAUDE.md amendments

New **Logging contract** section covering: what auto-captures and when; my in-session
responsibilities (on a decision, write `decisions/log.md` and apply the promotion test out
loud); pointers-not-copies, so achiOS never duplicates achiMem content; and the fact that
claude-mem is off in this repo, with achiMem as the sole memory.

## Version control

`git init` in achiMem. `.gitignore` for `.obsidian/workspace*.json`, `.obsidian/cache`,
`.DS_Store`. Initial commit of current state. Hook commits use the message form
`achimem: auto-capture <session-id>`, so automated writes are greppable and separable from
Aki's own edits.

## Error handling

| Failure | Behaviour |
|---|---|
| Hook recursion | `ACHIMEM_CAPTURE=1` + `CLAUDE_MEM_INTERNAL=1` guard, checked first |
| Detached Haiku dies mid-run | Stub was written first and `status` only flips on success, so the file stays valid and unenriched. SessionStart surfaces it |
| Haiku returns garbage | Bad text in `raw/`, never a bad file operation — Haiku has no tools |
| Transcript unparseable | Log to stderr, write the stub with `turns: unknown`, do not block session exit |
| achiMem git conflict | Path-scoped `git add`; on commit failure, log and exit 0 — the file is still on disk |
| Obsidian holds a file open | All unattended writes are new files or appends, never rewrites |
| Hook itself throws | Wrap `main()`, always `exit 0`. A logging system must never break a session |

## Testing

`tests/test_achimem_capture.py`, pytest, against JSONL fixtures:

- turn counting on a mixed transcript
- `Edit`/`Write`/`NotebookEdit` extraction, including multiple tool_use blocks per message
- `git commit` detection in Bash tool inputs
- gate: below threshold and no writes → no output file
- gate: zero turns but one file written → captured
- recursion guard: `ACHIMEM_CAPTURE=1` → immediate exit, no side effects
- stub frontmatter is valid YAML and round-trips
- malformed JSONL line does not crash the parser
- `achimem_recall.py` on an empty `raw/sessions/` returns valid, empty context

## File manifest

New:
- `AIS-OS/scripts/achimem_capture.py`
- `AIS-OS/scripts/achimem_recall.py`
- `AIS-OS/tests/test_achimem_capture.py`
- `AIS-OS/.claude/settings.json`

Edited:
- `~/.claude/skills/sync-achimem/SKILL.md`
- `~/.claude-mem/settings.json`
- `~/Documents/Obsidian/achiMem/CLAUDE.md`
- `~/Documents/Obsidian/achiMem/wiki/personal/decisions.md`
- `~/Documents/Obsidian/achiMem/wiki/personal/achi-os.md`
- `AIS-OS/CLAUDE.md`
- `AIS-OS/decisions/log.md`

Created:
- achiMem git repo + `.gitignore`
- `achiMem/raw/sessions/`

## Out of scope

- Extending capture to other repos (`sfv-thesis`, `career-ops`). Prove it in AIS-OS first.
- Migrating existing claude-mem observations into achiMem.
- Touching schoolMem or its `ingest-batch` pipeline.
- The full achiOS INGEST that `achi-os.md` still has pending.
