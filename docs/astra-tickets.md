# Astra implementation tickets

Published on 2026-09-05 after Aki approved the breakdown. Ten new issues and revisions to achiCore #128, achiCore #113 and AIS-OS #11. GitHub issue bodies are authoritative if later implementation changes their scope. AFK means unattended implementation under existing review and merge rules. T9 requires Aki for the live Flash pilot and activation. Frontend planning is a separate follow-up in the Astra plan.

## W0. [Make the full pytest command work unchanged in scoped Codex homes](https://github.com/achibukz/achiCore/issues/128)

Repository: `achibukz/achiCore`. Revised issue #128.

### Parent

[achiCore #83](https://github.com/achibukz/achiCore/issues/83), autonomous-learning design discussion.

### What to build

AFK implementation. Extend existing #128 with the reproduced September 5 failures. Provide one repository-owned test runner used by human shells, bound writer and reviewer worktrees, and CI. Update pyproject.toml, dependency discovery, affected tests, CI, test documentation and Luna's testing instructions. Preserve subprocess lifecycle coverage from #72.

The audit reproduced a learning_ledger collection error with a temporary HOME even using the main checkout's complete venv. Three worker venvs lack pytest and pytest-asyncio. CI installs these separately and clones a moving AIS-OS default branch. The global pre-push dispatcher resolves hooks beneath git-dir, which misses the shared repository hook in linked worktrees. Deliver a reviewed installation change for that dispatcher alongside the runner, preserving all other hooks.

Follow the agreed behavior and ownership in the [Astra plan](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md). Gemini 3.8 Flash must support the runtime path. A manual `/learn` command is never a prerequisite. Existing repository review and merge rules still apply.

### Acceptance criteria

- [ ] One documented command completes unchanged in a fresh bound Luna and Aea Codex worktree, a human shell and CI on Python 3.11 through 3.13. Record actual bound-run evidence before closure.
- [ ] Declare test dependencies, including pytest and pytest-asyncio, alongside runtime dependencies such as rich. Record Python, dependency-manifest and resolved AIS-OS revision in the test receipt; use a declared shared dependency revision in CI and local runs.
- [ ] Resolve repository and AIS-OS paths independently of scoped HOME. No caller-supplied HOME, PYTHONPATH, VIRTUAL_ENV or basetemp override is needed. Preserve scoped credentials, skills and subprocess permissions.
- [ ] Use a unique bounded per-run temporary root. Isolate test state from production and preserve the subprocess failures covered by #72 without skips or weaker assertions.
- [ ] The pre-push dispatcher reaches the repository test hook in both main and linked worktrees. The hook calls the same runner; no hook is disabled. Luna uses her provisioned checkout instead of fetching a second review clone.
- [ ] Environment setup leaves Git status clean, including any supported .venv symlink. Do not hide unrelated untracked files. Expose environment failure separately from a failing product assertion.
- [ ] Unit and integration tests cover fresh test dependencies, scoped HOME, sibling resolution, concurrent temp roots, main and linked-worktree hooks, environment artifacts and unchanged subprocess lifecycle cases.

### Blocked by

None. Can start immediately.

### Recommended model

`claude-opus-4-6-thinking`. Environment and hook isolation can pass in CI while failing only in a bound worker.

## W3. [Handle repositories without CI through an explicit review policy](https://github.com/achibukz/achiCore/issues/113)

Repository: `achibukz/achiCore`. Revised issue #113.

### Parent

[achiCore #83](https://github.com/achibukz/achiCore/issues/83), autonomous-learning design discussion.

### What to build

AFK implementation. Revise #113 so an intentionally CI-free repository reaches review promptly while a missing check on a repository that requires CI remains a failure to establish readiness. Add a persisted per-repository policy to src/github_client.py, src/review_handoff.py and the ToWork status path in src/bot.py.

The absence of .github/workflows does not establish that no CI exists. Repositories can require external providers or legacy commit statuses. Read branch protection or ruleset requirements when accessible, include check runs and commit statuses, and treat missing permissions or unknown policy as unresolved. An explicit local-review policy may permit handoff with a verified local test receipt and a visible CI-not-configured state.

Follow the agreed behavior and ownership in the [Astra plan](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md). Gemini 3.8 Flash must support the runtime path. A manual `/learn` command is never a prerequisite. Existing repository review and merge rules still apply.

### Acceptance criteria

- [ ] An explicitly configured repository without required CI bypasses the 45-minute no-check wait and reaches review only with the configured local verification evidence.
- [ ] Repositories with required CI wait for the required checks or statuses on the current head. Empty results, missing Actions files and API errors cannot turn those requirements green.
- [ ] External CI and legacy status contexts remain visible. Unknown requirements or insufficient API permissions produce an actionable policy state, not a silent bypass.
- [ ] The job card distinguishes CI not configured, required checks pending, failed checks and unknown policy. The same policy applies to direct review and ToWork handoff.
- [ ] Policy changes record their source and revision. A PR changing its own workflow files cannot authorize a downgrade of the repository review policy.
- [ ] Unit and integration tests cover explicit no-CI policy, local evidence missing, required checks not arrived, external statuses, failed checks, missing API permissions, changed head and attempted policy downgrade.

### Blocked by

- [achiCore #128](https://github.com/achibukz/achiCore/issues/128), local test evidence contract.

### Recommended model

`claude-opus-4-6-thinking`. A missing check must not weaken a review gate just because the local workflow directory is absent.

## W1. [Verify worker environments before dispatching autonomous jobs](https://github.com/achibukz/achiCore/issues/146)

Repository: `achibukz/achiCore`. Created issue #146.

### Parent

[achiCore #83](https://github.com/achibukz/achiCore/issues/83), autonomous-learning design discussion.

### What to build

AFK implementation. Extend src/worktrees.py and the ToWork start and review-handoff paths with a deterministic readiness probe using #128's runner. Provision writer and reviewer environments before a paid model turn. Expose failures on the existing job card with a retry action and a read-only worker inventory.

Use a separate environment per worktree, or an immutable cache keyed by Python and the dependency manifest. Never let one worker's dependency installation mutate another worker's running environment. Reuse existing provisioning rollback, /standby and merged-job cleanup rather than adding another deletion routine.

Follow the agreed behavior and ownership in the [Astra plan](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md). Gemini 3.8 Flash must support the runtime path. A manual `/learn` command is never a prerequisite. Existing repository review and merge rules still apply.

### Acceptance criteria

- [ ] A newly started job verifies the writer before implementation and the reviewer before review, using their actual engine environment and write boundary. Dependency or import failure dispatches no model.
- [ ] The probe checks interpreter, required imports, isolated temporary writes and child-process support. It does not run the full suite on every turn. Cache only against the exact environment and runner fingerprint.
- [ ] Setup leaves the checkout clean and records interpreter, runner hash, dependency manifest, AIS-OS revision and probe result in the job history.
- [ ] Retry rechecks the failed prerequisite and continues the pending stage. An unchanged failure reports one actionable state instead of consuming a model repair cycle.
- [ ] The inventory links worktrees to jobs and worker slots and reports dirty state, environment readiness and cached branch status. Unknown ownership and dirty historical work remain untouched.
- [ ] Concurrent provisioning cannot share a mutable environment or delete another attempt. Existing merged-job parking still releases both workers and keeps its current safeguards.
- [ ] Unit and integration tests cover missing pytest, bad sibling resolution, denied temp or child creation, cache invalidation, clean setup, concurrent workers, retry recovery and dirty orphan preservation.

### Blocked by

- [achiCore #128](https://github.com/achibukz/achiCore/issues/128), canonical scoped-home runner.

### Recommended model

`claude-opus-4-6-thinking`. Concurrent provisioning and environment caching can affect another worker without failing the creating job.

## W2. [Resume autonomous jobs from verified progress without repeating unchanged failures](https://github.com/achibukz/achiCore/issues/147)

Repository: `achibukz/achiCore`. Created issue #147.

### Parent

[achiCore #83](https://github.com/achibukz/achiCore/issues/83), autonomous-learning design discussion.

### What to build

AFK implementation. Change src/to_work.py, src/review_loop.py, src/review_handoff.py, src/github_client.py and the related bot handlers so recovery resumes the unfinished stage. Preserve versioned attempt and review receipts instead of clearing approval and replacing review history on every resume.

Classify environment, auth, transport, pending CI, missing CI, assertion failure, merge conflict and review findings before choosing the next actor. Only a code defect or actionable review finding dispatches a repair model. Supply the failed check's bounded diagnostic evidence, current commit and environment fingerprint. Reuse #113's no-CI policy and #143's conflict flow.

Follow the agreed behavior and ownership in the [Astra plan](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/astra-plan.md). Gemini 3.8 Flash must support the runtime path. A manual `/learn` command is never a prerequisite. Existing repository review and merge rules still apply.

### Acceptance criteria

- [ ] Resuming an unchanged approved PR revalidates its current checks, non-dismissed review and recorded head, base, issue-body and policy revisions. It returns to merge-ready with zero writer or reviewer calls when evidence remains valid.
- [ ] A changed head, base, specification or review invalidates the affected approval. Pending or temporarily unavailable GitHub state waits or parks without launching implementation. No automatic merge is added.
- [ ] An environment, auth or transport failure retains its reason and prerequisite. Use at most two bounded deterministic retries where retryable, then park. No-CI follows the explicitly configured repository policy from #113, never a fabricated green check.
- [ ] Persist a fingerprint of stage, head, environment and normalized failure. The same unresolved fingerprint cannot launch another model repair after resume unless relevant evidence changes or Aki explicitly requests another attempt.
- [ ] Preserve existing review-cycle, CI-repair and wall-clock limits across automatic recovery. A manual fresh attempt is explicit and retains earlier history. Unknown mergeability follows bounded read retries; real conflicts use #143.
- [ ] Store trusted command, cwd, commit, environment, exit status, log reference and test totals when available. Handoffs use these receipts; model-written success claims cannot replace them. Emit outcome and failure events for the learning pipeline.
- [ ] Record model calls, reported input/output tokens, test executions and wait time per stage. Mark unavailable usage as unknown. Prove fewer model calls with replayed unchanged-state failures; do not claim token savings from polling time.
- [ ] Unit and integration tests cover unchanged approval reuse, invalidated or dismissed review, auth outage, pending and missing CI, repeated environment failure, changed failure fingerprint, real assertion repair, merge conflict, restart and preserved attempt history.

### Blocked by

- [achiCore #146](https://github.com/achibukz/achiCore/issues/146)
- [achiCore #113](https://github.com/achibukz/achiCore/issues/113), explicit policy for repositories without CI.
- [achiCore #143](https://github.com/achibukz/achiCore/issues/143), bounded conflict resolution.

### Recommended model

`claude-opus-4-6-thinking`. Recovery must avoid duplicate paid work without reusing stale approval or weakening merge gates.

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

- [achiCore #147](https://github.com/achibukz/achiCore/issues/147), trusted test and job outcome receipts.

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

HITL implementation. Build a shared sanitized replay corpus and a release runner, starting alongside [AIS-OS #13](https://github.com/achibukz/AIS-OS/issues/13). Run real Gemini 3.8 Flash at high effort for both foreground interpretation and background review. Prove correction-to-later-action behavior, note capture and recall, linked ticket completion, procedure reuse and fault recovery. Mocked model tests or results on Astra cannot satisfy the real-model gate.

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

- [achiCore #147](https://github.com/achibukz/achiCore/issues/147), environment preflight and bounded recovery.

### Recommended model

`claude-opus-4-6-thinking`. Independent evaluation and rollback must catch failures the implementation can accidentally validate itself.

