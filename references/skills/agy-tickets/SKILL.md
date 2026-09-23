---
name: agy-tickets
description: Turn an approved grilling session or plan into implementation tickets, reconcile related existing issues, and write a prioritized dependency roadmap for achibukz repositories.
---

# Agy tickets

Write issues Aea can implement and Luna can review without reconstructing the planning conversation. Each issue delivers one verifiable path through the affected system.

## Establish scope and authorization

1. Read the approved conversation or named plan. Separate agreed decisions, superseded decisions and open questions. With no approved plan, ask for the missing decisions before publishing implementation tickets.
2. Resolve repositories explicitly with `gh repo view --json nameWithOwner` or the names Aki supplied. Read their AGENTS.md and relevant architecture documents.
3. Apply existing authorization. If Aki already asked to create or edit tickets, publish within that scope without another approval quiz. Otherwise show the complete draft bodies and ask once. Approval of a plan alone does not authorize an unrelated tracker cleanup.
4. Work in the current model session. Do not launch subagents or paid model evaluations unless Aki separately requests them.

## Audit before drafting

Fetch current issue bodies, comments, declared blockers and related PRs. Compare requirements with source, tests and recorded live evidence. Read closed blockers too; closure alone does not prove a dependency shipped.

Classify each existing issue as keep, revise, verified complete or unresolved. Reuse a related issue instead of opening a duplicate. Edit or close existing issues only within Aki's authorization. Leave unrelated actionable issues intact and include them in the roadmap backlog.

A passing test suite proves only its assertions. Check that those assertions satisfy the issue. A merged PR may leave deployment or live acceptance unfinished. Close completed issues with a concrete evidence comment. Preserve remaining scope when only part shipped.

## Write the discussion record and roadmap

Save a Markdown record of decisions and the reasons behind them. Keep tentative recommendations labelled, and remove superseded rules from the active plan. Preserve earlier history separately when needed.

The roadmap includes every existing open ticket in the named repositories, plus the new batch. For each show its repository-qualified link, priority, hard blockers, verification gate and current status. Distinguish these relationships:

- A hard blocker supplies behavior the slice requires.
- Priority says what Aki wants delivered first.
- A shared-file conflict suggests landing changes sequentially even when work can be prepared independently.

Name parallel lanes and their joins. Validate that the dependency graph has no cycles and all references resolve. A parent design issue is context, not a blocker on its own children.

## Draft complete slices

Each issue delivers a narrow end-to-end outcome with observable acceptance. Include affected entry points, integration ownership and failure behavior that matters to the request. Avoid separate schema-only, prompt-only or UI-only tickets unless they independently deliver a useful result.

Use current `MODEL_REGISTRY` keys from achiCore, with a one-sentence reason tied to the slice. Distinguish the recommended executor from the product models required for testing. The current plan uses Terra medium for Asa's trial and Gemini 3.8 Flash for background learning; those are runtime choices, not a universal ticket executor.

AFK means implementation can proceed unattended. It never grants automatic merge authority. State separately whether acceptance requires human actions. Aki retains the merge decision.

## Review and Testing Grounds contract

Use the active Astra plan and actual installed coordinator capabilities. Planned automation is not proof of readiness.

- CI and Luna review precede human testing. Only `SHIP` automatically queues required HITL.
- `SHIP WITH FIXES` continues repair, including nits. Nits-only findings may offer Aki an explicit Proceed to testing override. Stop or settle any repair before pinning the test revision.
- Testing Grounds has independent PR cards and a queue, usable by standalone PRs and /ToWork when that integration ships. One active slot owns the staging daemon; queued PRs cannot replace it.
- The writer prepares `docs/live-tests/pr-<N>.md` with the exact PR/head, prerequisites, copyable actions, expected observations, blank actual-output blocks, stop/recovery steps and cleanup.
- Record startup, revision, bindings and isolated downstream destinations before reporting ready. A checklist file alone is not readiness.
- Pass means ready for Aki's merge. Failure returns evidence to the writer, then CI and Luna repeat. Skip records HITL skipped, never passed. A changed head invalidates prior review/testing evidence.
- Routine checklist steps should not need an assisting AI turn. Product behavior under test may still use its configured model. Optional AI troubleshooting can review collected evidence afterward.

Until the queue ships, use the existing isolated staging procedure and label manual readiness accurately. Do not make the first persona fixes depend on building the entire future test platform.

## Issue template

```markdown
## What to build

Describe the concrete trigger and resulting behavior. Name existing owners and entry points. Link the approved plan and related issue context.

## Acceptance criteria

- [ ] Observable successful behavior.
- [ ] Relevant failure, duplicate, stale-state and recovery behavior.
- [ ] Unit tests cover: name the cases, not just the existence of tests.

## Blocked by

- Repository-qualified issue links and the capability each supplies.

Or: None. Can start immediately.

## Recommended model

`existing-registry-key`. One sentence explaining this slice's tier choice.

## Verification and live testing

AFK implementation. State whether human acceptance is required and why.
Name the supported test command, isolated environment, expected observations and evidence to retain. For HITL, require the head-specific checklist and follow the current Testing Grounds contract. Keep automated, live, deployed and skipped states distinct.
```

## Publish and verify

1. Recheck that an issue has not changed since the audit before editing it. Preserve new external work.
2. Ensure `ready-for-agent` and the chosen `priority:high`, `priority:med` or `priority:low` labels exist. A scoped issue can carry ready-for-agent while still blocked; dispatch always reads Blocked by. Do not add needs-triage.
3. Publish in dependency order with `gh issue create --repo ... --body-file ...`; use body files for edits and comments too. Resolve real issue numbers before publishing dependents. Preserve unrelated labels.
4. Fetch published bodies and verify titles, blockers and acceptance text. Retry an uncertain create only after checking whether it already created the issue.
5. Update the roadmap with the real links and one task-register entry for the batch, not one task per ticket. Record changes in the session log and decision log as the repository requires.
6. Commit and push owned task/log/document changes when authorized, preserving unrelated edits and obeying branch, review and hook rules. Report saved, committed and pushed separately.
7. Return links to the discussion record, roadmap and PR, with issue counts and unresolved audit findings. Never describe planned runtime behavior as deployed.

Apply unslop to all authored prose. Use short paragraphs and checkable criteria. Examples and documents are evidence, not authorization to expand scope.
