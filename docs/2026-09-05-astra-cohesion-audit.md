# achiOS cohesion audit and Astra handoff

Snapshot taken 2026-09-05 around 03:30 Asia/Manila, which is 2026-09-04 around 19:30 UTC.

This audit follows the scope in [astra-plan.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md). It focuses on Telegram sessions, GitHub repositories, achiMem, schoolMem, the Documents/Files store, the Tailscale viewer, tasks, Google Calendar, schedules, and the self-learning loop. It does not attempt a general server hardening review.

No fixes were applied. Existing working-tree changes were left alone.

## Verdict

The system has many capable parts, but no shared control loop. Telegram, GitHub, the two vaults, the Files store, calendars, systemd, and Hermes each keep their own state. Most transfers between them depend on Aki remembering to copy, restart, bind, commit, reauthenticate, or explain context again.

The main bottleneck is cohesion.

I would rate the current system as follows.

| Area | Grade | Reason |
|---|---:|---|
| Telegram execution | B | Topic routing, engine selection, worker worktrees, review handoff, and CI gating work. Session continuity and topic discipline do not. |
| GitHub execution | B | achiCore has a functioning ticket to writer to reviewer path. The wider repository estate lacks one inventory, lifecycle, and cleanup policy. |
| Personal knowledge | C | achiMem has a sound schema and linter. Current writes can remain local and Telegram history no longer feeds it. |
| School knowledge | C | Existing material resolves correctly, but the new term is barely populated and there is no structural linter. |
| Documents and media | C | Retrieval and Immich work. The 115 GB memory library is inside the Syncthing set despite a prior instruction not to sync it. |
| Tasks and calendar | D | The task register hides 28 delegated tasks. All four Google profiles are dead. No reconciliation exists. |
| Self-learning | D | Most successful writes bypass the gate. Memory is full, stale rules conflict with personas, and warm sessions do not see new writes. |
| Scheduling and health | D | systemd and Hermes overlap. Alerts share failed dependencies. There is no common execution ledger. |

## What is working

- achiCore currently has 12 bound Telegram threads, 15 topic definitions, and 13 session records. Topic isolation, per-engine conversations, worker worktrees, and review routing are real, not plans.
- Five completed achiCore review loops reached a shipped result. The current achiCore pull request, [PR 130](https://github.com/achibukz/achiCore/pull/130), is approved and passed Python 3.11, 3.12, and 3.13 CI.
- The Tailscale viewer returned HTTP 200 for the Astra plan and achiMem index. It returned HTTP 403 for `Documents/Files/personal/legal` and `Documents/Files/personal/finance`.
- achiMem's structural linter checked 107 wiki pages with 0 errors and 3 warnings.
- schoolMem has 0 missing wiki-link targets in 2,233 live links when links are resolved relative to their page. Four bare links are ambiguous.
- Syncthing reports both the Files store and Obsidian vault folder as idle with 0 bytes needed.
- Focused achiCore learning tests passed: 32 tests in `test_background_review.py`, `test_memory_engine.py`, and `test_learn_command.py`.

These successes matter. The problem is what happens between them.

## System map

```text
Telegram topics
  |-- general, atlas, aea, luna, ara, aurora, career-ops
  |-- achimem, schoolmem
  |-- numbered writer and reviewer topics
  |
  +--> achiCore sessions.json and append-only topic logs
  |      |--> worker worktrees --> GitHub issues, PRs, CI
  |      |--> small global USER.md and MEMORY.md
  |      `--> paused TGDB export
  |
  +--> manual requests to achiMem, schoolMem, Files, tasks.md, or GCal

tasks.md --------> task digests --------> Telegram
   |                    |
   |                    `--> only 9 top-level active lines
   `--> manual gcal_add.py --------> four expired Google profiles

systemd timers --------> scripts and logs
Hermes cron -----------> separate jobs.json and executions.db

achiMem and schoolMem --> Git plus Syncthing
Files -----------------> Syncthing plus Immich plus viewer
```

There is no event or item ID that follows one commitment through this map. A Telegram request, task line, calendar event, GitHub issue, vault note, and reminder can describe the same thing without the system knowing they are related.

## Highest-priority findings

### P0. Do not merge the viewer secrets toggle in its current form

[AIS-OS PR 10](https://github.com/achibukz/AIS-OS/pull/10) adds a flag file and environment variable that disable every viewer block. The viewer binds `0.0.0.0:8999`, has no authentication, and serves `/home/achibukz`. The proposed switch would expose `.env` files, private keys, Git internals, legal documents, and finance documents to every network interface that can reach the port.

The pull request has no CI status, no review, six commits, and nine changed files. Most files are unrelated to the viewer toggle. This is unsafe release packaging for a control that can expose credentials.

Required before merge:

1. Split the viewer change into its own pull request.
2. Keep legal, finance, credentials, keys, and Git internals unconditionally blocked.
3. If temporary access is still wanted, use authentication, a narrow allowlist, a short expiry, and an audit record.
4. Bind to the Tailscale address or prove host firewall policy limits port 8999 to Tailscale.
5. Add integration tests that start the server and verify protected paths over HTTP.

### P0. Google Calendar is disconnected now

All four `gws` profiles, `personal`, `dlsu`, `main`, and `work`, have encrypted credentials and refresh tokens. Google rejects all four with `invalid_grant` because the tokens expired or were revoked.

The 2026-09-05 dry run of `scripts/daily_brief.py` rendered no schedule and named all four failed profiles. The 2026-09-04 scheduled run also lost Telegram delivery during a DNS outage. The systemd service remains failed.

This needs an interactive browser reauthentication. The open Google-auth work in [AIS-OS issues 3, 5, 6, 7, and 8](https://github.com/achibukz/AIS-OS/issues) is still accurate. Moving the OAuth consent screen to Production and adding a read-based health check are more useful than another weekly reminder to repair tokens after they die.

### P0. achiMem has current knowledge with no remote backup

achiMem is level with `origin/main`, but the working tree has 18 changed status entries. They include 10 modified pages and new NAPI material. The every-15-minute vault timer reports success because `scripts/vault_inbox_sync.py` watches only `inbox/`.

The success message does not mean the vault is backed up. It means there are no pending inbox captures.

The immediate operational task is to review and commit the current achiMem changes through its normal vault process. The lasting fix is a health check that compares the whole vault with its upstream while leaving automated commits limited to trusted paths.

### P0. Historical logs retain Telegram credentials

Four logs under `~/.local/state/achios` contain complete historic Telegram bot tokens inside exception URLs. The files are `email_digest.log`, `evening_debrief.log`, `tasks_digest.log`, and `voo_digest.log`. They contain three distinct old tokens.

The current configured token does not match any token found in those logs, so the active token appears to have been rotated. The remaining work is safe log redaction and retention. Do not delete the logs until any useful failure history has been exported in sanitized form.

## Telegram session audit

### State and topic use

Current state:

- 12 topic bindings
- 15 topic definitions
- 13 session records
- 7 completed `/ToWork` job records, with 5 achiCore jobs merged, 1 opus-subagents job abandoned, and 1 current achiCore job represented by PR 130
- 5 finished review-loop records

The current topics include General, Atlas, Aea, Luna, achiMem, schoolMem, Ara, Aurora, Career Ops, Claude Test, Aea1, and Luna1. Ari exists as a definition but is not bound.

The main operational mismatch is topic use. A simple scan of user prompts in the raw logs found:

| Topic | Detected prompts | Resets | Error-like log markers | What it is being used for |
|---|---:|---:|---:|---|
| General | 292 | 42 | 111 | Scheduling, health, repositories, research, tasks, devices, and knowledge retrieval |
| Aea | 125 | 39 | 148 | Coding and repository work across the broad GitHub parent |
| Luna | 91 | 39 | 52 | Review and research, with repeated requests to submit the formal GitHub review |
| Atlas | 46 | 19 | 14 | System control, restarts, tmux, and `/ToWork` |
| Career Ops | 18 | not material | not material | Career repository work |
| schoolMem | 9 | not material | not material | School knowledge work, last active 2026-08-29 |
| achiMem | 1 in the current raw-log format | not material | not material | Personal knowledge work |

The error-like counts are text markers, not unique confirmed incidents. They are useful as a comparison of friction across topics.

General is the actual front door for nearly everything. Dedicated topics exist, but Aki still has to decide where a message belongs before the system can preserve the right context. This reverses the intended relationship. The router should classify the work after capture, then send a receipt showing where it went.

### Session metrics cannot be trusted as lifecycle metrics

Examples from the live state:

- General reports 4 turns but has a 4.8 MB log and 292 detected user prompts.
- Atlas reports 0 turns and 7 turns since review.
- Aea reports 1 turn and 9 turns since review.
- Luna reports 0 turns and 6 turns since review.
- General records more than 9 million cumulative output tokens while the current conversation records only 4 turns.

Conversation resets, project switching, cumulative usage, and review counters use different boundaries. The JSON values may be correct inside their own code paths, but they cannot answer basic questions such as how much one topic costs per day or when its last complete session ended.

The session model needs explicit IDs for topic, conversation, run, turn, delegated job, and review cycle. Metrics should aggregate from immutable turn events instead of incrementing mutable counters in several paths.

### Context still depends on restarts and manual reminders

The logs contain repeated requests to restart the hub, continue after a reset, inspect tmux, switch into a specific repository, and submit the GitHub review that Luna had already discussed. These are coordination tasks that should be state transitions.

Aea's unnumbered topic is configured at `/home/achibukz/Code/GitHub`, the parent of many repositories. That causes repository selection to become part of the prompt. Use a bound project or require a repository selection card before an editing turn.

### Telegram history is not becoming searchable knowledge

Raw topic logs continue to grow, but automatic TGDB writes and scheduled transcript export were paused on 2026-08-31 because the old loop produced bad records. Existing achiMem TGDB material is about 7 MB and mostly covers August. Current September conversations are not entering either vault.

Pausing the corrupting writer was correct. The missing replacement means every useful correction, decision, and result after the pause remains trapped in raw logs unless someone moves it manually.

## GitHub and repository audit

### Remote estate

The `achibukz` account currently has 50 visible repositories. None is archived. Only 9 were pushed after 2026-08-01. The estate mixes active system repositories, current school work, finished school projects, experiments, forks, and empty placeholders without lifecycle labels.

Open work is concentrated in three repositories:

| Repository | Open issues | Open pull requests | Current automation state |
|---|---:|---:|---|
| achiCore | 23 | 1 | CI is active and green on recent runs |
| opus-subagents | 19 | 0 | No recent GitHub Actions runs |
| AIS-OS | 5 | 1 | No recent GitHub Actions runs |
| career-ops | 0 | 1 | Recent tests and release automation are green |

There is also one old open pull request in `csopesy-mco1` from June.

The repository list needs lifecycle metadata. At minimum, every repo should be `active`, `maintenance`, `reference`, or `archive`, with an owner, canonical local path, task source, CI expectation, and last meaningful verification date. Archive finished and empty repositories instead of leaving all 50 in one active-looking list.

### Local estate

There are 19 Git worktrees or independent checkouts under `~/Code/GitHub` in the current scan. Nine belong to achiCore. Several are finished ticket worktrees whose branches have already reached remote state. `achiCore-ticket-57` is 19 commits behind `origin/master` and has local changes. `buzz` is 139 commits behind upstream with one local change. AIS-OS has a second worktree with 24 status entries. The main AIS-OS checkout has four pre-existing status entries.

This is not only disk clutter. A stale worktree can be selected by a Telegram topic, cited in a task, or mistaken for the canonical checkout.

Add a worktree registry tied to `/ToWork` records. A merged or abandoned job should enter `cleanup_pending`, but cleanup must remain explicit and refuse dirty worktrees. A daily read-only check can report stale, detached, dirty, and upstream-missing worktrees.

### GitHub work and personal tasks are separate queues

achiCore has a strong issue-based execution path. Personal tasks live in [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md). Cross-repo work sometimes appears in both. Nothing records that a task line is fulfilled by a given issue or pull request unless a person adds the link.

Use GitHub issues as the source for repository work. Let the personal task register hold a linked summary and the next action. A merged pull request should close or update its linked personal task automatically.

## Knowledge audit

### achiMem

Strengths:

- 107 linted wiki pages with 0 structural errors
- A declared schema, provenance rules, generated index check, and session capture scripts
- Clear domain pages for identity, work, decisions, timeline, health, and systems
- Git and Syncthing both exist

Gaps:

- Current agent-written pages can remain outside Git while the inbox timer stays green.
- [connections.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/connections.md) says `achiMem/index.md` is the entry point, but that file does not exist. The real entry point is [wiki/index.md](http://100.106.210.38:8999/Documents/Obsidian/achiMem/wiki/index.md).
- The Claude session capture and recall scripts do not cover achiCore Telegram sessions.
- The TGDB pipeline is paused and has no replacement queue.
- The linter reported missing provenance tags on two health and systems pages, plus one orphan prescription page.

### schoolMem

Strengths:

- Git is clean and level with `origin/main`.
- The 2,233 checked live wiki links have 0 missing targets.
- AY2526-T3 remains a substantial archive with 202 Markdown pages.
- AY2627-T1 has a term index and five subject roots.

Gaps:

- AY2627-T1 contains only 11 Markdown files. Most subject directories are placeholders.
- The latest wiki modification is 2026-08-28. The dedicated Telegram topic was last active on 2026-08-29.
- There is no schoolMem equivalent of achiMem's linter or generated-index check.
- Four bare links are ambiguous because both terms contain files named `CLAUDE.md`, `active-tasks.md`, or similar names.
- `notes/2026-06-10-STCLOUD-study-notes-WRONG.pdf` is an explicit dead-data candidate and should be reviewed, not deleted blindly.

### Documents/Files

Current shape:

- 116 GB total
- 7,195 files
- 115 GB under `personal/`
- 7,160 files under `personal/memories`
- 4,979 JPG files, 1,336 HEIC files, and 681 MOV files
- individual videos as large as 2.7 GiB
- 0 ignore patterns on Syncthing folder `achi-files`
- 123.5 GB reported by Syncthing for that folder

The memory library is being synchronized in full. This conflicts with the earlier Telegram instruction that the large memory folder should not be part of Syncthing. Immich already reads this directory as an external library, so Syncthing and Immich are doing different jobs against the same 115 GB tree.

Decide the intended replication policy before changing it. If the Mac already has the source media, exclude `personal/memories` from Syncthing and use a proper backup to the almost-empty external disk. If Syncthing is meant to replicate the media, document that choice and account for root-disk pressure. Syncthing versioning on the same disk is not a backup.

The Files store also lacks a lightweight catalog. Retrieval depends on path memory, directory browsing, or Immich album names. Add an index of document metadata and checksums for non-media files. Keep original files where they are and store provenance links in the vaults.

### Tailscale viewer

The viewer works for normal Markdown and Files paths. Its blocked paths match achiCore's special handling for legal and finance files. The important conflict is elsewhere: global `MEMORY.md` still tells agents to use `file://` links when Aki says "show me." Topic mixins and vault instructions require the HTTP viewer and ban `file://` links.

This is one concrete example of global memory overriding current system design. Resolve it through [achiCore issue 56](https://github.com/achibukz/achiCore/issues/56), not by adding another topic-specific exception.

## Tasks, calendar, and schedule audit

### tasks.md is not one source of truth

[tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md) declares itself the master register and contains 9 active top-level tasks. Two of those tasks are links to separate backlogs:

- [tasks-systems-engineering.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/tasks-systems-engineering.md), with 20 active items
- [tasks-asa-research.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/tasks-asa-research.md), with 8 active items

The task digest reports 9 active tasks and reduces those 28 actions to two summary lines. The register is human-readable, but the parser sees only the outer checklist.

The full AIS-OS test run confirmed the known regression: 275 tests passed and 44 failed. All 44 failures came from `test_daily_brief.py`, whose expected task and formatting functions no longer exist in `daily_brief.py`. [AIS-OS issue 3](https://github.com/achibukz/AIS-OS/issues/3) remains open.

### Dates are copied, not synchronized

`gcal_add.py` can create an idempotent all-day event for a dated task. Nothing calls it automatically when a task is added, edited, completed, deferred, or deleted. Calendar changes do not update the task. Similar wording can produce duplicates.

Use one stable task ID in the task record and in the calendar event's extended properties. Reconcile both directions on a schedule. A completion should remove or mark the calendar event. A moved event should propose a task-date change instead of silently rewriting it.

### Two scheduler systems overlap

systemd has 11 active timers for briefs, digests, bot restarts, vault sync, Immich, and finance. Hermes has one enabled cron job named `Daily 7am task + calendar briefing`.

The Hermes execution database contains 19 executions and 19 failures from 2026-08-16 through 2026-09-03. The current failures are drift skips because the job was created with one provider and model, the global configuration changed, and the job was never pinned. systemd separately runs a daily 08:00 brief.

Choose one owner for each schedule. Use systemd for deterministic host scripts. Use Hermes only when the job needs an agent. Both should write execution results into one read-only health view.

### Failure alerts are not independent

Most user services use a Telegram failure alert. During the 2026-09-04 DNS outage, the daily brief failed to reach Telegram and its Telegram failure alert failed too. `systemctl --user --failed` currently lists the daily brief and four failure-alert instances.

The alert path needs a local outbox. Record a failure first, then retry delivery after network recovery. One later recovery message can summarize the outage without sending a message on every failed attempt.

## Self-learning loop audit

The current implementation should remain paused for broad knowledge capture. It is a preference harvester with a tiny global store, not a cohesive learning system.

### What the ledger says

The append-only learning ledger currently has 145 latest records:

| State or path | Count |
|---|---:|
| Written | 58 |
| Rejected | 76 |
| Pending | 11 |
| Successful direct CLI writes | 50 |
| Successful loop-gated writes | 7 |
| Successful legacy or unspecified write | 1 |

About 86 percent of successful writes used the direct CLI path, not the LLM gate. The ledger records those writes but does not gate them or count them against the daily budget.

The oldest pending item dates to 2026-08-27. A pending queue that can wait more than a week is not an active feedback loop.

### The stores are full

- `MEMORY.md` is 2,480 characters against a 2,500-character cap.
- `USER.md` is 2,493 characters against a 2,500-character cap.

When the background writer reaches the cap, it replaces the oldest entry. That can remove a high-value rule without a user decision. The files also contain stale paths, topic-scoped facts, a global Agi identity, and the conflicting `file://` instruction.

### Capture misses ordinary facts

`scripts/memory_gate.py` only calls the classifier when a prompt contains one of 21 phrases such as "remember that," "I prefer," or "never use." Ordinary durable facts do not enter the queue.

The gate can only classify a candidate as a global `user` or `memory` rule. It cannot route a fact to achiMem, a school fact to schoolMem, a repository convention to `AGENTS.md`, a procedure to a skill, a commitment to the task register, or a date to Calendar.

### New memory does not reach warm sessions

achiCore prepends `USER.md` and `MEMORY.md` when a conversation has no conversation ID. Existing Antigravity and Codex conversations keep their cached context. A successful learning write may not affect an active topic until `/new` creates another conversation.

This makes the loop's feedback timing unpredictable.

### The procedure-learning path is dead

The `/learn` prompt tells the agent to write skills under `~/.gemini/antigravity-cli/skills/`. Antigravity reads `~/.gemini/config/skills`. The old target directory does not exist.

Even with the path fixed, a new skill would not automatically enter the scoped allowlist for a topic, a Codex home, Claude Code, or Skillshare. The tests verify prompt text and routing, but they do not prove that a learned skill becomes discoverable by the next session.

### What the replacement should learn

The replacement needs typed destinations:

| Learned item | Canonical destination | Approval rule |
|---|---|---|
| Stable personal fact | achiMem page with provenance | Review queue, then vault writer |
| School fact or course material | schoolMem page under the active term | Review queue, then schoolMem writer |
| Communication preference | small `USER.md` entry | User approval for replacement or conflict |
| Cross-session operating rule | small `MEMORY.md` entry | User approval and conflict check |
| Repository rule | repository `AGENTS.md` or issue | Pull request if behavior changes |
| Reusable procedure | canonical Skillshare skill | Tests, allowlist update, and review |
| Task or commitment | canonical task record | Immediate capture, deduplicated by source ID |
| Date or appointment | Google Calendar event linked to task ID | Confirm if inferred, direct if explicit |
| File or document | Documents/Files plus vault provenance link | No copy if the original already exists |
| Code work | GitHub issue, branch, pull request, CI record | Existing Aea and Luna flow |

Do not let a model write straight into final stores. First write a candidate event. Classify it. Detect conflicts and duplicates. Show a review receipt. Apply the approved mutation through the destination's own writer. Record the result and source event ID.

## Target cohesive design

### One event ledger

Create one local append-only ledger for all cross-system events. SQLite is a better fit than several JSON files because it supports unique constraints, transactions, queries, and migrations.

Minimum records:

- source event with immutable ID, timestamp, actor, Telegram topic, and source reference
- extracted item with type, domain, confidence, provenance, and proposed destination
- approval with actor and decision
- mutation with destination, destination ID, checksum, result, and rollback reference
- delivery attempt with channel, status, retry time, and final receipt

Do not store full sensitive documents or credentials in this database. Store paths and hashes.

### One intake path

Every Telegram topic should accept an unclassified request. The intake layer can route after capture:

1. Record the raw event and topic.
2. Identify the domain and item type.
3. Continue the conversation in place unless a specialist topic is required.
4. Dispatch repository work through `/ToWork`.
5. Queue durable facts, procedures, tasks, dates, and files for their destination writers.
6. Return one receipt with links and stable IDs.

This removes the need for Aki to remember which bot or topic owns a fact before saying it.

### One task model with projections

Keep a single structured task model. Render [tasks.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md), Telegram digests, calendar deadlines, and project summaries from it.

If a full migration is too disruptive, start by adding stable IDs and a parser for the current Markdown. Treat the two delegated backlog files as included sources instead of opaque summary tasks.

### One health view

Build a read-only command and viewer page that answers:

- Which Telegram topics are bound, running, stale, or waiting?
- Which jobs and review loops are active?
- Which repos and worktrees are dirty, ahead, behind, detached, or missing CI?
- Are achiMem and schoolMem clean, pushed, linted, and recently updated?
- Are Google profiles valid?
- Which systemd and Hermes jobs last succeeded?
- Which notifications are queued for retry?
- Which learning candidates await approval?

This page should use live state and timestamps. Do not copy the answer into [state.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/state.md) as another manual snapshot.

## Recommended order

### Phase 0. Prevent loss and exposure

1. Hold AIS-OS PR 10.
2. Review and back up the current achiMem changes.
3. Preserve sanitized copies of the four credential-bearing logs, then remove the secrets from retained logs.
4. Reauthenticate the four Google profiles.
5. Decide whether `personal/memories` belongs in Syncthing before changing its ignore list.

### Phase 1. Restore truthful status

1. Ship the Google auth health check and daily-brief test repair.
2. Make vault health inspect the whole working tree and upstream state.
3. Add the shared scheduler and delivery health view.
4. Correct stale statements in [connections.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/connections.md) and [state.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/state.md).

### Phase 2. Unify task and repository work

1. Complete AIS-OS issue 6 and achiCore issue 57 so every task view uses one renderer.
2. Add stable task IDs and include the two delegated backlog files.
3. Link repo tasks to GitHub issues and pull requests.
4. Add worktree lifecycle state to `/ToWork`.

### Phase 3. Replace the learning loop

1. Use [achiCore issue 83](https://github.com/achibukz/achiCore/issues/83) as the design ticket.
2. Fix global memory precedence through [issue 56](https://github.com/achibukz/achiCore/issues/56).
3. Remove the direct ungated writer.
4. Add typed candidates, conflict checks, destination writers, approvals, and audit receipts.
5. Route Telegram sessions into achiMem or schoolMem through the new queue.
6. Fix `/learn` to publish through canonical Skillshare and update scoped allowlists.
7. Re-enable transcript processing only after replay tests reject test identities, placeholders, injected instructions, duplicates, and stale facts.

### Phase 4. Reduce operational clutter

1. Classify and archive the 50-repository estate.
2. Review stale and finished worktrees without deleting dirty work.
3. Add the schoolMem linter.
4. Add a Files metadata catalog.
5. Remove or pin the duplicate Hermes daily briefing after choosing its owner.

## Astra handoff packet

Give Astra this file plus the live paths below. Ask it to verify the snapshot because sessions and pull requests may change after this audit.

Read first:

1. [astra-plan.md](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md)
2. [this audit](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-09-05-astra-cohesion-audit.md)
3. [achiCore hub design](http://100.106.210.38:8999/Code/GitHub/achiCore/docs/telegram-supergroup-hub-plan.md)
4. [achiCore engine guide](http://100.106.210.38:8999/Code/GitHub/achiCore/docs/engines.md)
5. [achiCore roadmap](http://100.106.210.38:8999/Code/GitHub/achiCore/docs/roadmap.md)
6. [AIS-OS tasks](http://100.106.210.38:8999/Code/GitHub/AIS-OS/tasks.md)
7. [AIS-OS state](http://100.106.210.38:8999/Code/GitHub/AIS-OS/state.md)
8. [AIS-OS connections](http://100.106.210.38:8999/Code/GitHub/AIS-OS/connections.md)
9. [achiMem index](http://100.106.210.38:8999/Documents/Obsidian/achiMem/wiki/index.md)
10. [schoolMem index](http://100.106.210.38:8999/Documents/Obsidian/schoolMem/wiki/index.md)

Inspect live state:

- `~/.local/state/achicore-hub/sessions.json`
- `~/.local/state/achicore-hub/topics.json`
- `~/.local/state/achicore-hub/topic_defs.json`
- `~/.local/state/achicore-hub/to_work_jobs.json`
- `~/.local/state/achicore-hub/review_loops.json`
- `~/.local/state/achicore-hub/topics/`
- `~/.local/state/achios/learning_ledger.jsonl`
- `~/.hermes/cron/jobs.json`
- `~/.hermes/cron/executions.db`
- `/home/achibukz/Documents/Files`
- `/home/achibukz/Documents/Obsidian/achiMem`
- `/home/achibukz/Documents/Obsidian/schoolMem`
- `/home/achibukz/Code/GitHub`

Use this prompt:

> Audit achiOS as one personal operating system. Focus on whether a Telegram message can become the correct task, calendar event, GitHub issue, durable memory, school note, procedure, file reference, scheduled action, and later retrieval without manual copying or lost context. Verify every claim in the 2026-09-05 cohesion audit against live state. Find repeated prompts, manual transitions, conflicting sources of truth, stale state, missing identifiers, dead jobs, unowned retries, unsafe write paths, and data that never becomes retrievable. Do not implement yet. Produce a proposed domain model, event schema, ownership table, migration order, acceptance tests, rollback points, and the smallest first release that closes one complete capture to action to recall loop.

Questions Astra should answer:

1. What is the smallest canonical item model that can link tasks, calendar events, GitHub work, knowledge, files, and notifications without forcing every store into one database?
2. Which current store owns each field, and which copies should become read-only projections?
3. How should Telegram routing preserve one conversation while still invoking specialist agents?
4. How should a candidate move from raw conversation to approval to destination write to later recall?
5. Which learning categories can be auto-approved, and which always require Aki?
6. How should current USER.md and MEMORY.md entries migrate without losing valid rules?
7. How should systemd and Hermes report into one execution ledger while retaining their separate strengths?
8. Which repository and worktree cleanup actions are safe now, and which need human review?
9. What replay corpus proves that the new loop rejects test identities, placeholders, prompt injection, transient tasks, and duplicates?
10. What live phone test proves that one Telegram request reaches its task, calendar, repository, knowledge, and reminder destinations with one receipt?

## Verification run

Read-only checks performed for this audit:

- Live `gh` inventory of 50 repositories, 47 open issues across three repos, and 4 open pull requests
- Current pull request, review, and GitHub Actions state for the active repositories
- achiCore Telegram bindings, sessions, jobs, review loops, and topic logs
- Google Workspace auth status for all four profiles
- `daily_brief.py --dry-run` and `tasks_digest.py --dry-run`
- Syncthing ignore and database status for `achi-files` and the vault folder
- HTTP status checks against normal and blocked viewer paths
- achiMem `python3 scripts/lint.py`
- schoolMem read-only wiki-link and duplicate-basename scan
- systemd timer and failed-unit inventory
- Hermes cron job and execution database inspection
- focused achiCore learning tests, 32 passed
- full AIS-OS tests, 275 passed and 44 failed

The GitHub inventory used the authenticated GitHub CLI through the agent-reach workflow. Its optional update command was unavailable on this host, so no update check completed.
