# Astra implementation tickets

## Next Astra work, 2026-09-05

The reusable assisted-testing skill is installed locally and its source is in [PR #21](https://github.com/achibukz/AIS-OS/pull/21) for review. Its next real assisted-run acceptance is still open.

The worker implementation is deployed; the next workstream is the self-learning loop. Start with [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13), stable task and Calendar operations, and [achiCore #56](https://github.com/achibukz/achiCore/issues/56), persona and memory precedence. Then connect ordinary input through achiCore #148 and correction reuse through AIS-OS #14. Keep #155/#156 as parallel worker follow-ups, not a claim that every worker gate passed. The rest of T1 through T9 retains its declared dependency order.

Prepare AIS-OS #18's replay corpus while the early slices are built. Its final real Flash pilot still waits for its integrations. For tickets that need a human action, use [assisted-live-testing](http://100.106.210.38:8999/.config/skillshare/skills/assisted-live-testing/SKILL.md) and the [assisted testing guide](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/assisted-live-testing.md): the assistant prepares the test, guides one step at a time, checks the human's observations, saves a Markdown interaction record and posts a PR comment. This covers CLI/backend, API, device, browser and Telegram work. Automated-only tickets do not need a human gate.

Testing Grounds is reusable infrastructure, not a fresh or automatically ready run. Read the skill's Telegram reference for the isolated root, operator config and lifecycle checks. Downstream Calendar, database and vault destinations need separate isolation. See the [retrospective](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-09-05-assisted-testing-retrospective.md) for what our workflow test did and did not prove.


## 2026-09-05 deployment update

[achiCore #153](https://github.com/achibukz/achiCore/issues/153) is closed at Aki's request. [PR #154](https://github.com/achibukz/achiCore/pull/154) is merged as `bbb8fb73a6b1ba3632187df3b9ee45b31b4d3af1` and the main hub restarted on that code at 18:45 UTC. Telegram polling succeeded. Bindings and conversation IDs were preserved.

Remaining worker work is [#155](https://github.com/achibukz/achiCore/issues/155), separate conflict-repair attempts and Atlas repair/merge-queue status, and [#156](https://github.com/achibukz/achiCore/issues/156), invalidating cached probes when a worker virtualenv disappears or changes. Neither follow-up is implemented. Background preparation and automatic recovery retain their default-off production settings.

Aki's Flash staging run produced five completed jobs and one abandoned job. It did not establish six simultaneous jobs, all-engine coverage or the full fault-injection matrix. Closure and deployment do not mark those gates passed. See the [deployment and test record](http://100.106.210.38:8999/Code/GitHub/achiCore/docs/issue-153-deployment.md) for commands, counts, receipts and limits. Learning T1 through T9 and the control board remain separate work; this deployment does not establish learning completion.


Originally published on 2026-09-05. Aki subsequently consolidated worker reliability into achiCore #153. The learning ticket bodies below remain separate. GitHub issue bodies are authoritative if later implementation changes their scope. AFK means unattended implementation under existing review and merge rules. T9 requires Aki for the live Flash pilot and activation. Frontend planning is a separate follow-up in the Astra plan.

## R1. [Make six concurrent /ToWork jobs recover reliably and keep reviewed PRs ready to merge](https://github.com/achibukz/achiCore/issues/153)

Repository: `achibukz/achiCore`. R1 is closed and its implementation is deployed through PR #154. The assignment description below is historical; remaining defects are #155 and #156. Read the [full body](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-autonomous-loop-ticket.md) and [workflow audit](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-09-05-autonomous-loop-audit.md).

R1 owns the remaining acceptance criteria from #64, #65, #66, #67, #121, #122, #123, #143, #146 and #147. It adds six-job admission, recoverable operation ownership, early branch preparation and an isolated Telegram test hub. The original issues remain requirement references, with organizational closure rather than a claim that their code is complete.

W0, #128, shipped in PR #150. W3, #113, shipped in PR #151. Follow-up PR #152 is merged too. Preserve and verify these implementations instead of repeating the old environment and CI-policy designs.

R1's internal order is worker reservation and preflight, durable recovery, Claude stream/write/fallback support, background branch preparation, worker runbooks and staging acceptance. The source issues are not hard blockers on starting R1. #25 remains a separate model rollout after R1.

## T1. [Fulfill task and Calendar intents with stable IDs and durable receipts](https://github.com/achibukz/AIS-OS/issues/13)

Repository: `achibukz/AIS-OS`. Created issue #13.

### Parent

[achiCore #83](https://github.com/achibukz/achiCore/issues/83), autonomous-learning design discussion.

### What to build

AFK implementation. Add `scripts/cohesion.py` with a versioned submit, context and capabilities contract. Start with structured task and Calendar intents. Reuse `scripts/gcal_add.py` and the existing task parser. Add a local SQLite record for each source, item, preference revision and destination operation. A CLI submission must produce the chosen task or event and an inspectable receipt. It must also work with injected fixture transports. This complete command-line path becomes the contract Telegram uses.

Keep tasks.md as the task owner and Google Calendar as the appointment owner. Include docs/tasks-systems-engineering.md and docs/tasks-asa-research.md explicitly. Seed editable preferences from Aki's examples, social plans to Calendar only, quick tasks and coding tickets to tasks only, school deadlines to both. A date alone does not select both.

Follow the agreed behavior and ownership in the [Astra plan](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md). Gemini 3.8 Flash must support the runtime path. A manual `/learn` command is never a prerequisite. Existing repository review and merge rules still apply.

### Acceptance criteria

- [ ] Calendar-only creates no task line; tasks-only creates no event; both creates linked destinations. The receipt identifies applied and pending operations separately.
- [ ] Task IDs survive renaming, moving to Done and date changes. Included backlog tasks render once and internal IDs do not leak into the task card.
- [ ] Calendar entries retain profile, calendar ID, stable event ID and an opaque private item property. Support timed appointments and all-day deadlines in the configured timezone.
- [ ] Redelivery and a timeout after Calendar accepts an insert create at most one event. A partial both operation retries only the unfinished destination.
- [ ] Task writes compare a fresh content hash and preserve unrelated edits. Do not modify an event with unknown ownership or changed version.
- [ ] Expose schema-versioned submit, context and capabilities responses without importing Telegram. Reserve durable source IDs before side effects.
- [ ] Unit and integration tests cover all three placements, renamed tasks, included backlogs, timed and all-day dates, duplicate submission, ambiguous timeout, partial success and concurrent human edits.

### Blocked by

None. Can start immediately.

### Recommended model

`claude-opus-4-6-thinking`. Cross-store retries and concurrent edits can look correct while duplicating or losing real work.

## T2. [Connect ordinary Telegram requests to automatic intent handling and current preferences](https://github.com/achibukz/achiCore/issues/148)

Repository: `achibukz/achiCore`. Created issue #148.

### Parent

[achiCore #83](https://github.com/achibukz/achiCore/issues/83), autonomous-learning design discussion.

### What to build

AFK implementation. Integrate the [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13) contract into `src/bot.py` and the common direct and delegated turn path. Record authorized raw Telegram input before prompt assembly, including edit revisions, and bind structured proposals to that source. Read current capabilities and scoped preferences on every turn, including resumed conversations. The normal foreground model proposes an action; the trusted parent handler validates and submits it through the AIS-OS writer. Bound model subprocesses keep their Landlock restrictions and receive no generic privileged file or command endpoint. Show a short destination receipt in the originating topic.

Capture result, failure and cancellation events with run, attempt, topic, workspace and existing job IDs. Assistant assertions and observed tool outcomes must keep distinct roles. Failed Telegram delivery must not erase completed evidence. Unsupported capabilities produce a truthful pending or unavailable result.

Follow the agreed behavior and ownership in the [Astra plan](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md). Gemini 3.8 Flash must support the runtime path. A manual `/learn` command is never a prerequisite. Existing repository review and merge rules still apply.

### Acceptance criteria

- [ ] A natural meetup, quick-task or school-deadline request reaches the expected [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13) destinations from its current topic with no manual learning or routing command.
- [ ] Antigravity, Codex and Claude Code receive current scoped preference context on both new and warm turns, without changing raw source text.
- [ ] The source envelope comes from the handler. A model cannot label its own output as a user correction or replace the source event ID.
- [ ] Redelivered messages, edited messages, retried attempts and delegated wrappers retain distinct revisions and one original source lineage.
- [ ] Invalid proposal JSON, unsupported actions and missing source references cause no destination write and return a usable failure or clarification.
- [ ] Provide a repeatable Gemini 3.8 Flash demonstration script using synthetic requests; final real-model activation is T9.
- [ ] Unit and integration tests cover the three placements, each engine on warm and new turns, malformed proposals, redelivery, edits, delegation, cancellation and failed receipt delivery.

### Blocked by

- [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13)
- [achiCore #56](https://github.com/achibukz/achiCore/issues/56), persona and memory precedence.

### Recommended model

`claude-opus-4-6-thinking`. Source identity and resumed prompt handling affect every action and can fail only in particular engine paths.

## T3. [Learn destination preferences from corrections and apply them to later requests](https://github.com/achibukz/AIS-OS/issues/14)

Repository: `achibukz/AIS-OS`. Created issue #14.

### Parent

[achiCore #83](https://github.com/achibukz/achiCore/issues/83), autonomous-learning design discussion.

### What to build

AFK implementation. Extend the cohesion submit and context contract so an ordinary correction fixes the referenced item and creates a versioned, scoped preference. Later matching requests retrieve and use that revision automatically. Implement preference conflict resolution and a persistent background consolidation worker around `scripts/memory_gate.py` and `scripts/learning_ledger.py`.

Aki's initial examples are seeds. They must evolve from actual corrections, including where notes should go. Record the difference between explicit category rules, learned narrow generalizations and this-time-only exceptions. Repetition of the agent's own output is not additional evidence. Retain failures and corrections as well as successes.

The reviewer uses Gemini 3.8 Flash with a proved inference-only transport. The installed agy JSON-schema flag alone does not deny tools. Resolve and test that transport before enabling review; leave evidence queued if it is unavailable.

Follow the agreed behavior and ownership in the [Astra plan](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md). Gemini 3.8 Flash must support the runtime path. A manual `/learn` command is never a prerequisite. Existing repository review and merge rules still apply.

### Acceptance criteria

- [ ] After a Calendar placement, "no, just tasks.md" repairs the owned operation and changes a later matching request without `/learn` or `/new`.
- [ ] An explicit this-time-only correction changes only its item. From-now-on wording persists the category rule. Ambiguous broader scope preserves the item correction and asks one narrow question.
- [ ] Current explicit instructions outrank learned preferences. Specific scopes outrank broad scopes. Same-scope conflicts retain both sources and require resolution.
- [ ] An unwanted Calendar entry removed by a correction stays suppressed during reconciliation. Changed or unowned events produce a conflict instead of deletion.
- [ ] The persistent worker consumes new source events only, wakes every five minutes, makes zero calls when idle, and reserves at most 24 calls per Manila day with retries included.
- [ ] Enforce one classifier at a time, 6,000 total input tokens, 1,000 output tokens, 90 seconds and at most one retry. Use no premium fallback; keep deferred evidence after budget exhaustion.
- [ ] Classifier output cannot write files, execute tools or approve itself. Its sources, claims, scope and proposed changes pass deterministic validation. Exclude recalled text, generated notes, mocks and placeholders as independent evidence.
- [ ] Unit and integration tests cover correction then later reuse, initial seeds, one-time exceptions, explicit category changes, same-scope conflicts, suppression, forged provenance, source echoes, restart recovery and daily-budget races.

### Blocked by

- [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13)
- [achiCore #148](https://github.com/achibukz/achiCore/issues/148)

### Recommended model

`claude-opus-4-6-thinking`. Learning scope, provenance and repair semantics can reinforce an error while passing simple happy-path tests.

## T4. [Save Telegram notes automatically and promote sourced updates to allowed achiMem pages](https://github.com/achibukz/AIS-OS/issues/15)

Repository: `achibukz/AIS-OS`. Created issue #15.

### Parent

[achiCore #83](https://github.com/achibukz/achiCore/issues/83), autonomous-learning design discussion.

### What to build

AFK implementation. Add note and knowledge writers behind the existing cohesion capabilities contract. A normal "take note" request must save a sourced record under achiMem raw/sessions or schoolMem inbox, return its path and make it available to scoped recall. Extend `scripts/achimem_capture.py`, `scripts/achimem_recall.py` and the vault writer through shared helpers rather than introducing an independent memory store.

Enable automatic small-section updates on achiMem's achi-os, achi-core and achibuntu system pages, append completed-work rows to timeline.md, and append Tooling / workflow rows to decisions.md with original decision links. Prepare and review the vault automation contract and section markers before enabling those five targets. Other wiki destinations keep their existing ingest rules. The parent handler authorizes only typed note or section operations against configured destinations; model-selected arbitrary paths cannot cross a topic write boundary.

Follow the agreed behavior and ownership in the [Astra plan](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md). Gemini 3.8 Flash must support the runtime path. A manual `/learn` command is never a prerequisite. Existing repository review and merge rules still apply.

### Acceptance criteria

- [ ] A note spoken in any bound topic reaches the appropriate permitted vault destination and is retrievable through context with its source and domain.
- [ ] Personal facts require direct user evidence or cited document evidence. Inferences remain labelled and cannot become confirmed personal facts.
- [ ] The five-page allowlist resolves exact paths and sections. Unknown paths, traversal, symlinks to other targets and attempted allowlist expansion fail before writing.
- [ ] A concurrent page edit or contradiction queues a conflict. Unrelated dirty files are neither committed, stashed nor discarded.
- [ ] After a permitted patch, update provenance and log.md, regenerate the index when required, and run the existing linter. Expose applied, committed and pushed states separately.
- [ ] Repeated capture from a Claude hook and Telegram shares source identity where available; uncertain legacy matches do not manufacture independent confirmations.
- [ ] Unit and integration tests cover note capture and recall, school routing, each allowed page mutation, forbidden targets, duplicate capture, source rejection, page conflicts, failed lint and failed Git push.

### Blocked by

- [achiCore #148](https://github.com/achibukz/achiCore/issues/148)
- [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14)

### Recommended model

`claude-opus-4-6-thinking`. Automatic personal-knowledge changes need reliable source checks and must preserve concurrent vault work.

## T6. [Reconcile completed GitHub work with linked active tasks and the evening debrief](https://github.com/achibukz/AIS-OS/issues/11)

Repository: `achibukz/AIS-OS`. Revised issue #11.

### Parent

[achiCore #83](https://github.com/achibukz/achiCore/issues/83), autonomous-learning design discussion.

### What to build

AFK implementation. Implement `scripts/sync_completed_tickets.py` against stable links from [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13) and call the shared completion renderer from `scripts/evening_debrief.py`. A completed linked issue moves its existing task to Done once. A merged PR can complete a task directly linked to that PR; issue-linked tasks follow the issue's completion state.

Keep configurable repositories with achibukz/achiCore, achibukz/AIS-OS and achibukz/career-ops as the existing defaults. Preserve --date YYYY-MM-DD, defaulting to today in Asia/Manila, and --dry-run. Add persistent poll cursors and a bounded overlap so downtime does not lose completions at midnight. Keep completion summaries distinct from active tasks. Emit source-backed outcome evidence for learning.

Follow the agreed behavior and ownership in the [Astra plan](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md). Gemini 3.8 Flash must support the runtime path. A manual `/learn` command is never a prerequisite. Existing repository review and merge rules still apply.

### Acceptance criteria

- [ ] A completed linked issue updates the original active task, preserves its stable ID, and appears once in the debrief.
- [ ] Issue closure plus its merged PR produces one work-item completion. Renamed titles do not break matching.
- [ ] Closed-as-not-planned issues, unmerged closed PRs, unrelated PRs and partial work do not mark an active task complete.
- [ ] An unlinked completion can appear in the debrief without inventing or completing an unrelated task. Distinct issue and PR number namespaces do not collide.
- [ ] Reopened issues reconcile their explicitly linked task state. An incompatible manual task edit becomes a conflict rather than being overwritten.
- [ ] Dry-run changes neither destinations nor poll cursors. Cursor recovery includes work completed during downtime, with dates interpreted in Asia/Manila.
- [ ] Unit and integration tests cover active-to-Done updates, duplicate issue/PR evidence, title changes, not-planned closure, unmerged and unrelated PRs, reopen, conflicting edits, midnight boundaries and missed polls.

### Blocked by

- [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13)

### Recommended model

`claude-opus-4-6-thinking`. Completion and reopen events must reconcile existing work without treating every closed GitHub object as success.

## T5. [Use verified learning on warm turns and retire direct global-memory writes](https://github.com/achibukz/achiCore/issues/149)

Repository: `achibukz/achiCore`. Created issue #149.

### Parent

[achiCore #83](https://github.com/achibukz/achiCore/issues/83), autonomous-learning design discussion.

### What to build

AFK implementation. Complete the common learning path in `src/bot.py`, `src/background_review.py`, `src/memory_engine.py` and engine-home integration. Replace the old turn-counter reviewer and direct manage_memory mutation instructions with submissions through the governed cohesion writer. Preserve optional legacy command entry points as submissions, but keep all automatic triggers in ordinary work.

Build at most 1,500 tokens of current domain-scoped facts, preferences and verified procedures before each relevant action. Keep source references and revisions. Link observed outcomes back to the revisions actually used. Retain native-client memory disabling in bound turns. Migrate valid global memory entries with provenance and quarantine ambiguous historical entries.

Follow the agreed behavior and ownership in the [Astra plan](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md). Gemini 3.8 Flash must support the runtime path. A manual `/learn` command is never a prerequisite. Existing repository review and merge rules still apply.

### Acceptance criteria

- [ ] Every supported engine sees a newly accepted fact or preference in a warm conversation without `/new`; the source event still contains only the original user text.
- [ ] All learning mutations use the policy writer. The old reviewer cannot run beside the new worker, and memory-full handling never evicts the oldest entry automatically.
- [ ] Recalled records are filtered by domain, repository, applicability, revocation and freshness before ranking. Cross-domain access requires an explicit task connection.
- [ ] A procedure is eligible after one observed success plus relevant checks. A model statement that work succeeded cannot verify it.
- [ ] Record retrieved, selected, applied and corrected separately. A failed verified procedure is suspended or narrowed according to its actual prerequisites.
- [ ] Legacy imports are idempotent and preserve originals. Ineligible old TGDB content remains quarantined. Rollback can disable new recall without erasing captured evidence.
- [ ] Unit and integration tests cover warm recall across engines, token bounds, scope, expired and revoked facts, false successes, direct-write refusal, full memory, legacy import and worker cutover.

### Blocked by

- [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14)
- [AIS-OS #15](https://github.com/achibukz/AIS-OS/issues/15)
- [achiCore #56](https://github.com/achibukz/achiCore/issues/56), precedence and memory cleanup.

- [achiCore #153](https://github.com/achibukz/achiCore/issues/153), trusted test and job outcome receipts.

### Recommended model

`claude-opus-4-6-thinking`. Shared-memory cutover and outcome attribution need stronger checks than confirming that a prompt contains a note.

## T7. [Deliver learning receipts after outages and report current integration health](https://github.com/achibukz/AIS-OS/issues/16)

Repository: `achibukz/AIS-OS`. Created issue #16.

### Parent

[achiCore #83](https://github.com/achibukz/achiCore/issues/83), autonomous-learning design discussion.

### What to build

AFK implementation. Connect the coordination outbox to `scripts/telegram_notify.py` and add a compact learning section to `scripts/evening_debrief.py`. Failed receipt delivery must survive a process restart. After recovery, deliver one incident summary with the final state. Include revised preferences, saved notes, useful procedures, completed work, conflicts and deferred review counts in the daily digest.

Add a read-only health command for queue age, model budget, destination application, Calendar auth, vault application/commit/push and notification delivery. Reuse the current google_auth_health.py implementation. An inbox-only sync success must not report the whole vault backed up.

Follow the agreed behavior and ownership in the [Astra plan](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md). Gemini 3.8 Flash must support the runtime path. A manual `/learn` command is never a prerequisite. Existing repository review and merge rules still apply.

### Acceptance criteria

- [ ] Network failure followed by worker restart and recovery delivers the pending receipt with its original operation identity.
- [ ] Retries are bounded and honor retryable versus permanent failures. Telegram delivery is at least once: an accepted send with a lost acknowledgement may duplicate a receipt. Keep its operation ID stable, reconcile a known message ID and never repeat the underlying action. Persistent failures do not alert on every attempt.
- [ ] Healthy routine learning appears in the daily digest; conflicts and failed requested actions produce actionable alerts.
- [ ] The digest distinguishes captured, accepted, applied, backed up, retrieved and corrected. Deferred reviews do not count as learned.
- [ ] Health reports cached versus live timestamps, oldest pending age, remaining daily review calls and separate whole-vault dirty/upstream status.
- [ ] Existing digest formatting and unaffected sections retain their contract. No second daily briefing schedule is introduced.
- [ ] Unit and integration tests cover transport outage and recovery, duplicate deliveries, permanent failures, idle silence, budget deferral, stale health, dirty vault with clean inbox and digest preservation.

### Blocked by

- [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14)
- [AIS-OS #15](https://github.com/achibukz/AIS-OS/issues/15)
- [AIS-OS #11](https://github.com/achibukz/AIS-OS/issues/11), revised completion reconciliation.

### Recommended model

`claude-opus-4-6-thinking`. Retry and status semantics must stay correct when the notification channel fails with the action it reports.

## T8. [Turn verified procedures into reviewed skills and publish them to allowed agents](https://github.com/achibukz/AIS-OS/issues/17)

Repository: `achibukz/AIS-OS`. Created issue #17.

### Parent

[achiCore #83](https://github.com/achibukz/achiCore/issues/83), autonomous-learning design discussion.

### What to build

AFK implementation. Detect reusable procedures from accepted execution evidence and automatically prepare a skill change in a branch and pull request. Store first-party learned skills under `skills/learned/` in AIS-OS, with source references, prerequisites, relevant verification and repository/tool-version scope. The current Skillshare source directory has no Git repository, so a PR cannot target it directly.

After the PR is reviewed and merged through the existing workflow, a trusted publisher installs only approved skills to the canonical Skillshare directory. Update a persona allowlist through a reviewed achiCore change when needed and verify the permitted Antigravity, Codex and Claude Code discovery paths. Do not report a skill usable while its allowlist change is pending.

Follow the agreed behavior and ownership in the [Astra plan](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md). Gemini 3.8 Flash must support the runtime path. A manual `/learn` command is never a prerequisite. Existing repository review and merge rules still apply.

### Acceptance criteria

- [ ] One recorded successful execution with relevant checks can produce a scoped reusable procedure and a reviewable PR without a manual `/learn` request.
- [ ] Only reviewed merged revisions become installed shared skills. A candidate cannot change shared rules, permissions or its own publishing allowlist.
- [ ] The PR includes source evidence, scope, verification commands and an expected output. Repeated evidence updates the existing proposal rather than opening duplicates.
- [ ] Published skill content matches the reviewed source hash. Persona allowlists control discovery in each engine home; unrelated personas do not gain the skill.
- [ ] A failed prerequisite, installation or verification keeps the skill unavailable with a clear status. Revocation prevents future discovery of that revision.
- [ ] Personal content and raw conversations are not copied into public skill PRs. Use sanitized examples and private source references where needed.
- [ ] Unit and integration tests cover evidence-to-PR preparation, duplicate proposals, unreviewed publication refusal, reviewed-hash validation, each engine allowlist, revoked skills and failed installation.

### Blocked by

- [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14)
- [achiCore #149](https://github.com/achibukz/achiCore/issues/149)

### Recommended model

`claude-opus-4-6-thinking`. Publishing executable guidance across protected configuration paths requires verified review state and exact source identity.

## T9. [Prove the autonomous loop with Gemini 3.8 Flash and a recoverable Telegram pilot](https://github.com/achibukz/AIS-OS/issues/18)

Repository: `achibukz/AIS-OS`. Created issue #18.

### Parent

[achiCore #83](https://github.com/achibukz/achiCore/issues/83), autonomous-learning design discussion.

### What to build

Unattended replay implementation followed by assisted feature live testing. Build a shared sanitized replay corpus and a release runner, starting alongside [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13). Run real Gemini 3.8 Flash at high effort for both foreground interpretation and background review. Prove correction-to-later-action behavior, note capture and recall, linked ticket completion, procedure reuse and fault recovery. Mocked model tests or results on Astra cannot satisfy the real-model gate.

Ship a consented phone pilot with synthetic notes, Calendar items and linked test tickets. Enable capture-only, shadow proposals and restricted automatic writes in stages. Keep independent switches for capture, classification, actions, wiki writes and skill publication. Record actual results without claiming the existing unit suite verifies unimplemented behavior.

Follow the agreed behavior and ownership in the [Astra plan](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md). Gemini 3.8 Flash must support the runtime path. A manual `/learn` command is never a prerequisite. Existing repository review and merge rules still apply.

### Acceptance criteria

- [ ] A held-out set of at least 40 requests covers all three seed placements, paraphrases, natural corrections, one-time exceptions, notes, scope conflicts and unsupported inferences.
- [ ] Gemini 3.8 Flash passes every explicit placement and correction case and at least 90 percent of held-out paraphrases. Record actual model, prompt revision, token use, latency and failures.
- [ ] No missing-source response, invented target, invalid JSON or unsafe proposal causes a write. Any unauthorized destination change or invented personal fact blocks release regardless of aggregate score.
- [ ] A live Flash foreground/background pilot demonstrates normal request, correction, later matching request, saved-note warm recall, linked ticket completion and verified procedure reuse without `/learn` or `/new`.
- [ ] Crash after destination acceptance and before acknowledgement, exhaust the model budget, revoke a preference and fail Calendar auth. The system preserves evidence and resumes or reports the exact conflict.
- [ ] Restore a SQLite backup in isolation and verify outstanding operation identity and learning revisions. Pilot cleanup touches only recorded pilot-owned artifacts.
- [ ] After at least seven days and ten eligible real reuse opportunities, report retrieval, selection, applied outcomes and corrections separately. Pause an affected rule on a harmful result; time alone does not qualify release.
- [ ] Unit and integration tests cover replay isolation, separate expected outcomes, model assertions, release thresholds, source rejection, crash recovery, budget exhaustion, revocation, backup restoration and owned-artifact cleanup.

### Blocked by

- [achiCore #148](https://github.com/achibukz/achiCore/issues/148)
- [AIS-OS #14](https://github.com/achibukz/AIS-OS/issues/14)
- [AIS-OS #15](https://github.com/achibukz/AIS-OS/issues/15)
- [achiCore #149](https://github.com/achibukz/achiCore/issues/149)
- [AIS-OS #11](https://github.com/achibukz/AIS-OS/issues/11), revised completion reconciliation.
- [AIS-OS #16](https://github.com/achibukz/AIS-OS/issues/16)
- [AIS-OS #17](https://github.com/achibukz/AIS-OS/issues/17)

- [achiCore #153](https://github.com/achibukz/achiCore/issues/153), environment preflight and bounded recovery.

### Recommended model

`claude-opus-4-6-thinking`. Independent evaluation and rollback must catch failures the implementation can accidentally validate itself.

