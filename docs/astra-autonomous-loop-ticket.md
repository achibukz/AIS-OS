# Make six concurrent /ToWork jobs recover reliably and keep reviewed PRs ready to merge

## 2026-09-05 deployment update

[achiCore #153](https://github.com/achibukz/achiCore/issues/153) is closed at Aki's request. [PR #154](https://github.com/achibukz/achiCore/pull/154) is merged as `bbb8fb73a6b1ba3632187df3b9ee45b31b4d3af1` and the main hub restarted on that code at 18:45 UTC. Telegram polling succeeded. Bindings and conversation IDs were preserved.

Remaining worker work is [#155](https://github.com/achibukz/achiCore/issues/155), separate conflict-repair attempts and Atlas repair/merge-queue status, and [#156](https://github.com/achibukz/achiCore/issues/156), invalidating cached probes when a worker virtualenv disappears or changes. Neither follow-up is implemented. Background preparation and automatic recovery retain their default-off production settings.

Aki's Flash staging run produced five completed jobs and one abandoned job. It did not establish six simultaneous jobs, all-engine coverage or the full fault-injection matrix. Closure and deployment do not mark those gates passed. See the [deployment and test record](http://100.106.210.38:8999/Code/GitHub/achiCore/docs/issue-153-deployment.md) for commands, counts, receipts and limits. Learning T1 through T9 and the control board remain separate work; this deployment does not establish learning completion.

The original brief or audit below is retained as a historical source. Its present-tense observations refer to its original checkout.


Published as [achiCore #153](https://github.com/achibukz/achiCore/issues/153). GitHub is authoritative after later scope updates. The source tickets below are consolidated here, not completed by this planning change.

## Outcome

Aki can start six independent tickets, leave them running, and return to reviewed pull requests. Merging one PR triggers background preparation of the remaining affected branches. Routine environment, CI, provider and transport failures recover without another implementation prompt or a manual SSH repair. Aki keeps the final merge decision. A changed reviewed commit returns through verification and review before its Merge action becomes available again.

This is one implementation assignment for one executor session, with ordered stages and one completion report. The executor may use several commits on its ticket branch. Runtime concurrency between Aea/Luna job pairs is required; executor subagents are not. Complete the audit, implementation, regression tests and staging verification within this assignment. Do not stop after producing another plan.

## Scope consolidated here

| Previous ticket | Responsibility now owned here |
|---|---|
| achiCore #64 | Verify existing worker worktrees and repair remaining allocation, ownership or rollback defects |
| achiCore #65 | Verify existing mixins and normalize unattended worker instructions |
| achiCore #66 | Verify existing standby and preserve clean, merged-only release |
| achiCore #67 | Verify paired review and exact commit handoff |
| achiCore #121 | Complete Claude Code event translation and redacted diagnostics |
| achiCore #122 | Complete Claude Code write boundaries, identity and cancellation |
| achiCore #123 | Complete Claude Code recovery and configured quota fallback |
| achiCore #143 | Resolve conflicts, extending the manual button with background preparation |
| achiCore #146 | Prepare and probe the actual worker environments before paid dispatch |
| achiCore #147 | Resume verified progress, preserve receipts and stop repeated unchanged failures |

The original issue bodies remain requirement references. Every original acceptance criterion must appear in the final coverage matrix as verified, implemented here or explicitly replaced by a requirement below. Organizational closure of an original ticket is not evidence of implementation. Their internal dependency edges become the implementation order inside this ticket. Recheck original prerequisites against shipped code rather than requiring those archived tickets to reopen or dispatch separately.

Already shipped and to preserve: #128 through PR #150, the canonical test runner, and #113 through PR #151, explicit repository CI policy. PR #152 was also merged at Aki's request during consolidation; `a1c5d9e` adds early `ci_undeclared` refusal when the probe finds no CI. Verify their remaining runtime gaps. Do not rebuild either from its historical defect description. AIS-OS now declares local review on its base branch and names its own interpreter in the command, at commit `efe250d` observed during this audit.

Self-learning, TGDB knowledge formation, task/Calendar reconciliation, the control board, broad administrative automation and changing Luna's default model remain separate. #25 retains its model rollout scope and depends on this ticket's Claude support. #56 retains global-memory cleanup and precedence; preserve that interface while fixing worker instructions. Emit job outcome receipts for the learning work without depending on its database or classifier being implemented.

## Starting evidence

The audit began at achiCore `4ff50b5786bca1fc111bab2378835b1294063877`. The starting branch is now `a1c5d9e33293d0e73624746e96a7179fe8d4a8d5` after PR #152. Recheck HEAD before editing. Read the [workflow audit](http://100.106.210.38:8999/Code/GitHub/AIS-OS/docs/2026-09-05-autonomous-loop-audit.md), [engine guide](http://100.106.210.38:8999/Code/GitHub/achiCore/docs/engines.md) and [hub architecture](http://100.106.210.38:8999/Code/GitHub/achiCore/docs/telegram-supergroup-hub-plan.md).

Source shows no worker-pair reservation between selection and asynchronous provisioning, approval/history loss on resume, generic readiness errors returning to implementation, branch synchronization starting only on a Merge tap, and no Claude quota classifier or possible-write tracker. These are source findings, not a six-job production reproduction. The existing 488 focused tests passed in 34.12 seconds. They do not establish the requested concurrency or live Telegram behavior.

## 1. Reserve workers and prepare their environments

Reuse the existing job, topic, worktree and delegation stores. Reserve the issue and both worker slots before yielding to credential checks, fetches or provisioning. Reservation ownership must survive the awaits and have an explicit release path. Concurrent starts for different issues cannot choose or roll back the same pair. Failed provisioning removes only artifacts created by that reservation. Preserve pre-existing and dirty worktrees.

Support six active jobs with configurable bounded model and test-process concurrency. A job waiting for GitHub, a cooldown or human input releases its execution slot. Independent workspaces can progress together; only operations sharing a worktree or shared Git metadata serialize. Do not lock a whole repository for the duration of every model turn. Serialize remote merges per repository and recheck state after acquiring ownership. A stopped or restarted owner cannot later mutate a reclaimed job. Use durable operation identities and verify child-process exit before handing over a worktree.

Provision an independent environment per worktree or an immutable dependency cache. Probe writer and reviewer under their actual engine environment, identity and write boundary before their first paid turn. Check the interpreter, declared imports, AIS-OS resolution, temporary writes, child creation and exit observation. Key reuse by runner, dependency manifest, interpreter and sibling revision. Reuse `scripts/run_tests.py`; the probe is cheaper than the full suite. Environment failure names the missing prerequisite and dispatches no repair model.

Completion evidence: simultaneous-start tests with forced scheduling barriers, rollback and restart tests, six distinct pairs, clean environment creation, and probes in actual scoped environments.

## 2. Make recovery resume the unfinished stage

Persist the stage, attempt history, observed head and base SHAs, specification and policy revisions, reviewer identity and review validity, command receipts, and pending operations. Keep historical review cycles when a new attempt begins. Resume revalidates evidence before deciding whether implementation, review, verification or a deterministic read is needed.

Classify environment, authentication, transport, pending CI, missing CI policy, assertion failure, review findings, quota and merge conflicts separately. An unchanged approved PR with valid evidence reaches merge-ready with zero new writer or reviewer calls. A transient lookup error cannot become the full implementation prompt. Use at most two bounded retries for transient reads, then retain one actionable incident. Retry when a relevant prerequisite changes; repeated Resume on the same unresolved failure fingerprint cannot consume another model repair.

Keep the existing review and time bounds through automatic recovery: three reviewer cycles, two CI repairs per cycle, six hours for confirmation, twelve hours for a review loop and the existing 24-hour job-attempt bound. A fresh user-requested attempt retains earlier history. Approval-ready work must retain its receipts across expiry and restart; later revalidation must not require implementing it again. DO NOT SHIP continues to require Aki's decision. Nits-only remains a separate review outcome and cannot fabricate a formal approval.

Preserve #113's policy from the base branch, required checks and legacy statuses. A 403 means unknown requirements. Missing policy is a setup problem with a concrete remedy, not an invitation to generate code. A PR cannot downgrade its own gate. Cover external providers that report only on PRs: no checks on the base head does not prove that no provider exists. PR #152's absence probe must not prematurely stop a repository with a configured external provider or a declared required context. Describe missing observations honestly and retain bounded discovery or an explicit repository declaration where needed. Cache local verification only with matching source, environment, runner and policy evidence. Failed local tests and environment setup are different states.

Trusted receipts record command, cwd, head, dependency/environment identity, exit code and bounded redacted output reference. Parse test totals from observed output. Distinguish requested, running, applied, verified and reported operations so a lost acknowledgement cannot repeat the underlying side effect. Outcome events carry stable IDs for later learning integration.

Completion evidence: crash at each dispatch/result boundary, restart recovery, identical-failure replay, dismissed approvals, changed heads/specifications/policies, CI outages and explicit no-CI behavior. Record model calls separately from polling and mark missing token usage unknown.

## 3. Complete Claude Code support and job-level quota recovery

Preserve fresh/resumed invocation, explicit model and effort, scoped homes, disabled native memory and fallback, and the denied Agent tool. Complete the shared event mapping for partial/final text, tools and results, hooks/plugins/MCP lifecycle, permission failures, rate limits, usage, terminal results and malformed or unknown records. Telegram stays concise and avoids duplicate finals. Verbose logs retain supported diagnostic payloads after secret redaction. Do not collect hidden reasoning.

Apply the existing Landlock boundary and identity rules to every bound Claude invocation. Preserve the writable scoped session home while protecting the operator's real Claude configuration. Record possible writes from tool and shell starts before completion. Cancellation terminates and awaits the whole process group; reuse an interrupted conversation only when its state is verified safe. Drain stdout and stderr concurrently.

Use the shared stall and fallback mechanisms. Recognize quota, overload and model unavailability from captured provider evidence. Scope cooldowns to the affected account or model as reported. Several jobs sharing an exhausted account must not each retry every model in that account. Honor configured fallback order and effort, and start a fresh target-engine conversation. Authentication failures and content-policy refusals are not quota fallbacks. Keep cooldown state recoverable across daemon restarts, with expiry and account identity checks.

Before any possible write, safe fallback may retry the turn. After a possible write, do not replay the original prompt. The job owner first verifies process exit, current worktree changes, commits and recorded external operations. It can continue with an eligible fallback only from that inspected checkpoint, using remaining work and preserved evidence. An unknown external side effect parks for resolution. Retain this distinction even if it means a genuinely ambiguous job needs Aki. If all permitted providers are cooling, wait until the earliest eligible retry without occupying a model slot or repeatedly notifying.

Completion evidence: original #121/#122/#123 acceptance matrix, large stdout/stderr, first-write races, account-wide quota across six jobs, exact fallback effort, refusal handling, cancellation and checkpoint continuation without duplicated writes or external actions.

## 4. Prepare affected branches before the Merge tap

Add background GitHub checks for active jobs, with bounded polling and immediate invalidation after an observed merge. A base update marks related readiness evidence stale. Debounce several base updates and synchronize each branch to the newest observed base at the next safe checkpoint. A busy writer or reviewer finishes or is explicitly cancelled and awaited before its checkout changes. Detect externally merged PRs and run existing cleanup once.

Use the existing assigned writer for semantic conflict repair. The coordinator performs scheduling and ordinary Git checks without a model call. Merge the remote base into the ticket branch, preserving published history. No unattended rebase, force-push or automatic PR merge is introduced. A branch that is merely behind is distinct from a genuine conflict or unknown mergeability. Limit semantic repair attempts per head/base/failure fingerprint; preserve the job's overall bounds.

Resolve append-only log conflicts deterministically only where entry boundaries and identities prove both entries are preserved. Overlapping edits to the same entry remain conflicts. Do not claim an arbitrary percentage of conflicts can be handled automatically, and do not introduce a general AST merge system without evidence it is needed.

Any changed head invalidates approval. Run the canonical tests, check current CI policy and obtain Luna's approval on the new head before showing Merge ready. On a Merge tap, acquire repository merge ownership and recheck current head, base, required checks and non-dismissed approval. Submit the merge with the expected head. If the base changes during verification, invalidate and repeat the affected verification; never claim that the user's second tap is guaranteed instantaneous.

Keep a Fix conflicts or Retry action as a recovery option. Continuous preparation should remove the routine need for it. Explain waiting, preparing, reviewing, ready and needs-decision states on the existing job card. Coalesce status edits, honor Telegram retry_after, and avoid a notification burst from six jobs in one group.

Completion evidence: two near-simultaneous merges, base updates during review, unknown mergeability, real and clean conflicts, log preservation, external merges, stopped owners, lost acknowledgements and bounded repeated base updates. A stale button cannot merge unreviewed code.

## 5. Normalize Aea and Luna workflows across engines

Maintain one reviewed implementation workflow and one reviewed review workflow for unattended workers. Keep persona identity, shared mixins and runtime engine configuration in their existing owners. Replace the worker dependency on interactive slash-command chaining and resolve the code-review/subagent contradiction. Use worker-specific runbooks if changing global shared skills would alter unrelated interactive workflows. Publish through reviewed repository changes; a worker cannot rewrite protected global skill installations.

Luna starts from the complete PR diff and acceptance criteria, then reads affected callers, tests, schemas and relevant sibling-repository code. Relevant AIS-OS context is allowed. Record the sibling revision, and pin or revalidate it when findings or tests depend on it. The coordinator prepares the reviewer checkout at the exact PR head without checking out a branch held in another worktree. The reviewer does not edit implementation source. Re-reviews start with changed code and unresolved findings, expanding where needed to assess interactions. Preserve the existing verdict/counts format and formal review identity.

Verify persona identity and boundaries on new, warm, recovered and compacted conversations for each supported engine. First-turn injection alone does not prove that resume loses history. Keep stable instructions separate from current job/context records and preserve prompt caching where supported. Configuration changes must invalidate stale workflow context deliberately. Fix observed retention failures and test them; do not blindly prepend the entire memory block on every turn.

Completion evidence: visible runnable workflows for Aea/Luna in each engine, no subagent invocation, no unusable slash dependency, exact reviewer checkout, two-axis review, relevant cross-repository reading, unchanged-code finding rejection, and warm-turn workflow updates.

## 6. Provide an isolated Telegram staging hub

Build a repeatable staging instance with its own bot token, private test forum, state, topic bindings, engine homes, worktree root and test repositories. Give every resource a run identity. An instance name alone is insufficient because engine homes and destination paths can otherwise remain shared. Staging must not poll the production token, write production job state, consume production queued messages or learn synthetic evidence as personal knowledge.

Keep test faults inside staging: stop its daemon or children, fail its transport, simulate quotas, delay CI and use fixture services. Administrative verification uses named trusted operations against staging resources. Never execute a model-selected shell command with extra privileges. Protect operation definitions from modification by the candidate code they verify. Do not add broad sudo access or automatic production configuration changes.

Automate handler/callback replay, real Git/fixture subprocess tests and staging outbound Telegram checks. Label simulated inbound updates as simulation. Telegram does not deliver bot messages to other bots, so a second bot cannot establish a real user-to-bot test. Source: [Telegram bot FAQ](https://core.telegram.org/bots/faq#why-doesn-39t-my-bot-see-messages-from-other-bots).

Provide a short real phone smoke test for incoming commands, button callbacks, attachments, routing, status and cancellation. Aki supplies the separate bot/group credentials and performs the initial real-user interactions. After setup, ordinary verification runs unattended where the transport permits it. If resources are unavailable, finish the runner and fixtures, report the exact missing resource and leave the live acceptance gate pending. Do not declare the overall ticket complete from simulations alone.

Completion evidence: failed staging operations leave production untouched; simultaneous instances have different state and homes; teardown removes only run-owned test artifacts; real phone steps and automated checks have separate receipts.

## Release acceptance

- [ ] Map all original criteria and the new audit findings to fixes or current verified behavior. Record checkout, dependency and provider versions.
- [ ] Six independent jobs run concurrently across at least two repositories, including three against the same repository. No pair, branch, worktree, conversation or review identity is shared accidentally.
- [ ] Cover required CI, explicit local review and unknown policy. Only the configured no-CI case proceeds without remote checks.
- [ ] Inject a quota wall, transient network failure, failed environment probe, CI delay, actual assertion failure, daemon restart and merge conflict. Recover each routine case without an implementation restart or duplicate side effect. Ambiguous cases show one actionable state.
- [ ] Merge one approved staging PR and observe the remaining affected branches prepare in the background. Merge another only after its current head/base evidence is valid. No unreviewed automatic merge occurs.
- [ ] Six-job replay records zero new writer/reviewer calls for unchanged valid approval plus a transient readiness failure. Capture actual model calls, usage when provided, wait time, test counts and user interventions.
- [ ] Run real-model staging turns covering all three engines and configured fallback. Synthetic provider faults may test classification, but report them separately from real provider behavior.
- [ ] Pass the repository suite through `scripts/run_tests.py -q`, required CI, independent review, staging isolation checks and the real Telegram smoke test. Preserve subprocess cleanup coverage and never weaken an assertion to obtain green.
- [ ] Include a deployment and rollback runbook with independent switches for background preparation and automatic recovery, durable pending work, and a versioned state migration/backup. Deployment remains a reviewed operation after staging evidence.

## Blocked by

None for code implementation. The ten source tickets are internal scope, not prerequisites to dispatch separately. Live closure requires the isolated bot/group and authorized staging provider access described above. Production deployment is a later reviewed operation.

## Recommended model

`claude-opus-4-6-thinking`. Concurrency, retry ownership, credential boundaries and approval reuse can pass happy-path tests while corrupting another job. `gpt-6-astra` at high or higher effort is a registered alternative if Aki selects Astra. This recommendation does not change any worker default or fallback chain.
